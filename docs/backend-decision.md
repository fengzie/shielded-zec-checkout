# Backend and version decision

Status: **superseded on 2026-07-14 before any checkout payment was attempted.** The co-located Zebra and Zallet path below is retained as reproducible prior evidence, not as the default architecture or the next feasibility path.

## Current decision

Use a local light-client wallet against configurable CompactTxStreamer endpoints. Do not require a co-located full validator for the default standalone checkout deployment.

- The merchant sidecar performs compact-block scanning and shielded note trial decryption locally.
- The remote chain-data service receives no viewing key, spending key, address list, or order mapping.
- The provider contract remains independent of Zaino, Lightwalletd, or any particular endpoint operator.
- Production profiles should compare independent endpoints and fail closed on disagreement or stale data.
- A merchant-operated Zebra plus Zaino stack remains an optional sovereign deployment profile.

ZingoLib `v5.0.0` is the leading candidate for the next pre-application feasibility attempt. Selection remains provisional until its current testnet CompactTxStreamer path, shielded-only address derivation, sending behavior, confirmation detection, and machine-readable automation are exercised locally. Production library selection remains future funded work and must not be claimed by the feasibility result.

The stable architecture and trust boundaries are recorded in [Long-term architecture](architecture.md).

## Why the previous path was superseded

Zallet is a full-node wallet. Both of its current backends depend on Zebra state, so the feasibility deployment inherited a full testnet validation sync. That provided a narrow, self-validated chain view but imposed substantial startup time, CPU use, and storage for a gate that only needs one real shielded payment.

Shielded payment detection requires local scanning because note ciphertexts must be trial-decrypted with wallet key material. It does not require every merchant to validate and retain the full chain. The CompactTxStreamer protocol provides the smaller and more appropriate boundary.

The dedicated attempt was stopped before payment. Its containers and Docker network were removed, and its reproducible validator cache and downloaded binaries were deleted. The small encrypted payer and merchant wallet directories were retained because they control disposable testnet identities and the confirmed faucet-funded note.

## Superseded full-node attempt

The superseded attempt used the Zallet `zaino` backend against a co-located Zebra node:

| Component | Pinned version | Verification |
|---|---:|---|
| Zallet | `v0.1.0-beta.1` / source `5be0f4861feedc47978102c627c6293dea2d7838` | Official release binary executed locally and reported `zallet 0.1.0-beta.1` |
| Zebra | `v6.0.0` / source `bb41d69013edbfa8594bb097fa751f47eeb31445` | Official release and NU6.3 testnet activation record checked |
| Zallet embedded Zaino libraries | `zaino-fetch 0.2.1`, `zaino-state 0.3.1` / source `8048bf8df61cd409af8c22518a16514bee02a0fb` | Exact dependencies recorded in the Zallet release source; no separate `zainod` process is operated |

The locally verified Zallet Linux arm64 `zaino` backend artifact had SHA-256:

```text
05d30bd98772680cfd1aa1949aef2914acd51db8f4b014bf06b5c26efff1d50c
```

The locally verified Zebra Linux arm64 binary had SHA-256:

```text
8b21c20421c4979481b44d2d602eec493f60bebe250137a645379977ad4d7d92
```

Zaino `0.6.0` was also checked as the current standalone upstream release on the decision date, but it is not a runtime component or transcript version for this deployment.

### Why it was initially selected

- Zallet is the current wallet replacement path and exposes the required account, UA receiver inspection, note listing, send, and operation-status RPCs.
- The `zaino` backend is the portable option for separate services and talks to stock Zebra JSON-RPC. The direct Zebra state backend is Linux-only, requires a specially built Zebra indexer feature, and does not support regtest.
- Zebra `v6.0.0` and Zallet `v0.1.0-beta.1` both include the current NU6.3 testnet rules. Older local results must not be reused as current API evidence.
- The harness keeps backend calls narrow and explicit so a later backend revision does not alter the public checkout contract.

### Observed packaging caveat

The official `zodlinc/zallet:v0.1.0-beta.1` image digest observed locally was:

```text
sha256:639c36a7c7bf2dc8c9c8e00f2e9a9107401af80c4dac4f3cf2adcb1b1880c3ee
```

Invoking its launcher selected `zallet-zebra`, but the backend binary was absent from the image filesystem. The separately published `zallet-zaino` release binary could report its version in that minimal image, but the image also lacked CA certificates and the Zaino client failed during startup. The feasibility deployment therefore pins the direct release artifact and runs it in a CA-enabled ARM64 glibc userspace. The image behavior is recorded as needing upstream confirmation; no upstream contact has been made in this phase.

### Production boundary

Zallet describes this release as beta and warns that breaking changes and wallet recreation may be required. Passing one testnet payment is only a feasibility result. Production hardening, stable restart recovery, withdrawal, failure-path tests, and independent reproduction remain future funded work.

## Next feasibility path

1. Pin the light-client wallet source and build inputs.
2. Probe at least one testnet CompactTxStreamer endpoint for network, height, and current protocol compatibility.
3. Create fresh disposable payer and merchant wallets at a recent wallet birthday.
4. Derive and inspect a shielded-only buyer address before requesting funds.
5. Run exactly one real payer-to-merchant payment, detect the confirmed note locally, and save a redacted transcript.
6. Stop without entering production integration, withdrawal, or hosted detector work.

All work and artifacts from both feasibility attempts are prior work with **USD 0 requested**.

## References

- [Zallet user guide](https://zcash.github.io/zallet/)
- [Zallet v0.1.0-beta.1](https://github.com/zcash/zallet/releases/tag/v0.1.0-beta.1)
- [Zebra v6.0.0](https://github.com/ZcashFoundation/zebra/releases/tag/v6.0.0)
- [Zaino 0.6.0](https://github.com/zingolabs/zaino/releases/tag/0.6.0)
- [ZingoLib v5.0.0](https://github.com/zingolabs/zingolib/releases/tag/zingolib_v5.0.0)
- [ZIP 307](https://zips.z.cash/zip-0307)
