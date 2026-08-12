import os
import re
import sys

import mysql.connector

import db
from config import Config

SQL_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
SQL_FILES = ["schema.sql", "views.sql", "procedures.sql", "seed.sql"]

SKIP_PATTERN = re.compile(r"^\s*(USE\s+|CREATE\s+DATABASE\s+)", re.IGNORECASE)
DELIMITER_PATTERN = re.compile(r"^\s*DELIMITER\s+(\S+)\s*$", re.IGNORECASE)


def split_statements(sql_text):
    statements = []
    delimiter = ";"
    buffer = ""

    for line in sql_text.splitlines():
        delimiter_change = DELIMITER_PATTERN.match(line)
        if delimiter_change:
            delimiter = delimiter_change.group(1)
            continue

        if not buffer and SKIP_PATTERN.match(line):
            continue

        buffer += line + "\n"

        while delimiter in buffer:
            statement, _, remainder = buffer.partition(delimiter)
            if statement.strip():
                statements.append(statement.strip())
            buffer = remainder

    if buffer.strip():
        statements.append(buffer.strip())

    return statements


def create_database_if_possible():
    try:
        connection = mysql.connector.connect(**db.connection_settings(include_database=False))
    except mysql.connector.Error as error:
        print("Could not connect to the MySQL server: %s" % error)
        sys.exit(1)

    cursor = connection.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS `%s`" % Config.MYSQL_DATABASE)
        print("Database ready: %s" % Config.MYSQL_DATABASE)
    except mysql.connector.Error as error:
        print(
            "Could not create the database (%s). It probably already exists or your "
            "hosting provider created it for you. Continuing." % error
        )
    finally:
        cursor.close()
        connection.close()


def run_sql_file(connection, file_name):
    path = os.path.join(SQL_DIRECTORY, file_name)
    with open(path, "r", encoding="utf-8") as sql_file:
        statements = split_statements(sql_file.read())

    cursor = connection.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
            while cursor.nextset():
                pass
        connection.commit()
        print("Applied %s (%d statements)" % (file_name, len(statements)))
    finally:
        cursor.close()


def main():
    create_database_if_possible()

    connection = mysql.connector.connect(**db.connection_settings())
    try:
        for file_name in SQL_FILES:
            run_sql_file(connection, file_name)
    finally:
        connection.close()

    print("")
    print("Database setup finished for '%s' on %s." % (Config.MYSQL_DATABASE, Config.MYSQL_HOST))
    print("Default admin login: admin / admin123 - change it immediately.")


if __name__ == "__main__":
    main()
