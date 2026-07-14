# Backend and version decision

Status: **superseded on 2026-07-14 before any checkout payment was attempted.** The co-located Zebra and Zallet path below is retained as reproducible prior evidence, not as the default architecture or the next feasibility path.

## Current decision

Use a local light-client wallet against configurable CompactTxStreamer endpoints. Do not require a co-located full validator for the default standalone checkout deployment.

- The merchant sidecar performs compact-block scanning and shielded note trial decryption locally.
- The remote chain-data service receives no viewing key, spending key, address list, or order mapping.
- The provider contract remains independent of Zaino, Lightwalletd, or any particular endpoint operator.
- Production profiles should compare independent endpoints and fail closed on disagreement or stale data.
- A merchant-operated Zebra plus Zaino stack remains an optional sovereign deployment profile.

ZingoLib `v5.0.0` passed endpoint and address preflight but is rejected for the
current funded gate because it predates the active Ironwood wallet path. The
ordinary `dev` comparison below also lacked that receive path. Neither result
is evidence of a broken CompactTxStreamer architecture.

`zingolib_v5.0.0` was rechecked against the official upstream refs on
2026-07-14 and remains the newest stable tag. The release publishes source but
no prebuilt assets. The active `dev` branch contains later, untagged work; it is
not used for this reproducible gate.

The active branch merged preparatory `pre_ironwood` work on 2026-07-13, after
the v5 tag was published. One bounded comparison used
`dev@6f507e55c666c2cc0b0a1f6be48c8c50e5e40e55`; it completed a fresh scan but
also did not detect the confirmed payer note. The actual receive implementation
was on `feat/ironwood`, not ordinary `dev`. A tagged release remains preferred;
an untagged feature branch is exact-commit evidence only and cannot be presented
as stable packaging.

### Light-client preflight evidence

The first two candidate checks passed on 2026-07-14:

- source tag `zingolib_v5.0.0`, commit `9e897f8b2fc5f12a99604f2533164af62af7d3ac`;
- locally built `zingo-cli` package `0.4.0`, SHA-256 `1cab62c9f3bdee425942e5d9c328f4f765c7609d7a97ef14fbe7172b6b91343c`;
- public-testnet CompactTxStreamer response from `https://testnet.zec.rocks:443`;
- disposable UA reported Orchard and Sapling receivers with no transparent receiver;
- temporary wallet state was deleted after the preflight.

This initial record proves endpoint compatibility and receiver control only.

The funded check then confirmed 1 TAZ to the payer UA at height `4170365`.
ZingoLib v5 scanned and rescanned through `4170373` while reporting zero shielded
outputs, notes, and balance. The checkout send was correctly stopped. See
`artifacts/light-client-note-blocker-2026-07-14.json`.

The exact ordinary dev comparison built `zingo-cli` package `0.4.0` from
commit `6f507e55c666c2cc0b0a1f6be48c8c50e5e40e55` (binary SHA-256
`4d5e1af45d6e42be7708a397b8321f2e15634952ccee76c891873de190a1132d`). Its
first compact-server ChainTip request timed out; one in-session retry then
rescanned heights `4170213` through `4170438` completely. Its legacy counter
reported two Sapling outputs, but chain inspection identifies them as Ironwood
actions. It found no wallet note and no checkout send was attempted. See
`artifacts/light-client-dev-note-blocker-2026-07-14.json`.

The feasibility pass used `feat/ironwood` commit
`b8af4fd520c7a4833b253b044d7e61626e44b2af` and
`librustzcash@4d9a68dc80508e7644aa99e1b4add7c831057bba`. Receive scanning worked,
but the fee proposal counted V3 spends in the legacy Orchard view while the
builder placed them in Ironwood. A narrow local patch aligned those views. The
resulting `zingo-cli` binary SHA-256 was
`9f2f113d6a9d2356e6051d9e9f6959e5ad919dc5478976f7bce2b962489942a3`.
This exact candidate passed one real payment but is not adopted for production;
the patch needs upstream review or replacement and an independent rerun.

The source tag is annotated but not cryptographically signed. Its Cargo package
and changelog say `zingo-cli 0.4.0`, while the same commit's internal version
constant makes `--version` report `Zingo CLI 0.1.1`. The exact source commit,
locked dependencies, and binary digest are therefore authoritative for this
preflight; the version-label mismatch remains a production packaging caveat.

The CLI's atomic wallet save also creates its temporary file without an explicit
Unix mode. Under a default `umask 022`, a save changed the disposable wallet
file from `0600` to `0644`; the enclosing directory remained `0700`, and the
file was immediately restored to `0600`. The harness now runs the CLI under
`umask 077` and fails unless the resulting wallet file is exactly `0600`.
Production persistence must enforce this independently rather than relying on
the operator's shell umask.

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

1. Completed: pin the light-client wallet source and build inputs.
2. Completed: probe a testnet CompactTxStreamer endpoint for network, height, and current protocol compatibility.
3. Completed: create and scan disposable payer and merchant wallets at a recent birthday.
4. Completed: derive two unique merchant UAs and inspect their shielded-only receiver sets.
5. Completed: detect the confirmed Ironwood payer funding note with the exact feature-branch candidate.
6. Completed: run exactly one real payer-to-merchant payment and save the confirmed merchant-note transcript.
7. Next: replace the local fee-accounting patch with an upstream-reviewed release and independently repeat the same gate.
8. Stop without entering production integration, withdrawal, or hosted detector work.

All work and artifacts from both feasibility attempts are prior work with **USD 0 requested**.

## References

- [Zallet user guide](https://zcash.github.io/zallet/)
- [Zallet v0.1.0-beta.1](https://github.com/zcash/zallet/releases/tag/v0.1.0-beta.1)
- [Zebra v6.0.0](https://github.com/ZcashFoundation/zebra/releases/tag/v6.0.0)
- [Zaino 0.6.0](https://github.com/zingolabs/zaino/releases/tag/0.6.0)
- [ZingoLib v5.0.0](https://github.com/zingolabs/zingolib/releases/tag/zingolib_v5.0.0)
- [ZingoLib Ironwood feature merge record](https://github.com/zingolabs/zingolib/pull/2428)
- [Ironwood activation on the current community testnet](https://forum.zcashcommunity.com/t/ironwood-is-active-on-testnet-zec-rocks/56557)
- [ZIP 307](https://zips.z.cash/zip-0307)
