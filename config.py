from datetime import timedelta


class Config:
    DEBUG = True
    SECRET_KEY = "oes-development-secret-key"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)

    MYSQL_HOST = "localhost"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWORD = ""
    MYSQL_DATABASE = "oes_db"

    PASS_PERCENTAGE = 40
