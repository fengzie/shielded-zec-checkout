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

## Status

Pre-application feasibility work only. The repository does not yet claim a production backend, restart recovery, withdrawal support, complete failure-path coverage, or third-party reproduction. See [the current feasibility record](docs/feasibility.md).

## Quick start

Requirements:

- Python 3.11 or newer;
- a fully synchronized Zebra testnet validator and two synchronized Zallet wallets using the pinned backend decision;
- a payer wallet with spendable shielded testnet ZEC;
- RPC credentials supplied only through environment variables.

Run local tests:

```bash
make test
```

Probe configured RPC endpoints without sending funds:

```bash
export VALIDATOR_RPC_URL=http://127.0.0.1:18232
export VALIDATOR_RPC_USER=local-rpc-user
export VALIDATOR_RPC_PASSWORD='set-locally'
export MERCHANT_RPC_URL=http://127.0.0.1:28232
export MERCHANT_RPC_USER=local-rpc-user
export MERCHANT_RPC_PASSWORD='set-locally'
export PAYER_RPC_URL=http://127.0.0.1:38232
export PAYER_RPC_USER=local-rpc-user
export PAYER_RPC_PASSWORD='set-locally'

make probe
```

Run the real gate after the payer wallet is funded:

```bash
export PAYER_FROM_ADDRESS='utest1...'
python3 harness/zec_checkout_gate.py run \
  --merchant-account-name merchant-feasibility \
  --payer-from-address "$PAYER_FROM_ADDRESS" \
  --amount-zatoshi 100000 \
  --confirmations 1 \
  --out artifacts/testnet-feasibility.json
```

RPC passwords, mnemonic phrases, spending keys, viewing keys, wallet paths, and full Unified Addresses are never written to the transcript.
The harness queries Zebra directly and fails closed until its reported testnet verification progress reaches `0.99999`.

## Documentation

- [Prior work ledger](docs/prior-work.md)
- [Backend and version decision](docs/backend-decision.md)
- [Feasibility gate and blocker](docs/feasibility.md)
- [Transcript schema](docs/transcript-schema.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

## License

Apache License 2.0 applies to the contents of this repository. The prior-work ledger cites unpublished private work for provenance only; no historical source code is included in or licensed through this repository.
