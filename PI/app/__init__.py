from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager # type: ignore
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from app import routes
    app.register_blueprint(routes.bp)

    return app