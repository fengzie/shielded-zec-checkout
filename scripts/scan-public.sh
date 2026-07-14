#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if rg -n --hidden --glob '!.git/**' \
  '(gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)' .; then
  echo "possible secret material found" >&2
  exit 1
fi

for pattern in "$@"; do
  if rg -n -i --hidden --glob '!.git/**' --fixed-strings -- "$pattern" .; then
    echo "forbidden public pattern found" >&2
    exit 1
  fi
done

if git rev-parse --verify HEAD >/dev/null 2>&1; then
  authors="$(git log --format='%an|%ae')"
  if [[ -n "$authors" ]] && ! grep -Eq '^fengzie\|[0-9]+\+fengzie@users\.noreply\.github\.com$' <<<"$authors"; then
    echo "unexpected public commit identity found" >&2
    exit 1
  fi
fi

echo "public safety scan passed"
