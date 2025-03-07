
.PHONY: bootstrap up down

bootstrap:
	echo noop

up:
	docker  compose -f ./docker-compose-for-test.yaml --env-file=./test-env up -d


down:
	docker  compose -f ./docker-compose-for-test.yaml --env-file=./test-env down
