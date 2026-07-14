# Transcript schema

The harness writes `shielded-zec-feasibility/v1` JSON.

Required pass fields:

| Field | Meaning |
|---|---|
| `status` | Must be `passed` |
| `network` | Must be `testnet` |
| `versions` | Pinned Zallet, Zebra, and Zaino versions |
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

Blocked runs contain `stage`, `blockerCode`, `blocker`, and optionally `shortestResolution`. A blocked transcript is evidence of an attempted or preflighted gate, not evidence of payment success.

The transcript must never contain mnemonic phrases, keys, RPC credentials, wallet paths, account UUIDs, payer source addresses, or full merchant Unified Addresses.
