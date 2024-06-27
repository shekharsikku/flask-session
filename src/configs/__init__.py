from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS
from flask import Flask
import pymysql
import sys

from src.utils import envs, cors


pymysql.install_as_MySQLdb()
db = SQLAlchemy()


def init_flask_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = envs["DATABASE_URI"]
    app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SECRET_KEY"] = envs["SECRET_KEY"]
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    
    db.init_app(app)

    CORS(app, resources={r"/api/*": {
        "origins": cors["ALLOWED_ORIGIN"],
        "supports_credentials": cors["WITH_CREDENTIAL"]
    }})

    from src.views.user import user as user_blueprint

    app.register_blueprint(user_blueprint)

    with app.app_context():
        from src.models.user import User
        
        try:
            with app.app_context():
                db.create_all()
        except SQLAlchemyError as e:
            print(f"Database connection error! \n{e}")
            sys.exit(1)
        else:
            db.session.execute(text("SELECT 1"))
            print("Database connection success!")
            return app
