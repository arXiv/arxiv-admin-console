ARXIV_DB_PORT := 21601

.PHONY: bootstrap up down  mysql2sqlite-image

bootstrap:
	echo noop

up:
	docker  compose -f ./docker-compose-for-test.yaml --env-file=./test-env up -d


down:
	docker  compose -f ./docker-compose-for-test.yaml --env-file=./test-env down


#-#
#-# dump-arxiv-db:
#-#   dumps mysqldb://arxiv:arxiv_password@127.0.0.1:21504/arXiv?ssl=false&ssl_mode=DISABLED
dump-arxiv-db:
	mysqldump -n --user=root --password=root_password --host=127.0.0.1 --port=${ARXIV_DB_PORT} -q -y --skip-add-drop-table --skip-comments --skip-disable-keys --skip-lock-tables --ssl-mode=DISABLED --lock-all-tables --result-file ./data/test-db.sql arXiv


mysql2sqlite-image: /usr/bin/docker
	docker buildx build -f ./Dockerfile.mysql2sqlite \
		--security-opt seccomp=unconfined  \
		--progress=plain \
		--platform=linux/amd64 -t mysql2sqlite:latest .
