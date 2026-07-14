# Feasibility artifacts

This directory contains public-safe, machine-readable feasibility records.

- A `passed` record must be emitted by the harness from a real testnet payment.
- A `blocked` record must state the exact missing external condition.
- Blocked records are immutable point-in-time evidence; consult `docs/feasibility.md` for the current backend decision and resolution path.
- Contract fixtures and handwritten examples must not be labeled as passed results.
- Secrets, wallet paths, account identifiers, and full Unified Addresses are prohibited.
