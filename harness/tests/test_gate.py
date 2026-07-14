import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from zec_checkout_gate import (  # noqa: E402
    GateError,
    address_commitment,
    assert_private_wallet_permissions,
    extract_last_json_object,
    sanitize_text,
    validate_endpoint_info,
    validate_passed_transcript,
    validate_shielded_only_address,
    light_preflight,
)


class EndpointTests(unittest.TestCase):
    def test_accepts_testnet_endpoint_info(self):
        self.assertEqual(
            validate_endpoint_info(
                {
                    "chain_name": "test",
                    "latest_block_height": 4_170_173,
                    "server_uri": "https://testnet.example:443/",
                    "vendor": "test",
                    "version": "v0",
                    "sapling_activation_height": 280000,
                    "consensus_branch_id": "37a5165b",
                }
            )["latestBlockHeight"],
            4_170_173,
        )

    def test_rejects_non_testnet_endpoint(self):
        with self.assertRaises(GateError) as context:
            validate_endpoint_info({"chain_name": "main", "latest_block_height": 1})
        self.assertEqual(context.exception.code, "WRONG_NETWORK")

    def test_rejects_missing_height(self):
        with self.assertRaises(GateError) as context:
            validate_endpoint_info({"chain_name": "test"})
        self.assertEqual(context.exception.code, "INVALID_HEIGHT")


class ReceiverGuardTests(unittest.TestCase):
    def test_accepts_orchard_and_sapling_without_transparent(self):
        address, receivers = validate_shielded_only_address(
            {
                "encoded_address": "utest1" + "a" * 80,
                "has_orchard": True,
                "has_sapling": True,
                "has_transparent": False,
            }
        )
        self.assertTrue(address.startswith("utest1"))
        self.assertEqual(receivers, ["orchard", "sapling"])

    def test_rejects_transparent_receiver(self):
        with self.assertRaises(GateError) as context:
            validate_shielded_only_address(
                {
                    "encoded_address": "utest1" + "a" * 80,
                    "has_orchard": True,
                    "has_sapling": True,
                    "has_transparent": True,
                }
            )
        self.assertEqual(context.exception.code, "TRANSPARENT_RECEIVER_PRESENT")

    def test_rejects_missing_sapling_receiver(self):
        with self.assertRaises(GateError) as context:
            validate_shielded_only_address(
                {
                    "encoded_address": "utest1" + "a" * 80,
                    "has_orchard": True,
                    "has_sapling": False,
                    "has_transparent": False,
                }
            )
        self.assertEqual(context.exception.code, "REQUIRED_SHIELDED_RECEIVER_MISSING")


class OutputAndRedactionTests(unittest.TestCase):
    def test_extracts_final_json_object_from_cli_logs(self):
        output = 'Creating\n{"first": true}\nSaved\n{"last": {"height": 2}}\n'
        self.assertEqual(extract_last_json_object(output), {"last": {"height": 2}})

    def test_address_commitment_does_not_expose_full_address(self):
        address = "utest1" + "a" * 80
        commitment = address_commitment(address)
        self.assertNotIn(address, commitment.values())
        self.assertEqual(len(commitment["sha256"]), 64)

    def test_sanitizes_endpoint_and_local_path(self):
        value = sanitize_text("failed at https://testnet.example:443 in /Users/example/wallet")
        self.assertNotIn("testnet.example", value)
        self.assertNotIn("/Users/example", value)


class PassedTranscriptTests(unittest.TestCase):
    def valid_transcript(self):
        return {
            "status": "passed",
            "network": "testnet",
            "confirmedNoteDetected": True,
            "transparentReceiverPresent": False,
            "secretsRecorded": False,
            "usdRequested": 0,
            "receiverTypes": ["orchard", "sapling"],
            "sendTxHash": "a" * 64,
            "requestedAmountZatoshi": "10",
            "detectedAmountZatoshi": "10",
            "confirmations": 1,
            "merchantAddress": {"prefix": "utest1abc…", "sha256": "b" * 64},
            "chainEvidence": {
                "componentCounts": {
                    "transparentInputs": 0,
                    "transparentOutputs": 0,
                    "saplingSpends": 0,
                    "saplingOutputs": 0,
                    "orchardActions": 0,
                    "ironwoodActions": 2,
                }
            },
        }

    def test_accepts_confirmed_ironwood_shielded_only_payment(self):
        transcript = self.valid_transcript()
        self.assertIs(validate_passed_transcript(transcript), transcript)

    def test_rejects_transparent_chain_component(self):
        transcript = self.valid_transcript()
        transcript["chainEvidence"]["componentCounts"]["transparentOutputs"] = 1
        with self.assertRaises(GateError):
            validate_passed_transcript(transcript)

    def test_rejects_amount_mismatch(self):
        transcript = self.valid_transcript()
        transcript["detectedAmountZatoshi"] = "9"
        with self.assertRaises(GateError):
            validate_passed_transcript(transcript)


class TemporaryWalletTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform != "win32", "POSIX permission assertion")
    def test_rejects_group_or_world_readable_wallet(self):
        with tempfile.TemporaryDirectory() as parent:
            wallet = pathlib.Path(parent) / "zingo-wallet.dat"
            wallet.write_bytes(b"disposable-test-wallet")
            wallet.chmod(0o644)
            with self.assertRaises(GateError) as context:
                assert_private_wallet_permissions(wallet)
            self.assertEqual(context.exception.code, "INSECURE_WALLET_FILE_MODE")

    @unittest.skipUnless(sys.platform != "win32", "POSIX permission assertion")
    def test_accepts_owner_only_wallet(self):
        with tempfile.TemporaryDirectory() as parent:
            wallet = pathlib.Path(parent) / "zingo-wallet.dat"
            wallet.write_bytes(b"disposable-test-wallet")
            wallet.chmod(0o600)
            self.assertEqual(assert_private_wallet_permissions(wallet), "0600")

    def test_removes_temporary_wallet_when_client_command_fails(self):
        with tempfile.TemporaryDirectory() as parent:
            wallet_dir = pathlib.Path(parent) / "wallet"
            wallet_dir.mkdir()
            args = SimpleNamespace(zingo_cli=sys.executable, server="https://testnet.example:443")
            with mock.patch("zec_checkout_gate.tempfile.mkdtemp", return_value=str(wallet_dir)), mock.patch(
                "zec_checkout_gate.base_transcript", return_value={}
            ), mock.patch(
                "zec_checkout_gate.run_client",
                side_effect=GateError("endpoint", "UNREACHABLE", "unreachable"),
            ):
                with self.assertRaises(GateError):
                    light_preflight(args)
            self.assertFalse(wallet_dir.exists())

    def test_cleanup_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as parent:
            wallet_dir = pathlib.Path(parent) / "wallet"
            wallet_dir.mkdir()
            args = SimpleNamespace(zingo_cli=sys.executable, server="https://testnet.example:443")
            with mock.patch("zec_checkout_gate.tempfile.mkdtemp", return_value=str(wallet_dir)), mock.patch(
                "zec_checkout_gate.base_transcript", return_value={}
            ), mock.patch(
                "zec_checkout_gate.run_client",
                side_effect=GateError("endpoint", "UNREACHABLE", "unreachable"),
            ), mock.patch("zec_checkout_gate.shutil.rmtree", side_effect=OSError("cleanup failed")):
                with self.assertRaises(GateError) as context:
                    light_preflight(args)
            self.assertEqual(context.exception.code, "TEMP_WALLET_CLEANUP_FAILED")


if __name__ == "__main__":
    unittest.main()
