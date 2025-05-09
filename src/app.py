from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from flask_socketio import SocketIO, emit, send
from flask import redirect, request
from typing import Dict, Any
import eventlet

from src.configs import init_app
from src.utils import cors, ApiResponse


app = init_app()
socketio = SocketIO(
    app=app,
    cors_allowed_origins=cors["ALLOWED_ORIGIN"],
    allow_credentials=cors["WITH_CREDENTIAL"],
    async_mode="eventlet"
)


# Handling a custom event for socket.io client

user_sockets: Dict[str, Any] = {}


@socketio.on("connect")
def handle_connect():
    user_id = request.args.get("uid")

    if user_id:
        user_sockets[user_id] = request.sid
        print(f"User connected of uid {user_id} with sid {request.sid}")
        
        online_users = {user_id: socket_id for user_id, socket_id in user_sockets.items()}
        emit("users:online", online_users, broadcast=True)


@socketio.on("disconnect")
def handle_disconnect():
    user_id = next((key for key, value in user_sockets.items() if value == request.sid), None)

    if user_id:
        del user_sockets[user_id]
        print(f"User disconnected of uid {user_id} disconnected")

        online_users = {user_id: socket_id for user_id, socket_id in user_sockets.items()}
        emit("users:online", online_users, broadcast=True)


@socketio.on('message')
def handle_message(msg):
    print('Received message:', msg)
    send('Response from Flask Server: ' + msg)  # Send a message back to client


# Handle root route and basic error/exception


@app.route("/", methods=["GET"])
def greet():
    return ApiResponse(200, "Welcome to World of Flask!")


# @app.errorhandler(404)
# @app.route("/<path:path>")
# def not_found(path):
#     print(f"Redirecting undefined path '{path}' to root route!")
#     return redirect("/")


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    return ApiResponse(error.code, f"{error.description}")


@app.errorhandler(Exception)
def handle_generic_exception(error):
    return ApiResponse(400, f"Error: {error}!")


@app.errorhandler(SQLAlchemyError)
def sqlalchemy_error(error):
    return ApiResponse(500, f"Error: {error}!")
