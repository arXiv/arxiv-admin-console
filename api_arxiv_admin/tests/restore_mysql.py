import time
import pymysql
import sys
import os
import argparse

def wait_for_mysql(host, port, user, password, database, max_retries, retry_delay):
    for _ in range(max_retries):
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                connect_timeout=1
            )
            conn.close()
            return True
        except pymysql.MySQLError as _e:
            time.sleep(retry_delay)
    return False


def execute_sql_file(sql_file, host, port, user, password, database):
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
    except pymysql.MySQLError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    cursor = conn.cursor()

    try:
        with open(sql_file, "r") as f:
            sql_commands = f.read()
    except Exception as e:
        print(e, file=sys.stderr)
        exit(1)

    try:
        for command in sql_commands.split(";"):
            if command.strip():
                cursor.execute(command)
        conn.commit()
    except pymysql.MySQLError as e:
        print(f"Error executing SQL file: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Wait for MySQL and execute an SQL file.")
    parser.add_argument("sql_file", help="Path to the SQL file to execute")
    parser.add_argument("--host", default=os.getenv("MYSQL_HOST", "127.0.0.1"), help="MySQL host")
    parser.add_argument("--port", type=int, default=int(os.getenv("MYSQL_TCP_PORT", 3306)), help="MySQL port")
    parser.add_argument("--user", default=os.getenv("MYSQL_USER", "root"), help="MySQL user")
    parser.add_argument("--password", default=os.getenv("MYSQL_PASSWORD", "root_password"), help="MySQL password")
    parser.add_argument("--database", default=os.getenv("MYSQL_DATABASE", "arXiv"), help="arXiv database")
    parser.add_argument("--max-retries", type=int, default=10, help="Maximum number of connection retries")
    parser.add_argument("--retry-delay", type=int, default=2, help="Seconds to wait between retries")

    args = parser.parse_args()

    if wait_for_mysql(args.host, args.port, args.user, args.password, args.database, args.max_retries,
                      args.retry_delay):
        if not args.sql_file:
            exit(0)

        if not os.path.isfile(args.sql_file):
            print(f"SQL file not found: {args.sql_file}", file=sys.stderr)
            sys.exit(1)
        execute_sql_file(args.sql_file, args.host, args.port, args.user, args.password, args.database)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
