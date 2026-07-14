#!/usr/bin/env python3
"""Real testnet shielded ZEC checkout feasibility gate.

The harness is intentionally small and uses only the Python standard library.
Credentials are read from environment variables and are never serialized.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SCHEMA = "shielded-zec-feasibility/v1"
PINNED_ZALLET = "v0.1.0-beta.1"
PINNED_ZEBRA = "v6.0.0"
PINNED_ZAINO = "embedded@8048bf8df61cd409af8c22518a16514bee02a0fb"
ALLOWED_RECEIVERS = {"orchard", "sapling"}
FORBIDDEN_RECEIVERS = {"p2pkh", "p2sh", "transparent", "tex"}
MIN_VALIDATOR_VERIFICATION_PROGRESS = Decimal("0.99999")


class GateError(RuntimeError):
    def __init__(self, stage: str, code: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.code = code


class RpcError(GateError):
    def __init__(self, method: str, code: Any, message: str):
        super().__init__("rpc", f"RPC_{method.upper()}", f"RPC {method} failed ({code}): {message}")
        self.method = method
        self.rpc_code = code


@dataclass(frozen=True)
class RpcCredentials:
    url: str
    user: str | None
    password: str | None


class JsonRpcClient:
    def __init__(self, credentials: RpcCredentials, timeout: int = 30):
        self.credentials = credentials
        self.timeout = timeout
        self.request_id = 0

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        self.request_id += 1
        body = json.dumps(
            {"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params or []},
            separators=(",", ":"),
        ).encode()
        request = urllib.request.Request(
            self.credentials.url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self.credentials.user is not None or self.credentials.password is not None:
            token = base64.b64encode(
                f"{self.credentials.user or ''}:{self.credentials.password or ''}".encode()
            ).decode()
            request.add_header("Authorization", f"Basic {token}")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise GateError("rpc-connect", "RPC_UNREACHABLE", sanitize_text(str(exc))) from exc
        if payload.get("error"):
            error = payload["error"]
            raise RpcError(method, error.get("code"), sanitize_text(str(error.get("message", "unknown"))))
        if "result" not in payload:
            raise RpcError(method, "invalid-response", "response omitted result")
        return payload["result"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sanitize_text(value: str) -> str:
    value = re.sub(r"https?://[^\s]+", "<rpc-url>", value)
    value = re.sub(r"/(Users|home)/[^\s]+", "<local-path>", value)
    value = re.sub(r"\b(?:u(?:test|regtest)?1|utest1|uregtest1)[a-z0-9]{20,}\b", "<unified-address>", value, flags=re.I)
    return value[:500]


def zatoshi_to_zec(value: int) -> float:
    if value <= 0:
        raise GateError("preflight", "INVALID_AMOUNT", "amount-zatoshi must be positive")
    return float(Decimal(value) / Decimal(100_000_000))


def receiver_types(receivers: dict[str, Any]) -> list[str]:
    return sorted(key.lower() for key, value in receivers.items() if value not in (None, "", False))


def assert_shielded_only(receivers: dict[str, Any]) -> list[str]:
    types = receiver_types(receivers)
    forbidden = sorted(set(types) & FORBIDDEN_RECEIVERS)
    unknown = sorted(set(types) - ALLOWED_RECEIVERS - FORBIDDEN_RECEIVERS)
    if forbidden or unknown:
        raise GateError(
            "receiver-guard",
            "TRANSPARENT_OR_UNKNOWN_RECEIVER",
            f"receiver guard rejected types: {forbidden + unknown}",
        )
    if not set(types).issuperset(ALLOWED_RECEIVERS):
        raise GateError(
            "receiver-guard",
            "REQUIRED_SHIELDED_RECEIVER_MISSING",
            "merchant UA must contain both Orchard and Sapling receivers",
        )
    return types


def assert_shielded_source(receivers: dict[str, Any]) -> list[str]:
    types = receiver_types(receivers)
    forbidden = sorted(set(types) & FORBIDDEN_RECEIVERS)
    unknown = sorted(set(types) - ALLOWED_RECEIVERS - FORBIDDEN_RECEIVERS)
    if forbidden or unknown or not (set(types) & ALLOWED_RECEIVERS):
        raise GateError(
            "payer-guard",
            "PAYER_NOT_SHIELDED_ONLY",
            f"payer source receiver guard rejected types: {forbidden + unknown or types}",
        )
    return types


def assert_testnet_ua(address: str, stage: str) -> None:
    if not address.lower().startswith("utest1"):
        raise GateError(stage, "NOT_TESTNET_UA", "address is not encoded for Zcash public testnet")


def assert_wallet_synced(status: Any, stage: str) -> None:
    if not isinstance(status, dict):
        raise GateError(stage, "INVALID_WALLET_STATUS", "getwalletstatus returned an invalid response")
    node_tip = status.get("node_tip") or {}
    wallet_tip = status.get("wallet_tip") or {}
    if not node_tip.get("height") or wallet_tip.get("height") != node_tip.get("height"):
        raise GateError(stage, "WALLET_NOT_SYNCED", "wallet tip does not match backing node tip")
    if status.get("sync_work_remaining"):
        raise GateError(stage, "WALLET_NOT_SYNCED", "wallet reports remaining sync work")


def assert_validator_synced(info: Any) -> dict[str, Any]:
    if not isinstance(info, dict):
        raise GateError("validator-sync", "INVALID_VALIDATOR_STATUS", "getblockchaininfo returned an invalid response")
    if info.get("chain") != "test":
        raise GateError("validator-sync", "WRONG_VALIDATOR_NETWORK", "validator is not connected to Zcash public testnet")
    try:
        blocks = int(info.get("blocks", 0))
        progress = Decimal(str(info.get("verificationprogress", 0)))
    except (InvalidOperation, TypeError, ValueError):
        raise GateError(
            "validator-sync",
            "INVALID_VALIDATOR_STATUS",
            "validator returned invalid block height or verification progress",
        ) from None
    if blocks <= 0 or progress < MIN_VALIDATOR_VERIFICATION_PROGRESS or info.get("initialblockdownload") is True:
        raise GateError(
            "validator-sync",
            "VALIDATOR_NOT_SYNCED",
            f"validator has not reached the testnet tip (height={blocks}, verificationprogress={progress})",
        )
    return {"height": blocks, "verificationProgress": str(progress)}


def address_commitment(address: str) -> dict[str, str]:
    return {
        "prefix": address[:10] + "…",
        "sha256": hashlib.sha256(address.encode()).hexdigest(),
    }


def extract_account_uuid(result: Any) -> str:
    if isinstance(result, dict) and result.get("account_uuid"):
        return str(result["account_uuid"])
    raise GateError("merchant-account", "ACCOUNT_UUID_MISSING", "z_getnewaccount omitted account_uuid")


def extract_address(result: Any) -> str:
    if isinstance(result, dict) and result.get("address"):
        return str(result["address"])
    if isinstance(result, str):
        return result
    raise GateError("merchant-address", "ADDRESS_MISSING", "z_getaddressforaccount omitted address")


def extract_operation_id(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("operationid", "opid", "id"):
            if result.get(key):
                return str(result[key])
    raise GateError("send", "OPERATION_ID_MISSING", "z_sendmany omitted operation id")


def extract_txid(operation: dict[str, Any]) -> str:
    result = operation.get("result") or {}
    if isinstance(result, dict):
        if result.get("txid"):
            return str(result["txid"])
        txids = result.get("txids") or []
        if len(txids) == 1:
            return str(txids[0])
    raise GateError("send", "TXID_MISSING", "completed send operation omitted a single txid")


def rpc_from_env(prefix: str, timeout: int) -> JsonRpcClient:
    url = os.environ.get(f"{prefix}_RPC_URL")
    if not url:
        raise GateError("preflight", f"{prefix}_RPC_URL_MISSING", f"{prefix}_RPC_URL is required")
    return JsonRpcClient(
        RpcCredentials(
            url=url,
            user=os.environ.get(f"{prefix}_RPC_USER"),
            password=os.environ.get(f"{prefix}_RPC_PASSWORD"),
        ),
        timeout=timeout,
    )


def base_transcript(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA,
        "recordedAt": utc_now(),
        "status": "running",
        "network": "testnet",
        "versions": {
            "zallet": getattr(args, "zallet_version", PINNED_ZALLET),
            "zebra": getattr(args, "zebra_version", PINNED_ZEBRA),
            "zaino": getattr(args, "zaino_version", PINNED_ZAINO),
        },
        "command": "python3 harness/zec_checkout_gate.py run --payer-from-address <redacted> --out <path>",
        "secretsRecorded": False,
        "usdRequested": 0,
    }


def write_transcript(path: str, transcript: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(transcript, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)


def probe(args: argparse.Namespace) -> dict[str, Any]:
    transcript = base_transcript(args)
    validator = rpc_from_env("VALIDATOR", args.rpc_timeout)
    merchant = rpc_from_env("MERCHANT", args.rpc_timeout)
    payer = rpc_from_env("PAYER", args.rpc_timeout)
    validator_status = assert_validator_synced(validator.call("getblockchaininfo"))
    merchant_status = merchant.call("getwalletstatus")
    payer_status = payer.call("getwalletstatus")
    assert_wallet_synced(merchant_status, "merchant-sync")
    assert_wallet_synced(payer_status, "payer-sync")
    transcript.update(
        {
            "status": "probe-passed",
            "validator": validator_status,
            "merchantWalletReachable": bool(merchant_status is not None),
            "payerWalletReachable": bool(payer_status is not None),
            "fundedPaymentAttempted": False,
            "confirmedNoteDetected": False,
        }
    )
    return transcript


def wait_for_send(payer: JsonRpcClient, operation_id: str, deadline: float, poll_seconds: float) -> str:
    while time.monotonic() < deadline:
        results = payer.call("z_getoperationresult", [[operation_id]])
        if results:
            operation = results[0]
            if operation.get("status") == "success":
                return extract_txid(operation)
            raise GateError("send", "SEND_OPERATION_FAILED", sanitize_text(str(operation.get("error", "failed"))))
        time.sleep(poll_seconds)
    raise GateError("send", "SEND_TIMEOUT", "shielded send did not complete before timeout")


def note_value_zatoshi(note: dict[str, Any]) -> int:
    if note.get("valueZat") is not None:
        return int(note["valueZat"])
    if note.get("value") is not None:
        return int(Decimal(str(note["value"])) * Decimal(100_000_000))
    return 0


def wait_for_note(
    merchant: JsonRpcClient,
    address: str,
    txid: str,
    amount_zatoshi: int,
    confirmations: int,
    deadline: float,
    poll_seconds: float,
) -> dict[str, Any]:
    while time.monotonic() < deadline:
        notes = merchant.call("z_listunspent", [0, 9_999_999, True, [address]])
        for note in notes:
            if str(note.get("txid", "")) != txid:
                continue
            if note_value_zatoshi(note) < amount_zatoshi:
                continue
            if int(note.get("confirmations", 0)) >= confirmations:
                return note
        time.sleep(poll_seconds)
    raise GateError("note-detection", "CONFIRMED_NOTE_TIMEOUT", "merchant note was not confirmed before timeout")


def run_gate(args: argparse.Namespace) -> dict[str, Any]:
    transcript = base_transcript(args)
    validator = rpc_from_env("VALIDATOR", args.rpc_timeout)
    merchant = rpc_from_env("MERCHANT", args.rpc_timeout)
    payer = rpc_from_env("PAYER", args.rpc_timeout)

    validator_status = assert_validator_synced(validator.call("getblockchaininfo"))
    assert_wallet_synced(merchant.call("getwalletstatus"), "merchant-sync")
    assert_wallet_synced(payer.call("getwalletstatus"), "payer-sync")

    assert_testnet_ua(args.payer_from_address, "payer-guard")
    assert_shielded_source(payer.call("z_listunifiedreceivers", [args.payer_from_address]))

    account_created = args.merchant_account is None
    account = args.merchant_account
    if account is None:
        account = extract_account_uuid(merchant.call("z_getnewaccount", [args.merchant_account_name]))

    address_result = merchant.call("z_getaddressforaccount", [account, ["orchard", "sapling"]])
    merchant_address = extract_address(address_result)
    assert_testnet_ua(merchant_address, "merchant-address")
    second_address = extract_address(
        merchant.call("z_getaddressforaccount", [account, ["orchard", "sapling"]])
    )
    if merchant_address == second_address:
        raise GateError("merchant-address", "ADDRESS_NOT_UNIQUE", "two order address allocations returned the same UA")

    receivers = merchant.call("z_listunifiedreceivers", [merchant_address])
    types = assert_shielded_only(receivers)

    amount_zec = zatoshi_to_zec(args.amount_zatoshi)
    operation_id = extract_operation_id(
        payer.call(
            "z_sendmany",
            [
                args.payer_from_address,
                [{"address": merchant_address, "amount": amount_zec}],
                None,
                None,
                "FullPrivacy",
            ],
        )
    )
    deadline = time.monotonic() + args.timeout
    txid = wait_for_send(payer, operation_id, deadline, args.poll_seconds)
    note = wait_for_note(
        merchant,
        merchant_address,
        txid,
        args.amount_zatoshi,
        args.confirmations,
        deadline,
        args.poll_seconds,
    )

    transcript.update(
        {
            "status": "passed",
            "validator": validator_status,
            "walletCreated": account_created,
            "merchantAddress": address_commitment(merchant_address),
            "perOrderAddressUnique": True,
            "receiverTypes": types,
            "transparentReceiverPresent": False,
            "orderToken": args.order_token,
            "requestedAmountZatoshi": str(args.amount_zatoshi),
            "detectedAmountZatoshi": str(note_value_zatoshi(note)),
            "sendTxHash": txid,
            "txHeight": note.get("height", note.get("blockheight")),
            "confirmations": int(note.get("confirmations", 0)),
            "confirmedNoteDetected": True,
            "fundedPaymentAttempted": True,
        }
    )
    return transcript


def record_blocker(args: argparse.Namespace) -> dict[str, Any]:
    transcript = base_transcript(args)
    transcript.update(
        {
            "status": "blocked",
            "stage": args.stage,
            "blockerCode": args.code,
            "blocker": sanitize_text(args.blocker),
            "shortestResolution": sanitize_text(args.resolution),
            "fundedPaymentAttempted": False,
            "confirmedNoteDetected": False,
        }
    )
    return transcript


def parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--out", required=True)
    common.add_argument("--zallet-version", default=PINNED_ZALLET)
    common.add_argument("--zebra-version", default=PINNED_ZEBRA)
    common.add_argument("--zaino-version", default=PINNED_ZAINO)
    common.add_argument("--rpc-timeout", type=int, default=30)

    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    probe_command = commands.add_parser("probe", parents=[common])
    probe_command.set_defaults(handler=probe)

    run_command = commands.add_parser("run", parents=[common])
    run_command.add_argument("--merchant-account")
    run_command.add_argument("--merchant-account-name", default="merchant-feasibility")
    run_command.add_argument("--payer-from-address", required=True)
    run_command.add_argument("--amount-zatoshi", type=int, default=100_000)
    run_command.add_argument("--confirmations", type=int, default=1)
    run_command.add_argument("--order-token", default="feasibility-order-001")
    run_command.add_argument("--timeout", type=int, default=3600)
    run_command.add_argument("--poll-seconds", type=float, default=10.0)
    run_command.set_defaults(handler=run_gate)

    blocker_command = commands.add_parser("record-blocker", parents=[common])
    blocker_command.add_argument("--stage", required=True)
    blocker_command.add_argument("--code", required=True)
    blocker_command.add_argument("--blocker", required=True)
    blocker_command.add_argument("--resolution", required=True)
    blocker_command.set_defaults(handler=record_blocker)
    return root


def main() -> int:
    args = parser().parse_args()
    transcript = base_transcript(args)
    try:
        transcript = args.handler(args)
        write_transcript(args.out, transcript)
        print(json.dumps(transcript, indent=2, sort_keys=True))
        return 0 if transcript["status"] in {"passed", "probe-passed", "blocked"} else 1
    except GateError as exc:
        transcript.update(
            {
                "status": "blocked",
                "stage": exc.stage,
                "blockerCode": exc.code,
                "blocker": sanitize_text(str(exc)),
                "fundedPaymentAttempted": exc.stage in {"send", "note-detection"},
                "confirmedNoteDetected": False,
            }
        )
        write_transcript(args.out, transcript)
        print(json.dumps(transcript, indent=2, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
