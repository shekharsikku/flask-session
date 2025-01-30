from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from flask_socketio import SocketIO, emit, send
from flask import redirect, request
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


@socketio.on('message')
def handle_message(msg):
    print('Received message:', msg)
    send('Response from Flask Server: ' + msg)  # Send a message back to client


@socketio.on("connect")
def handle_connect():
    user_id = request.args.get('userId')  # Flask's request object gives access to the query params

    socket_id = request.sid

    print(f"User connected with userId: {user_id}", socket_id)

    emit("response_event", {"message": f"Hello user {user_id}!"})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


# Handling a custom event from client


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
