from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import Config


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all
        
    from app import models  # noqa: F401
    from app.routes import main

    app.register_blueprint(main)

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Initialized the database.")

    return app
