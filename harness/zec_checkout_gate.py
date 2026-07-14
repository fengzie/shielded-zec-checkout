#!/usr/bin/env python3
"""Shielded ZEC light-client feasibility helpers.

The only passing condition for the overall gate remains a real public-testnet
shielded payer-to-merchant confirmed note.  This harness deliberately provides
only the safe, non-funding preflight that precedes that run:

* query a CompactTxStreamer endpoint through a pinned light-client binary;
* create an ephemeral testnet Unified Address with Orchard and Sapling
  receivers; and
* fail closed if the client reports any transparent receiver.

It never requests funds, sends a transaction, or retains the temporary wallet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shielded-zec-feasibility/v1"
DEFAULT_SERVER = "https://testnet.zec.rocks:443"
PINNED_ZINGOLIB = "zingolib_v5.0.0"
PINNED_ZINGOLIB_COMMIT = "9e897f8b2fc5f12a99604f2533164af62af7d3ac"
PINNED_ZINGO_CLI_PACKAGE = "0.4.0"
ALLOWED_RECEIVERS = {"orchard", "sapling"}
TXID_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class GateError(RuntimeError):
    def __init__(self, stage: str, code: str, message: str):
        super().__init__(message)
        self.stage = stage
        self.code = code


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sanitize_text(value: str) -> str:
    value = re.sub(r"https?://[^\s]+", "<endpoint>", value)
    value = re.sub(r"/(Users|home)/[^\s]+", "<local-path>", value)
    value = re.sub(r"\butest1[a-z0-9]{20,}\b", "<unified-address>", value, flags=re.I)
    return value[:500]


def address_commitment(address: str) -> dict[str, str]:
    return {"prefix": address[:10] + "…", "sha256": hashlib.sha256(address.encode()).hexdigest()}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as binary:
        for chunk in iter(lambda: binary.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_last_json_object(output: str) -> dict[str, Any]:
    """Return the last complete object printed by the interactive-compatible CLI."""
    decoder = json.JSONDecoder()
    last: dict[str, Any] | None = None
    last_end = -1
    for index, char in enumerate(output):
        if char != "{":
            continue
        try:
            decoded, end = decoder.raw_decode(output[index:])
        except json.JSONDecodeError:
            continue
        absolute_end = index + end
        if isinstance(decoded, dict) and absolute_end > last_end:
            last = decoded
            last_end = absolute_end
    if last is None:
        raise GateError("client-output", "JSON_OUTPUT_MISSING", "light-client command did not return a JSON object")
    return last


def validate_endpoint_info(info: dict[str, Any]) -> dict[str, Any]:
    if info.get("chain_name") != "test":
        raise GateError("endpoint", "WRONG_NETWORK", "CompactTxStreamer endpoint is not Zcash public testnet")
    try:
        height = int(info["latest_block_height"])
    except (KeyError, TypeError, ValueError):
        raise GateError("endpoint", "INVALID_HEIGHT", "endpoint omitted a positive latest block height") from None
    if height <= 0:
        raise GateError("endpoint", "INVALID_HEIGHT", "endpoint omitted a positive latest block height")
    return {
        "uri": str(info.get("server_uri", "")),
        "vendor": str(info.get("vendor", "")),
        "protocolVersion": str(info.get("version", "")),
        "latestBlockHeight": height,
        "saplingActivationHeight": str(info.get("sapling_activation_height", "")),
        "consensusBranchId": str(info.get("consensus_branch_id", "")),
    }


def validate_shielded_only_address(result: dict[str, Any]) -> tuple[str, list[str]]:
    address = result.get("encoded_address")
    if not isinstance(address, str) or not address.lower().startswith("utest1"):
        raise GateError("receiver-guard", "NOT_TESTNET_UA", "client did not return a public-testnet Unified Address")
    if result.get("has_transparent") is not False:
        raise GateError("receiver-guard", "TRANSPARENT_RECEIVER_PRESENT", "Unified Address contains transparent receiver")
    receiver_types = sorted(
        receiver
        for receiver, present in (("orchard", result.get("has_orchard")), ("sapling", result.get("has_sapling")))
        if present is True
    )
    if set(receiver_types) != ALLOWED_RECEIVERS:
        raise GateError(
            "receiver-guard",
            "REQUIRED_SHIELDED_RECEIVER_MISSING",
            "merchant Unified Address must contain exactly Orchard and Sapling receivers",
        )
    return address, receiver_types


def validate_passed_transcript(transcript: dict[str, Any]) -> dict[str, Any]:
    """Fail closed unless a redacted transcript satisfies the real-payment gate."""
    required = {
        "status": "passed",
        "network": "testnet",
        "confirmedNoteDetected": True,
        "transparentReceiverPresent": False,
        "secretsRecorded": False,
        "usdRequested": 0,
    }
    for field, expected in required.items():
        if transcript.get(field) != expected:
            raise GateError("transcript", "INVALID_PASS_TRANSCRIPT", f"invalid {field}")

    if set(transcript.get("receiverTypes", [])) != ALLOWED_RECEIVERS:
        raise GateError("transcript", "INVALID_PASS_TRANSCRIPT", "invalid receiverTypes")
    if not TXID_PATTERN.fullmatch(str(transcript.get("sendTxHash", ""))):
        raise GateError("transcript", "INVALID_PASS_TRANSCRIPT", "invalid sendTxHash")
    try:
        requested = int(transcript["requestedAmountZatoshi"])
        detected = int(transcript["detectedAmountZatoshi"])
        confirmations = int(transcript["confirmations"])
    except (KeyError, TypeError, ValueError):
        raise GateError("transcript", "INVALID_PASS_TRANSCRIPT", "invalid amount or confirmations") from None
    if requested <= 0 or requested != detected or confirmations < 1:
        raise GateError("transcript", "INVALID_PASS_TRANSCRIPT", "payment evidence does not match")

    counts = transcript.get("chainEvidence", {}).get("componentCounts", {})
    forbidden_counts = (
        "transparentInputs",
        "transparentOutputs",
        "saplingSpends",
        "saplingOutputs",
        "orchardActions",
    )
    if any(counts.get(field) != 0 for field in forbidden_counts) or counts.get("ironwoodActions", 0) < 1:
        raise GateError("transcript", "INVALID_PASS_TRANSCRIPT", "transaction is not Ironwood shielded-only")

    merchant = transcript.get("merchantAddress", {})
    if not re.fullmatch(r"[0-9a-f]{64}", str(merchant.get("sha256", ""))):
        raise GateError("transcript", "INVALID_PASS_TRANSCRIPT", "invalid merchant address commitment")
    if str(merchant.get("prefix", "")).startswith("utest1") is False:
        raise GateError("transcript", "INVALID_PASS_TRANSCRIPT", "invalid merchant address prefix")
    return transcript


def run_client(binary: Path, data_dir: Path, server: str, command: list[str]) -> str:
    invocation = [
        str(binary),
        "--chain",
        "testnet",
        "--server",
        server,
        "--data-dir",
        str(data_dir),
        "--nosync",
        *command,
    ]
    previous_umask = os.umask(0o077)
    try:
        try:
            completed = subprocess.run(invocation, text=True, capture_output=True, check=False, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise GateError("client-command", "LIGHT_CLIENT_COMMAND_FAILED", sanitize_text(str(error))) from error
    finally:
        os.umask(previous_umask)
    if completed.returncode != 0:
        message = sanitize_text((completed.stderr or completed.stdout).strip())
        raise GateError("client-command", "LIGHT_CLIENT_COMMAND_FAILED", message or "light-client command failed")
    return completed.stdout


def assert_private_wallet_permissions(wallet_path: Path) -> str:
    if not wallet_path.is_file():
        raise GateError("wallet-permissions", "WALLET_FILE_MISSING", "light client did not persist its wallet file")
    if os.name != "posix":
        return "platform-default"
    mode = stat.S_IMODE(wallet_path.stat().st_mode)
    if mode != 0o600:
        raise GateError(
            "wallet-permissions",
            "INSECURE_WALLET_FILE_MODE",
            f"wallet file mode must be 0600, observed {mode:04o}",
        )
    return f"{mode:04o}"


def binary_version(binary: Path) -> str:
    try:
        completed = subprocess.run(
            [str(binary), "--version"], text=True, capture_output=True, check=False, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GateError("binary", "VERSION_COMMAND_FAILED", sanitize_text(str(error))) from error
    if completed.returncode != 0:
        raise GateError("binary", "VERSION_COMMAND_FAILED", sanitize_text(completed.stderr))
    return completed.stdout.strip()


def base_transcript(binary: Path, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA,
        "recordedAt": utc_now(),
        "status": "running",
        "network": "testnet",
        "versions": {
            "zingolibTag": args.zingolib_tag,
            "zingolibCommit": args.zingolib_commit,
            "zingoCliPackage": args.zingo_cli_package_version,
            "zingoCliReported": binary_version(binary),
            "zingoCliSha256": sha256_file(binary),
        },
        "command": "python3 harness/zec_checkout_gate.py light-preflight --zingo-cli <path> --out <path>",
        "secretsRecorded": False,
        "usdRequested": 0,
    }


def write_transcript(path: str, transcript: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(transcript, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(target)


def light_preflight(args: argparse.Namespace) -> dict[str, Any]:
    binary = Path(args.zingo_cli).expanduser().resolve()
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise GateError("binary", "ZINGO_CLI_UNAVAILABLE", "--zingo-cli must name an executable light-client binary")

    transcript = base_transcript(binary, args)
    temporary_wallet = Path(tempfile.mkdtemp(prefix="shielded-zec-preflight-"))
    try:
        endpoint_info = validate_endpoint_info(
            extract_last_json_object(run_client(binary, temporary_wallet, args.server, ["info"]))
        )
        address, receiver_types = validate_shielded_only_address(
            extract_last_json_object(run_client(binary, temporary_wallet, args.server, ["new_address", "oz"]))
        )
        wallet_file_mode = assert_private_wallet_permissions(temporary_wallet / "zingo-wallet.dat")
    finally:
        try:
            shutil.rmtree(temporary_wallet)
        except OSError as error:
            raise GateError(
                "cleanup", "TEMP_WALLET_CLEANUP_FAILED", sanitize_text(str(error))
            ) from error

    transcript.update(
        {
            "status": "preflight-passed",
            "stage": "light-client-preflight",
            "endpoint": endpoint_info,
            "merchantAddress": address_commitment(address),
            "receiverTypes": receiver_types,
            "transparentReceiverPresent": False,
            "walletFileMode": wallet_file_mode,
            "walletDataRetained": False,
            "fundedPaymentAttempted": False,
            "confirmedNoteDetected": False,
            "nextGate": "fund a disposable shielded payer and detect one confirmed payer-to-merchant note",
        }
    )
    return transcript


def record_blocker(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA,
        "recordedAt": utc_now(),
        "status": "blocked",
        "network": "testnet",
        "stage": args.stage,
        "blockerCode": args.code,
        "blocker": sanitize_text(args.blocker),
        "shortestResolution": sanitize_text(args.resolution),
        "fundedPaymentAttempted": False,
        "confirmedNoteDetected": False,
        "secretsRecorded": False,
        "usdRequested": 0,
    }


def verify_transcript(args: argparse.Namespace) -> dict[str, Any]:
    try:
        transcript = json.loads(Path(args.transcript).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GateError("transcript", "TRANSCRIPT_READ_FAILED", sanitize_text(str(error))) from error
    validate_passed_transcript(transcript)
    return {
        "schemaVersion": SCHEMA,
        "status": "valid",
        "sendTxHash": transcript["sendTxHash"],
        "secretsRecorded": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)

    preflight = commands.add_parser("light-preflight")
    preflight.add_argument("--out", required=True)
    preflight.add_argument("--zingo-cli", required=True)
    preflight.add_argument("--server", default=DEFAULT_SERVER)
    preflight.add_argument("--zingolib-tag", default=PINNED_ZINGOLIB)
    preflight.add_argument("--zingolib-commit", default=PINNED_ZINGOLIB_COMMIT)
    preflight.add_argument("--zingo-cli-package-version", default=PINNED_ZINGO_CLI_PACKAGE)
    preflight.set_defaults(handler=light_preflight)

    blocker = commands.add_parser("record-blocker")
    blocker.add_argument("--out", required=True)
    blocker.add_argument("--stage", required=True)
    blocker.add_argument("--code", required=True)
    blocker.add_argument("--blocker", required=True)
    blocker.add_argument("--resolution", required=True)
    blocker.set_defaults(handler=record_blocker)

    verify = commands.add_parser("verify-transcript")
    verify.add_argument("--transcript", required=True)
    verify.set_defaults(handler=verify_transcript)
    return root


def main() -> int:
    args = parser().parse_args()
    output_path = getattr(args, "out", None)
    try:
        transcript = args.handler(args)
    except GateError as error:
        transcript = {
            "schemaVersion": SCHEMA,
            "recordedAt": utc_now(),
            "status": "blocked",
            "network": "testnet",
            "stage": error.stage,
            "blockerCode": error.code,
            "blocker": sanitize_text(str(error)),
            "fundedPaymentAttempted": False,
            "confirmedNoteDetected": False,
            "secretsRecorded": False,
            "usdRequested": 0,
        }
        if output_path:
            write_transcript(output_path, transcript)
        print(json.dumps(transcript, indent=2, sort_keys=True))
        return 2
    if output_path:
        write_transcript(output_path, transcript)
    print(json.dumps(transcript, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
