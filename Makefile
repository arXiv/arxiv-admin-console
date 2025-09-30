
DOCKER_DIRS := api_arxiv_admin ui-arxiv-admin
ALL_DIRS := $(DOCKER_DIRS) tests

include .env
export $(shell sed 's/=.*//' .env)

ARXIV_BASE_DIR ?= $(HOME)/arxiv/arxiv-base

.PHONY: HELLO all bootstrap docker-image up down

all: HELLO

define run_in_docker_dirs
	@for dir in $(DOCKER_DIRS); do \
		echo "Running $(1) in $$dir"; \
		$(MAKE) -C $$dir $(1) || exit 1; \
	done
endef

define run_in_all_subdirs
	@for dir in $(ALL_DIRS); do \
		echo "Running $(1) in $$dir"; \
		$(MAKE) -C $$dir $(1) || exit 1; \
	done
endef

HELLO:
	@echo To see the README of this Makefile, type "make help"

#-#
#-# help:
#-#   print help messsages
help:
	@awk '/^#-#/ { print substr($$0, 5)}' Makefile

.env: ../arxiv-keycloak/.env
	ln -s ../arxiv-keycloak/.env .env


#-#
#-# bootstrap:
#-#   bootstraps the environment
bootstrap: .bootstrap

.bootstrap: .env
	$(call run_in_all_subdirs,bootstrap)
	touch .bootstrap

#-#
#-# docker-image:
#-#   builds docker images
docker-image:
	$(call run_in_docker_dirs,docker-image)

#-#
#-# up:
#-#   runs docker compose up with .env.
up: .env
	docker compose --env-file=.env --env-file=../arxiv-keycloak/.env up -d

#-#
#-# down:
#-#   runs docker compose down
down:
	docker compose --env-file=.env --env-file=../arxiv-keycloak/.env down


#-#
#-# test:
#-#   runs test in all of subdirectories
test:
	$(call run_in_all_subdirs,test)

