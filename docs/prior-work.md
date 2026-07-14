# Prior work ledger

All entries below predate this public feasibility repository and are disclosed as existing, unfunded work. **USD 0 requested for every entry.** They are evidence of interface and integration exploration, not proof of a real testnet checkout.

Source location for all entries: an unpublished private Mobazha development repository. Commit IDs are recorded only as prior-work provenance; the corresponding source code is not included in or licensed through this repository. If any historical implementation is later proposed for inclusion, its ownership and licensing will be reviewed before publication.

| Commit | Public-safe summary | Tests / fixture evidence | Known limitation | Requested |
|---|---|---|---|---:|
| `108f7534fe2d3955d2cf628b93d8dee208a8460e` | Rail scaffold, central rail validation, sample transcript shape | Go tests for rail guards, checkout methods, sample helpers; example payer and checkout JSON fixtures | Offline and contract fixtures only | USD 0 |
| `ac8ddcb3d777c9693c83000de77178dc19942b6f` | Payment-session and Guest Checkout contract propagation | Handler, service, readiness-gate, projector, and session tests | No real wallet backend | USD 0 |
| `25bb84278492aa4cf98088fbd127da4d2ac8b3e4` | Narrow sidecar client, UA validation, address allocation, runtime readiness guard | Client, receiver guard, direct-payment, capability, and status tests | Buyer-visible gate deliberately closed | USD 0 |
| `11f739edae981ddcc1d6a2753aba4683afd77f5a` | Incoming-note monitor, confirmation gate, wallet metadata, setup contract | Monitor integration, wallet metadata, setup provider, and API contract tests | Note source remained simulated | USD 0 |
| `7f5c4e41ef8c28103783377b7473de86b705c5d4` | Balance, transfer, and withdrawal interface exploration | Client, service, handler, and contract tests | No verified real withdrawal | USD 0 |
| `1a5b41e31dc9b738dc8a3679a50a7dbf85ed5ba4` | Sidecar runtime and readiness wiring | Runtime wiring tests | Wiring remained deployment-profile-specific | USD 0 |
| `e04d1a50ba7747cc9a79497bb5a6b98891a53fab` | HTTP sidecar smoke mode and proof verifier | Sample smoke and proof-validation tests | Requires externally funded real note to pass | USD 0 |
| `199a44662758932da7d0c35258e49bb2d7657192` | Sidecar lifecycle projection in runtime status | Lifecycle status tests | Observability only | USD 0 |
| `79ebe997b56ac686c8d511ebe3d61de9f98c0601` | Disposable sidecar contract server and Docker fixture | Synthetic funded-note Docker fixture | Contract fixture is not a network payment | USD 0 |
| `05aad51c2bd4729f303c10579f24964bbafdd9d1` | Managed sidecar process exploration and Z3 adapter scripts | Process tests, adapter tests, local gate scripts | Historical stack could derive shielded-only UAs but could not produce a funded shielded payer, confirmed merchant note, or real withdrawal | USD 0 |

## Verification status

Re-run on 2026-07-14 from an isolated export of the historical branch, using Go 1.26.1 with `CGO_ENABLED=1` and the `goolm` build tag:

```text
go test -tags goolm ./samples/zcash-shielded-rail/... ./pkg/zcash/... ./internal/chains/zcashshielded/... -count=1
```

Result: pass for the sample, Z3 adapter, `pkg/zcash`, and sidecar client packages. The disposable contract server has no direct test files. These passing tests validate prior interfaces and fixtures only; they do not change the real testnet blocker or the USD 0 classification.

## Explicitly not completed by prior work

- a real testnet shielded payer to merchant UA payment;
- a confirmed merchant note transcript from a real backend;
- a production-candidate backend;
- restart recovery proven against real chain state;
- a real merchant withdrawal;
- comprehensive failure-path tests;
- independent third-party reproduction;
- a buyer-visible production release.
