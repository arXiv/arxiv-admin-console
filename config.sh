#!/bin/sh
. ../arxiv-keycloak/.env

cp ../arxiv-keycloak/.env ./.env

echo CLASSIC_COOKIE_NAME=tapir_session >> .env
echo SESSION_DURATION=$CLASSIC_SESSION_DURATION >> .env
