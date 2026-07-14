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

Status on 2026-07-14: **passed for one real public-testnet shielded checkout.**

The payer spent a confirmed Ironwood funding note to merchant address index 2.
The buyer-visible UA contained Orchard and Sapling receivers and no transparent
receiver. The merchant's UFVK-only wallet detected 99,990,000 zat as a confirmed
Ironwood note for txid
`3f98a2d722f4a8e5436ac6b753a5c9465c992b9736fdb0a9bd328e2a497d4be6`.
Independent chain inspection reported `shielded_only`, two Ironwood actions,
and zero transparent inputs, transparent outputs, Sapling spends/outputs, and
legacy Orchard actions. The redacted record is
`artifacts/light-client-ironwood-checkout-2026-07-14.json`.

The first attempt provisioned pinned Zebra and Zallet processes and derived shielded-only payer and merchant UAs. The [Fauzec community testnet faucet](https://fauzec.com/) confirmed 1 TAZ of full-privacy funding to the payer's Unified Address, but the local validator had not reached the public testnet tip, so the payer wallet could not detect or spend that note and a checkout payment was not attempted. The exact point-in-time machine-readable blocker remains in `artifacts/feasibility-2026-07-14.json` as USD 0 prior-work evidence.

The co-located full-node approach was then superseded because its resource cost is not appropriate for the default merchant deployment or this narrow gate. The dedicated runtime was stopped and its reproducible chain cache removed. Encrypted wallet state was retained because it controls the disposable testnet identities and funded note. See [the backend decision](backend-decision.md) and [long-term architecture](architecture.md).

The replacement preflight pinned ZingoLib `v5.0.0` at source commit
`9e897f8b2fc5f12a99604f2533164af62af7d3ac`. The locally built `zingo-cli`
package `0.4.0` binary reached `https://testnet.zec.rocks:443`, confirmed the endpoint's
`test` network and current height, and generated a disposable testnet UA with
exactly Orchard and Sapling receivers and `has_transparent=false`. The harness
then deleted the temporary wallet. The redacted result is
`artifacts/light-client-preflight-2026-07-14.json`; it records USD 0 requested
and explicitly records that no funded payment was attempted.

Two persistent disposable wallets were then created privately at birthday
height `4170213` and scanned through the same light-client endpoint. Both began
with zero Orchard, Sapling, and transparent balances. The payer address and two
unique merchant order addresses passed the Orchard + Sapling receiver guard;
only address prefixes and SHA-256 commitments are published. Wallet directories
are `0700` and wallet files were restored to `0600` after detecting the upstream
atomic-save mode caveat. See
`artifacts/light-client-wallet-preflight-2026-07-14.json`.

Fauzec then confirmed 1 TAZ with `full_privacy` to the shielded-only payer UA at
testnet height `4170365`. The pinned v5 wallet scanned and performed one bounded
rescan from birthday `4170213` through height `4170373`, but still reported zero
Orchard outputs, zero Sapling outputs, zero notes, and zero balance. The payer-to-
merchant send was stopped. The exact blocker is recorded in
`artifacts/light-client-note-blocker-2026-07-14.json`.

One bounded ordinary `dev` comparison then built and used
`dev@6f507e55c666c2cc0b0a1f6be48c8c50e5e40e55`. Its scan counter reported two
outputs under a legacy Sapling label, but independent transaction inspection
shows that the funding transaction actually contains two Ironwood actions and
no Sapling outputs. That branch did not include the wallet's Ironwood receive
path and correctly remains a point-in-time blocker record in
`artifacts/light-client-dev-note-blocker-2026-07-14.json`.

The exact `feat/ironwood` head
`b8af4fd520c7a4833b253b044d7e61626e44b2af`, pinned to
`librustzcash@4d9a68dc80508e7644aa99e1b4add7c831057bba`, detected the funding note
through the same CompactTxStreamer endpoint. Its send proposal initially
over-counted the V3 input as a legacy Orchard bundle and the builder rejected
the 10,000 zat imbalance. A narrow local feasibility patch split V2 and V3
inputs for fee accounting; the exact public-safe patch is
`artifacts/ironwood-input-fee-accounting.patch`. After the patch, one isolated
retry built, broadcast, mined, and detected the checkout successfully.

## Shortest resolution

1. Completed: endpoint, wallet, receiver, real send, mined transaction, and merchant UFVK confirmation evidence.
2. Completed: pin the exact Ironwood feature source, dependency commit, local patch, binary digest, and redacted transcript.
3. Before any production dependency choice, obtain an upstream release or reviewed equivalent that includes correct Ironwood input fee accounting.
4. Reproduce this same gate independently with that candidate and remove the local feasibility patch.

Do not proceed into Mobazha's primary payment path, production restart recovery, withdrawal, or hosted detector work during this pre-application gate.
