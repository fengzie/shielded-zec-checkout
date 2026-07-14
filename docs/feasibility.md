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

The pinned Zebra and Zallet processes are provisioned and actively syncing, and shielded-only payer and merchant UAs have been derived. The [Fauzec community testnet faucet](https://fauzec.com/) confirmed 1 TAZ of full-privacy funding to the payer's Unified Address, but the local validator has not yet reached the public testnet tip, so the payer wallet cannot detect or spend that note and a checkout payment was not attempted. The exact machine-readable blocker is in `artifacts/feasibility-2026-07-14.json`.

## Shortest resolution

1. Let Zebra `v6.0.0` reach the public testnet tip and pass the `0.99999` validator verification-progress preflight.
2. Let both Zallet `v0.1.0-beta.1` wallets catch up to that validator tip.
3. Confirm the payer wallet detects the already-confirmed faucet note as spendable.
4. Run the repository harness once and stop when a confirmed payer-to-merchant note transcript is written.

Do not proceed into Mobazha's primary payment path, production restart recovery, withdrawal, or hosted detector work during this pre-application gate.
