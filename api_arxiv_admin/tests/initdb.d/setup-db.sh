#!/bin/sh
INIT_DB_DIR=$(dirname "$(dirname "$(realpath "$0")")")
cd /var/lib && tar czf "${INIT_DB_DIR}/mysql_test_data.tgz" mysql
