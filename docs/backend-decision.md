# Backend and version decision

Status: accepted for the pre-application feasibility gate on 2026-07-14. This is not a production endorsement.

## Decision

Use the Zallet `zaino` backend against a co-located Zebra node:

| Component | Pinned version | Verification |
|---|---:|---|
| Zallet | `v0.1.0-beta.1` / source `5be0f4861feedc47978102c627c6293dea2d7838` | Official release binary executed locally and reported `zallet 0.1.0-beta.1` |
| Zebra | `v6.0.0` / source `bb41d69013edbfa8594bb097fa751f47eeb31445` | Official release and NU6.3 testnet activation record checked |
| Zaino | `0.6.0` | Latest official Zaino release checked; the feasibility deployment uses Zallet's embedded `zaino` backend rather than a separately operated indexer |

The locally verified Zallet Linux arm64 `zaino` backend artifact had SHA-256:

```text
05d30bd98772680cfd1aa1949aef2914acd51db8f4b014bf06b5c26efff1d50c
```

## Why this path

- Zallet is the current wallet replacement path and exposes the required account, UA receiver inspection, note listing, send, and operation-status RPCs.
- The `zaino` backend is the portable option for separate services and talks to stock Zebra JSON-RPC. The direct Zebra state backend is Linux-only, requires a specially built Zebra indexer feature, and does not support regtest.
- Zebra `v6.0.0` and Zallet `v0.1.0-beta.1` both include the current NU6.3 testnet rules. Older local results must not be reused as current API evidence.
- The harness keeps backend calls narrow and explicit so a later backend revision does not alter the public checkout contract.

## Observed packaging caveat

The official `zodlinc/zallet:v0.1.0-beta.1` image digest observed locally was:

```text
sha256:639c36a7c7bf2dc8c9c8e00f2e9a9107401af80c4dac4f3cf2adcb1b1880c3ee
```

Invoking its launcher selected `zallet-zebra`, but the backend binary was absent from the image filesystem. The separately published `zallet-zaino` release binary ran successfully when mounted into the same minimal runtime. This repository therefore pins the direct release artifact for the feasibility run and records the image behavior as needing upstream confirmation. No upstream contact has been made in this phase.

## Production boundary

Zallet describes this release as beta and warns that breaking changes and wallet recreation may be required. Passing one testnet payment is only a feasibility result. Production hardening, stable restart recovery, withdrawal, failure-path tests, and independent reproduction remain future funded work.

## Official references

- [Zallet user guide](https://zcash.github.io/zallet/)
- [Zallet v0.1.0-beta.1](https://github.com/zcash/zallet/releases/tag/v0.1.0-beta.1)
- [Zebra v6.0.0](https://github.com/ZcashFoundation/zebra/releases/tag/v6.0.0)
- [Zaino 0.6.0](https://github.com/zingolabs/zaino/releases/tag/0.6.0)
