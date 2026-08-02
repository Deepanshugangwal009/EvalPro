import mysql.connector

from config import Config


def get_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
    )


def run_query(query, params=None, fetch=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch == "one":
            return cursor.fetchone()
        if fetch == "all":
            return cursor.fetchall()
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=None):
    return run_query(query, params, fetch="one")


def fetch_all(query, params=None):
    return run_query(query, params, fetch="all")


def execute(query, params=None):
    return run_query(query, params)
