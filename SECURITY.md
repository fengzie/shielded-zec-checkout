# Security Policy

## Supported status

This repository is in a feasibility phase and is not production-ready. No current version should be used with mainnet funds.

## Reporting a vulnerability

Use GitHub private vulnerability reporting for this repository. Do not open a public issue for a suspected vulnerability involving keys, transaction privacy, receiver validation, authentication, or fund loss.

Include:

- affected commit;
- minimal reproduction steps;
- whether any real funds or private metadata may be at risk;
- suggested embargo needs.

Never include mnemonic phrases, spending keys, viewing keys, RPC credentials, or unredacted wallet data in a report.

## Security invariants

- Buyer-visible addresses must contain shielded receivers only.
- Receiver validation must fail closed on unknown or transparent receiver types.
- RPC endpoints should bind to loopback or a private network and require authentication.
- The harness must run on testnet and refuse mainnet.
- Public transcripts must be redacted and must not contain wallet secrets or full Unified Addresses.
