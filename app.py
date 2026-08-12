from flask import Flask, render_template

from blueprints.admin import admin_bp
from blueprints.auth import auth_bp
from blueprints.exam import exam_bp
from blueprints.result import result_bp
from blueprints.student import student_bp
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(exam_bp)
    app.register_blueprint(result_bp)
    return app


app = create_app()


@app.route("/")
def home():
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=Config.DEBUG)
