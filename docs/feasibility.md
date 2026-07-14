# Testnet feasibility gate

## Required pass condition

One real Zcash testnet run must complete:

```text
funded shielded payer
  -> merchant per-order Orchard + Sapling Unified Address
  -> receiver inspection proves no p2pkh or p2sh receiver
  -> merchant wallet detects the exact note
  -> note reaches at least one confirmation
  -> redacted machine-readable transcript is saved
```

A mock, Docker contract fixture, regtest-only address derivation, or hand-authored JSON file does not pass this gate.

## Current result

Status on 2026-07-14: **blocked before payment; no testnet result claimed.**

The current machine has no provisioned, synchronized testnet merchant and payer Zallet RPC endpoints and no funded shielded testnet payer wallet. The official Zallet beta release binary was verified, but a payment was not attempted. The exact machine-readable blocker is in `artifacts/feasibility-2026-07-14.json`.

## Shortest resolution

1. Start Zebra `v6.0.0` on testnet with authenticated loopback JSON-RPC.
2. Start two Zallet `v0.1.0-beta.1` wallets using the `zaino` backend and wait for sync.
3. Fund the payer wallet with shielded testnet ZEC from a legitimate testnet source.
4. Run the repository harness once and stop when a confirmed note transcript is written.

Do not proceed into Mobazha's primary payment path, production restart recovery, withdrawal, or hosted detector work during this pre-application gate.
