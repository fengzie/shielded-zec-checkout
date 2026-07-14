.PHONY: test check probe scan

test:
	python3 -m unittest discover -s harness/tests -v

check: test
	python3 -m compileall -q harness

probe:
	python3 harness/zec_checkout_gate.py probe --out artifacts/rpc-probe.json

scan:
	./scripts/scan-public.sh
