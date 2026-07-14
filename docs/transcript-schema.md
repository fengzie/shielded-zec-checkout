# Transcript schema

The harness writes `shielded-zec-feasibility/v1` JSON.

`preflight-passed` means only that a pinned light client reached a public-testnet
CompactTxStreamer endpoint and generated a shielded-only testnet UA in a
discarded temporary wallet. It is not a payment result and cannot satisfy the
required pass condition below.

On POSIX systems, a preflight record must also report `walletFileMode: "0600"`.
The harness fails closed if the light client saves group- or world-readable
wallet state.

`wallet-preflight-passed` records may contain only address prefixes and SHA-256
commitments for persistent disposable wallets. They must record zero or observed
balances, private file modes, and `fundedPaymentAttempted: false`; they do not
satisfy the payment gate.

Required pass fields:

| Field | Meaning |
|---|---|
| `status` | Must be `passed` |
| `network` | Must be `testnet` |
| `versions` | Pinned wallet, light-client protocol implementation, and endpoint software versions observed by the gate |
| `merchantAddress.prefix` | Short non-secret display prefix |
| `merchantAddress.sha256` | Commitment to the full UA without publishing it |
| `perOrderAddressUnique` | Two allocations returned different UAs |
| `receiverTypes` | Exactly the observed shielded receiver kinds |
| `transparentReceiverPresent` | Must be `false` |
| `requestedAmountZatoshi` | Amount sent by the payer |
| `detectedAmountZatoshi` | Amount detected in the matching merchant note |
| `sendTxHash` | Public testnet transaction identifier |
| `confirmations` | Confirmations observed by the merchant wallet |
| `confirmedNoteDetected` | Must be `true` |
| `secretsRecorded` | Must be `false` |
| `usdRequested` | `0` for pre-application work |

For the Ironwood transition record, `receiverTypes` describes the receivers
encoded in the UA (`orchard` and `sapling`), while chain and wallet evidence may
identify the detected note pool as `ironwood`. The transcript must preserve
that distinction rather than relabel an Ironwood action as a Sapling output.

Blocked runs contain `stage`, `blockerCode`, `blocker`, and optionally `shortestResolution`. A blocked transcript is evidence of an attempted or preflighted gate, not evidence of payment success.

The transcript must never contain mnemonic phrases, keys, RPC credentials,
wallet paths, account UUIDs, full payer source addresses, or full merchant
Unified Addresses. Short prefixes and SHA-256 commitments are allowed.
