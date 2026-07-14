import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from zec_checkout_gate import (  # noqa: E402
    GateError,
    address_commitment,
    assert_shielded_only,
    assert_shielded_source,
    assert_testnet_ua,
    assert_wallet_synced,
    receiver_types,
    sanitize_text,
    zatoshi_to_zec,
)


class ReceiverGuardTests(unittest.TestCase):
    def test_accepts_orchard_and_sapling(self):
        receivers = {"orchard": "u1orchard", "sapling": "zs1sapling"}
        self.assertEqual(assert_shielded_only(receivers), ["orchard", "sapling"])

    def test_rejects_p2pkh(self):
        with self.assertRaises(GateError) as context:
            assert_shielded_only({"orchard": "u1orchard", "sapling": "zs1sapling", "p2pkh": "tm..."})
        self.assertEqual(context.exception.code, "TRANSPARENT_OR_UNKNOWN_RECEIVER")

    def test_rejects_unknown_receiver(self):
        with self.assertRaises(GateError):
            assert_shielded_only({"orchard": "u1orchard", "sapling": "zs1sapling", "future": "x"})

    def test_requires_both_shielded_receivers(self):
        with self.assertRaises(GateError) as context:
            assert_shielded_only({"orchard": "u1orchard"})
        self.assertEqual(context.exception.code, "REQUIRED_SHIELDED_RECEIVER_MISSING")

    def test_omits_empty_receiver_values(self):
        self.assertEqual(receiver_types({"orchard": "x", "p2pkh": None}), ["orchard"])

    def test_payer_can_be_orchard_only(self):
        self.assertEqual(assert_shielded_source({"orchard": "x"}), ["orchard"])

    def test_payer_rejects_transparent_receiver(self):
        with self.assertRaises(GateError):
            assert_shielded_source({"orchard": "x", "p2pkh": "tm..."})


class NetworkAndSyncTests(unittest.TestCase):
    def test_accepts_public_testnet_ua(self):
        assert_testnet_ua("utest1" + "a" * 30, "test")

    def test_rejects_mainnet_and_regtest_ua(self):
        for address in ("u1" + "a" * 30, "uregtest1" + "a" * 30):
            with self.assertRaises(GateError):
                assert_testnet_ua(address, "test")

    def test_accepts_synced_wallet(self):
        assert_wallet_synced(
            {"node_tip": {"height": 100}, "wallet_tip": {"height": 100}},
            "sync",
        )

    def test_rejects_wallet_with_remaining_work(self):
        with self.assertRaises(GateError):
            assert_wallet_synced(
                {
                    "node_tip": {"height": 100},
                    "wallet_tip": {"height": 100},
                    "sync_work_remaining": {"unscanned_blocks": 1},
                },
                "sync",
            )


class RedactionTests(unittest.TestCase):
    def test_address_commitment_does_not_expose_full_address(self):
        address = "utest1" + "a" * 80
        commitment = address_commitment(address)
        self.assertNotIn(address, commitment.values())
        self.assertEqual(len(commitment["sha256"]), 64)

    def test_sanitizes_url_and_local_path(self):
        value = sanitize_text("failed at http://127.0.0.1:28232 in /Users/example/wallet")
        self.assertNotIn("127.0.0.1", value)
        self.assertNotIn("/Users/example", value)


class AmountTests(unittest.TestCase):
    def test_zatoshi_conversion(self):
        self.assertEqual(zatoshi_to_zec(100_000), 0.001)

    def test_rejects_non_positive_amount(self):
        with self.assertRaises(GateError):
            zatoshi_to_zec(0)


if __name__ == "__main__":
    unittest.main()
