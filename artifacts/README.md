# Feasibility artifacts

This directory contains public-safe, machine-readable feasibility records.

- A `passed` record must come from a real testnet payment and pass the harness transcript validator.
- A `preflight-passed` record proves only endpoint and shielded receiver checks;
  it must state that no funded payment was attempted.
- A `wallet-preflight-passed` record may commit to private disposable wallet
  addresses and permissions, but it is still not payment evidence.
- A `blocked` record must state the exact missing external condition.
- A confirmed faucet transaction is payer-fixture preparation, not a successful
  checkout; failure to detect it must remain a blocked record.
- An exact untagged comparison is evidence only for that commit; a completed
  scan that cannot detect the fixture note is a blocker, not a reason to try
  further unpinned revisions.
- Blocked records are immutable point-in-time evidence; consult `docs/feasibility.md` for the current backend decision and resolution path.
- `light-client-ironwood-checkout-2026-07-14.json` is the first passed record. It pins an untagged feature branch and a local feasibility patch, so it is not evidence of production readiness.
- `ironwood-input-fee-accounting.patch` is the public-safe minimal diff used for that run, based on the exact `librustzcash` commit named in the transcript.
- Contract fixtures and handwritten examples must not be labeled as passed results.
- Secrets, wallet paths, account identifiers, and full Unified Addresses are prohibited.
