from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from flask_socketio import SocketIO, emit, send
from flask import redirect, request
from typing import Dict, Any
import eventlet

from src.utils.response import ApiResponse
from src.configs import init_flask_app
from src.utils import cors


app = init_flask_app()
socketio = SocketIO(
    app=app,
    cors_allowed_origins=cors["ALLOWED_ORIGIN"],
    allow_credentials=cors["WITH_CREDENTIAL"],
    async_mode="eventlet"
)

# Handle root route and basic error/exception


@app.route("/", methods=["GET"])
def greet():
    return ApiResponse(200, "Welcome to World of Flask!")


@app.errorhandler(404)
@app.route("/<path:path>")
def not_found(path):
    print(f"Redirecting undefined path '{path}' to root route!")
    return redirect("/")


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    return ApiResponse(error.code, f"{error.description}")


@app.errorhandler(Exception)
def handle_generic_exception(error):
    return ApiResponse(400, f"Error: {error}!")


@app.errorhandler(SQLAlchemyError)
def sqlalchemy_error(error):
    return ApiResponse(500, f"Error: {error}!")
