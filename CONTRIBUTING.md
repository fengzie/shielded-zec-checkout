# Contributing

Contributions are welcome when they preserve the project's shielded-only and fail-closed guarantees.

## Development

1. Use Python 3.11 or newer.
2. Run `make test` before submitting a change.
3. Run `scripts/scan-public.sh` and any private redline patterns supplied by the maintainer.
4. Keep fixtures synthetic unless an artifact is explicitly identified as a redacted public testnet transcript.

## Required invariants

- Never add a transparent receiver to a buyer-visible address.
- Never fall back to transparent ZEC when a shielded backend is unavailable.
- Never log RPC credentials, seed material, viewing keys, spending keys, wallet paths, or full Unified Addresses.
- Keep testnet and mainnet configuration explicit and fail on a network mismatch.
- Do not describe mock or contract-fixture results as a real network payment.

## Commit safety

Public commits must use the public identity `fengzie` where the maintainer identity is needed. Do not include private product names, personal names, credentials, or internal-only repository paths in commit messages or public artifacts.

By contributing, you agree that your contribution is licensed under Apache-2.0.
