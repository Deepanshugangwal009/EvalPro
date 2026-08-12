import mysql.connector
from mysql.connector import pooling

from config import Config

_pool = None


def connection_settings(include_database=True):
    settings = {
        "host": Config.MYSQL_HOST,
        "port": Config.MYSQL_PORT,
        "user": Config.MYSQL_USER,
        "password": Config.MYSQL_PASSWORD,
        "connection_timeout": 15,
    }

    if include_database:
        settings["database"] = Config.MYSQL_DATABASE

    if Config.MYSQL_SSL:
        if Config.MYSQL_SSL_CA:
            settings["ssl_ca"] = Config.MYSQL_SSL_CA
        else:
            settings["ssl_verify_cert"] = False
    else:
        settings["ssl_disabled"] = True

    return settings


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="oes_pool",
            pool_size=Config.MYSQL_POOL_SIZE,
            pool_reset_session=True,
            **connection_settings()
        )
    return _pool


def get_connection():
    try:
        return _get_pool().get_connection()
    except mysql.connector.Error:
        return mysql.connector.connect(**connection_settings())


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


def call_procedure(procedure_name, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.callproc(procedure_name, params or ())
        rows = []
        for stored_result in cursor.stored_results():
            rows = stored_result.fetchall()
        connection.commit()
        return rows
    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=None):
    return run_query(query, params, fetch="one")


def fetch_all(query, params=None):
    return run_query(query, params, fetch="all")


def execute(query, params=None):
    return run_query(query, params)
