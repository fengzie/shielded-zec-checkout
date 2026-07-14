# Native Linux ARM64 testnet runbook

This is the smallest reproducible operator path for the pre-application feasibility gate. It is intentionally limited to native Linux ARM64, the platform used for the current run. It is not a production deployment guide.

Run every command from the repository root. Keep `runtime/` private; it contains wallet databases, encryption identities, RPC cookies, and full Unified Addresses and is excluded by `.gitignore`.

Prerequisites are a glibc-based Linux ARM64 system with CA certificates, plus `curl`, `jq`, `sha256sum`, `sed`, and `tar`.

## 1. Download and verify the pinned binaries

```bash
install -d -m 700 runtime/bin runtime/zebra/cache runtime/payer runtime/merchant

curl -fL \
  -o runtime/bin/zallet-zaino \
  https://github.com/zcash/zallet/releases/download/v0.1.0-beta.1/zallet-v0.1.0-beta.1-linux-arm64-zaino
printf '%s  %s\n' \
  05d30bd98772680cfd1aa1949aef2914acd51db8f4b014bf06b5c26efff1d50c \
  runtime/bin/zallet-zaino | sha256sum -c -

curl -fL \
  -o runtime/bin/zebrad.tar.gz \
  https://github.com/ZcashFoundation/zebra/releases/download/v6.0.0/zebrad-6.0.0-aarch64-unknown-linux-gnu.tar.gz
printf '%s  %s\n' \
  f227c56ea9a142803e7501c9bd6749963fd6f4290f4bc0b8214524e3a1b9f083 \
  runtime/bin/zebrad.tar.gz | sha256sum -c -
tar -xzf runtime/bin/zebrad.tar.gz -C runtime/bin zebrad

chmod 700 runtime/bin/zallet-zaino runtime/bin/zebrad
runtime/bin/zallet-zaino --version
runtime/bin/zebrad --version
```

Expected versions are `zallet 0.1.0-beta.1` and `zebrad 6.0.0`. The Zallet binary requires a CA-enabled Linux userspace even though the validator URL is HTTP; the release's minimal launcher image does not currently provide a complete runtime for this backend.

## 2. Start and fully synchronize Zebra

```bash
runtime/bin/zebrad -c examples/zebrad-testnet.toml start
```

The example enables cookie-authenticated RPC on loopback and persists testnet state under `runtime/zebra/cache`. Initial testnet synchronization commonly takes hours. Do not initialize the wallet accounts against a partial validator tip: account birthdays are derived from the validator state visible at creation time.

In another shell, read `runtime/zebra/.cookie` without printing it and call `getblockchaininfo`. Continue only when `chain` is `test` and `verificationprogress` is at least `0.99999`.

## 3. Initialize two disposable testnet wallets

```bash
cp examples/zallet-testnet.toml runtime/payer/zallet.toml
cp examples/zallet-testnet.toml runtime/merchant/zallet.toml
sed -i 's/127.0.0.1:28232/127.0.0.1:28233/' runtime/merchant/zallet.toml
chmod 600 runtime/payer/zallet.toml runtime/merchant/zallet.toml

for role in payer merchant; do
  runtime/bin/zallet-zaino -d "runtime/$role" generate-encryption-identity
  runtime/bin/zallet-zaino -d "runtime/$role" init-wallet-encryption
  runtime/bin/zallet-zaino -d "runtime/$role" generate-mnemonic
done
```

`generate-mnemonic` stores the mnemonic in the encrypted wallet; it does not print the phrase. These disposable testnet identities still control funds, so preserve the 0700/0600 permissions and never commit `runtime/`.

Start payer and merchant Zallet in separate shells:

```bash
runtime/bin/zallet-zaino -d runtime/payer start
runtime/bin/zallet-zaino -d runtime/merchant start
```

Create one payer account and derive its address by explicitly requesting `orchard` and `sapling`:

```bash
PAYER_ACCOUNT="$(
  runtime/bin/zallet-zaino -d runtime/payer \
    rpc z_getnewaccount '"feasibility-payer"' \
    | jq -r '.account_uuid'
)"

PAYER_ADDRESS="$(
  runtime/bin/zallet-zaino -d runtime/payer \
    rpc z_getaddressforaccount "\"$PAYER_ACCOUNT\"" '["orchard","sapling"]' \
    | jq -r '.address'
)"

runtime/bin/zallet-zaino -d runtime/payer \
  rpc z_listunifiedreceivers "\"$PAYER_ADDRESS\"" \
  | jq -e '(keys | sort) == ["orchard", "sapling"]'

umask 077
printf '%s\n' "$PAYER_ADDRESS" > runtime/payer/funding-address.txt
```

The receiver assertion must pass before the address is sent to a testnet faucet. Never omit the receiver list: Zallet's default address request also includes `p2pkh`.

## 4. Probe and run the gate

Read each service's `.cookie` into environment variables locally. Do not paste cookies into logs or transcripts.

```bash
export VALIDATOR_RPC_URL=http://127.0.0.1:18232
export MERCHANT_RPC_URL=http://127.0.0.1:28233
export PAYER_RPC_URL=http://127.0.0.1:28232

# Set the matching *_RPC_USER and *_RPC_PASSWORD values from each .cookie file.
make probe
```

After the payer has a spendable shielded testnet note, run the gate once:

```bash
python3 harness/zec_checkout_gate.py run \
  --merchant-account-name merchant-feasibility \
  --payer-from-address 'utest1...' \
  --amount-zatoshi 100000 \
  --confirmations 1 \
  --out artifacts/testnet-feasibility.json
```

Stop after one confirmed payer-to-merchant note. This runbook does not authorize production integration, withdrawal, hosted multi-tenant operation, or a transparent fallback.
