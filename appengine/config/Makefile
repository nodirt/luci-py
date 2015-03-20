build: compile-proto

compile-proto:
	tools/compile_proto.py .

test: build
	tools/run_coverage.py

deploy: upload switch

upload: build
	tools/gae upload -f

switch:
	tools/gae switch -f `tools/gae version`

rollback:
	appcfg.py -V `tools/gae version` rollback .
