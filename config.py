import os
import sys
from datetime import timedelta
from urllib.parse import unquote, urlparse

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _database_url_parts():
    url = os.environ.get("DATABASE_URL") or os.environ.get("MYSQL_URL")
    if not url:
        return {}

    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "").lstrip("/"),
    }


_url_parts = _database_url_parts()


def _secret_key():
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    hosted = (
        os.environ.get("FLASK_ENV") == "production"
        or os.environ.get("RENDER")
        or os.environ.get("PYTHONANYWHERE_DOMAIN")
    )
    if hosted:
        sys.exit("SECRET_KEY must be set when running on a hosting service.")
    return "evalpro-development-secret-key"


class Config:
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    SECRET_KEY = _secret_key()
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    MYSQL_HOST = _url_parts.get("host") or os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = _url_parts.get("port") or int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = _url_parts.get("user") or os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = _url_parts.get("password") or os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = _url_parts.get("database") or os.environ.get("MYSQL_DATABASE", "oes_db")

    MYSQL_SSL = os.environ.get("MYSQL_SSL", "0") == "1"
    MYSQL_SSL_CA = os.environ.get("MYSQL_SSL_CA", "")
    MYSQL_POOL_SIZE = int(os.environ.get("MYSQL_POOL_SIZE", "3"))

    PASS_PERCENTAGE = int(os.environ.get("PASS_PERCENTAGE", "40"))
