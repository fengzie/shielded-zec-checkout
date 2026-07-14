.PHONY: test check light-preflight scan

test:
	python3 -m unittest discover -s harness/tests -v

check: test
	python3 -m compileall -q harness
	python3 harness/zec_checkout_gate.py verify-transcript --transcript artifacts/light-client-ironwood-checkout-2026-07-14.json >/dev/null

light-preflight:
	@test -n "$(ZINGO_CLI)" || (echo "Set ZINGO_CLI to a pinned zingo-cli binary" >&2; exit 2)
	python3 harness/zec_checkout_gate.py light-preflight --zingo-cli "$(ZINGO_CLI)" --out artifacts/private/light-client-preflight.json

scan:
	./scripts/scan-public.sh
