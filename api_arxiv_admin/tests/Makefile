

include test-env
export $(shell sed 's/=.*//' test-env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: dump

dump:
	docker run --rm --network host \
		-v $(CURDIR)/../../tests/data/test-db-dump:/dump-data \
		mydumper/mydumper:latest \
		mydumper \
		--host=127.0.0.1 \
		--port=${ARXIV_DB_PORT} \
		--user=root \
		--password=root_password \
		--database=arXiv \
		--outputdir=/dump-data
