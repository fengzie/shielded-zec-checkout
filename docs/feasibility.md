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

Status on 2026-07-14: **the first backend attempt was stopped before payment; no testnet result is claimed.**

The first attempt provisioned pinned Zebra and Zallet processes and derived shielded-only payer and merchant UAs. The [Fauzec community testnet faucet](https://fauzec.com/) confirmed 1 TAZ of full-privacy funding to the payer's Unified Address, but the local validator had not reached the public testnet tip, so the payer wallet could not detect or spend that note and a checkout payment was not attempted. The exact point-in-time machine-readable blocker remains in `artifacts/feasibility-2026-07-14.json` as USD 0 prior-work evidence.

The co-located full-node approach was then superseded because its resource cost is not appropriate for the default merchant deployment or this narrow gate. The dedicated runtime was stopped and its reproducible chain cache removed. Encrypted wallet state was retained because it controls the disposable testnet identities and funded note. See [the backend decision](backend-decision.md) and [long-term architecture](architecture.md).

## Shortest resolution

1. Pin and build the selected light-client wallet candidate.
2. Verify a current testnet CompactTxStreamer endpoint's network, height, and protocol compatibility without sending wallet keys or addresses.
3. Create fresh disposable payer and merchant wallets at a recent wallet birthday.
4. Prove the buyer-visible address contains only allowed shielded receivers.
5. Fund the new payer, run one real payment, and stop when a confirmed payer-to-merchant note transcript is written.

Do not proceed into Mobazha's primary payment path, production restart recovery, withdrawal, or hosted detector work during this pre-application gate.
