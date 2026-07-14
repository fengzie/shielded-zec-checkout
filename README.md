# Shielded ZEC Checkout

Shielded ZEC Checkout is a **shielded-only ZEC checkout provider and reference integration for self-hosted commerce**.

The project is an independent, community-built integration led by fengzie. It is not an official Zcash project and is not endorsed by the Electric Coin Company, the Zcash Foundation, or Zcash Community Grants.

## Scope

This repository starts with a narrow pre-application feasibility gate:

- derive a per-order Unified Address containing Orchard and Sapling receivers;
- fail closed if a transparent `p2pkh` or `p2sh` receiver is present;
- send a real testnet shielded payment from a pre-funded payer wallet;
- detect the merchant note and wait for confirmation;
- write a redacted, machine-readable transcript.

Transparent ZEC is never a fallback. A buyer-visible address must pass the receiver guard before it can be used.

The reference integration target is a merchant-operated standalone commerce node. Mobazha is the first integration host and a potential commercial user of the open-source work. This repository does not build or claim a hosted multi-tenant detector.

## Architecture

The default deployment is a local light-client sidecar, not a co-located full node. Consensus and compact-block services are shared or separately operated; merchant viewing capability, wallet state, address derivation, note detection, and order mapping stay local.

```mermaid
flowchart LR
    V["Zebra consensus nodes"] --> I["Zaino or Lightwalletd-compatible<br/>CompactTxStreamer endpoints"]
    I --> S["Local shielded checkout sidecar<br/>compact scan and wallet database"]
    K["Local UFVK<br/>no spending authority"] --> S
    S --> C["Commerce provider contract<br/>and order lifecycle"]
    W["Isolated signer or USK<br/>withdrawal only"] -.-> S
```

See [Long-term architecture](docs/architecture.md) for trust assumptions, key separation, endpoint policy, checkout events, and optional sovereign deployment.

## Status

Pre-application feasibility work only. The initial co-located Zebra and Zallet attempt was stopped before payment and superseded by a light-client architecture. On 2026-07-14, one real testnet payer-to-merchant run passed: a shielded-only merchant UA received 99,990,000 zat, an UFVK-only merchant wallet detected the confirmed Ironwood note, and the mined transaction contained no transparent, Sapling, or legacy Orchard components.

The run required exact untagged Ironwood sources plus a narrow local fee-accounting patch; it therefore proves feasibility, not a production-ready dependency. This repository does not claim a production backend, restart recovery, withdrawal support, complete failure-path coverage, or third-party reproduction. See [the current feasibility record](docs/feasibility.md) and [redacted transcript](artifacts/light-client-ironwood-checkout-2026-07-14.json).

## Quick start

Requirements:

- Python 3.9 or newer;
- no wallet backend or network access for the local unit tests.

Run local tests:

```bash
make test
```

Run the non-funding light-client preflight with an exact, locally verified
`zingo-cli` binary:

```bash
ZINGO_CLI=/absolute/path/to/zingo-cli make light-preflight
```

This contacts public testnet, creates a disposable temporary wallet, verifies an
Orchard + Sapling UA with no transparent receiver, writes a redacted transcript,
enforces a `0600` wallet file under a private temporary directory, and deletes
the wallet directory. It does not sync wallet history, request
funds, or send a transaction. The archived full-node runbook is retained only
as first-attempt evidence.

## Documentation

- [Prior work ledger](docs/prior-work.md)
- [Long-term architecture](docs/architecture.md)
- [Backend and version decision](docs/backend-decision.md)
- [Archived full-node testnet runbook](docs/testnet-runbook.md)
- [Feasibility gate and blocker](docs/feasibility.md)
- [Transcript schema](docs/transcript-schema.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License

Apache License 2.0 applies to the contents of this repository. The prior-work ledger cites unpublished private work for provenance only; no historical source code is included in or licensed through this repository.
