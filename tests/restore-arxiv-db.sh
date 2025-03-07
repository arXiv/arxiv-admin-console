#!/bin/sh

SQL_FILE=$1
shift

MAX_RETRIES=3
RETRY_DELAY=5
COUNTER=0

# Function to check if MySQL is ready
wait_for_mysql() {
  echo "Waiting for MySQL to be ready..."
  until mysqladmin ping -h"$MYSQL_HOST" -P"$MYSQL_TCP_PORT" --silent; do
    echo "MySQL is unavailable - sleeping"
    sleep $RETRY_DELAY
  done
  echo "MySQL is up - executing SQL file"
}

wait_for_mysql

while [ $COUNTER -lt $MAX_RETRIES ]; do
  echo "Attempting to load SQL file: $SQL_FILE"
  (zcat "$SQL_FILE" | mysql -h "$MYSQL_HOST" -P "$MYSQL_TCP_PORT" -u root -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE") && break
  echo "Failed to load SQL file, retrying in $RETRY_DELAY seconds..."
  COUNTER=$((COUNTER + 1))
  sleep $RETRY_DELAY
done

if [ $COUNTER -eq $MAX_RETRIES ]; then
  echo "Failed to load SQL file after $MAX_RETRIES attempts."
  exit 1
else
  echo "SQL file loaded successfully."
fi
