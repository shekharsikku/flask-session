import datetime
import functools
import logging
import os

from dotenv import load_dotenv
from flask import Flask, make_response, jsonify, request, session, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import InvalidRequestError, OperationalError, SQLAlchemyError
from werkzeug.exceptions import BadRequest, NotFound, MethodNotAllowed, HTTPException

from src.hashed import generate_hashed, check_hashed
from src.schema import user_schema, users_schema, login_user_schema


load_dotenv()
logging.basicConfig(level=logging.DEBUG)
server_mode = os.getenv("SERVER_MODE")


# Flask App, Database, CORS and Session Configuration
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("MYSQLDB_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False
app.config["SQLALCHEMY_ECHO"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGIN")}})
db = SQLAlchemy(app)


# Check if the database connection is successfully established or not
with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        print("Connected to Database Successfully!")
    except SQLAlchemyError:
        print(f"Database Connection failed!")


class Users(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    fullname = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, username, email, fullname, password):
        self.username = username
        self.email = email
        self.fullname = fullname
        self.password = password

    def __repr__(self):
        return "<User %r>" % self.username


# Api response function
def api_response(message, data, code):
    if data is not None:
        return make_response(jsonify({"message": message, "data": data}), code)
    return make_response(jsonify({"message": message}), code)


# Error response function
def error_response(error, code):
    return make_response(jsonify({"error": error}), code)


@app.before_request
def before_request():
    session_keys = ["username", "email"]
    g.user = next((session[key] for key in session_keys if key in session), None)
    print(f"Existed Session User : {g.user}")


@app.after_request
def after_request(response):
    print(f"Api Request Handled Successfully! {request.url}")
    return response


@app.route("/", methods=["GET"])
def greet():
    return api_response("Welcome to Flask!", None, 200)


# Api route for register user - http://127.0.0.1:8100/api/users/register
@app.route("/api/users/register", methods=["POST"])
def register_user():
    user_data = request.get_json()

    required_fields = ["username", "email", "fullname", "password"]
    missing_fields = [field for field in required_fields if field not in user_data]

    if missing_fields:
        input_string = f"{', '.join(missing_fields)}, Required!"
        words = input_string.split(', ')    # Split the string into a list of words
        capitalized_words = [word.capitalize() for word in words]   # Capitalize each word in the list
        result_string = ', '.join(capitalized_words)    # Join the capitalized words back into a string
        return error_response(result_string, 403)   # Returning error response for missing fields

    username = user_data["username"]
    email = user_data["email"]
    fullname = user_data["fullname"]
    password = generate_hashed(user_data["password"])

    # Check for existing user with given username and email
    existing_user = Users.query.filter((Users.username == username) | (Users.email == email)).first()

    if existing_user:
        if existing_user.username == username:
            return error_response("Username Already Registered", 409)
        else:
            return error_response("Email Already Registered", 409)

    # Creating and registering a new user
    new_user = Users(username, email, fullname, password)
    db.session.add(new_user)
    db.session.commit()

    response = user_schema.dump(new_user)
    return api_response("User Registered Successfully!", response, 201)


# Api route for login user - http://127.0.0.1:8100/api/users/login
@app.route("/api/users/login", methods=["POST"])
def login_user():
    user_data = request.get_json()

    if not user_data:
        return error_response("User Credentials Required!", 406)

    username = user_data.get("username")
    email = user_data.get("email")

    if not any([username, email]):
        return error_response("Username or Email Required!", 403)

    exists_user = None

    if username:
        exists_user = Users.query.filter_by(username=username).first()
    elif email:
        exists_user = Users.query.filter_by(email=email).first()

    if not exists_user:
        session.pop("username", None)
        session.pop("email", None)
        return error_response("User Not Found!", 404)

    if "password" not in user_data:
        return error_response("Password Required!", 403)

    password = user_data["password"]

    # Verifying if same user trying too login again
    if "username" in session and username == session["username"]:
        return api_response("User Already Logged In!", None, 302)

    elif "email" in session and email == session["email"]:
        return api_response("User Already Logged In!", None, 302)
    else:
        # Removing exist session for new user login
        session.pop("username", None)
        session.pop("email", None)
    
    # Validating user data with given user credentials
    if username:
        exists_user = Users.query.filter_by(username=username).first()
    elif email:
        exists_user = Users.query.filter_by(email=email).first()
    else:
        return error_response("Invalid Credentials!", 403)

    if not exists_user:
        return error_response("User Not Found!", 404)

    check_login_user = login_user_schema.dump(exists_user)
    verify_password = check_hashed(password, check_login_user["password"])
    print(f"Password: {password}, Status: {verify_password}")

    if verify_password:
        session_key = "username" if username else "email"
        session[session_key] = check_login_user[session_key]
        response = user_schema.dump(check_login_user)
        return api_response("User Login Successfully!", response, 202)
    return error_response("Incorrect Password!", 406)


# Api route for check session user - http://127.0.0.1:8100/api/users/session
@app.route("/api/users/session", methods=["GET"])
def get_session_user():
    if g.user:
        session_key = next((key for key in ["username", "email"] if key in session), None)

        if session_key:
            session_user = Users.query.filter_by(**{session_key: session[session_key]}).first()
            if session_user:
                response = user_schema.dump(session_user)
                return api_response("Session User Data!", response, 200)
            else:
                return error_response("Session User Not Found!", 404)
    return error_response("Unauthorized Session", 401)


# Api route for logout current session user - http://127.0.0.1:8100/api/users/logout
@app.route("/api/users/logout", methods=["DELETE"])
def logout_user():
    session_keys = ["username", "email"]
    session_key = next((key for key in session_keys if key in session), None)

    if not session_key:
        return error_response("Unauthorized Session", 401)

    session_value = session.pop(session_key, None)

    if session_value is not None:
        return api_response("User Logged Out Successfully!", None, 206)
    else:
        return error_response("Unauthorized Session", 401)


# Login required decorator function for access other user data by session user
def login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if any(key in session for key in ["username", "email"]):
            return func(*args, **kwargs)
        else:
            return error_response("Unauthorized User!", 401)
    return secure_function


# Api route for fetch all users - http://127.0.0.1:8100/api/users/fetch
@app.route("/api/users/fetch", methods=["GET"])
@login_required
def fetch_users():
    all_users = Users.query.all()
    
    if not all_users:
        return error_response("No Users Found!", 404)

    response = users_schema.dump(all_users)
    return api_response("Users Fetched Successfully!", response, 200)


# Api route for fetch user by uid - http://127.0.0.1:8100/api/users/fetch/<uid>
@app.route("/api/users/fetch/<uid>", methods=["GET"])
@login_required
def fetch_user(uid):
    existed_user = db.session.get(Users, uid)

    if not existed_user:
        return error_response("User Not Found!", 404)

    response = user_schema.dump(existed_user)
    return api_response("User Fetched Successfully!", response, 200)


# Api route for fetch user by query parameter - http://127.0.0.1:8100/api/users/fetch/user?query=parameter
@app.route("/api/users/fetch/user", methods=["GET"])
@login_required
def fetch_user_by():
    user_data = request.args.to_dict()
    print("Search User :", user_data)

    if not user_data:
        return error_response("Please, Query User Data!", 406)

    existed_user = Users.query.filter_by(**user_data).first()

    if not existed_user:
        return error_response("User Not Found!", 404)

    response = user_schema.dump(existed_user)
    return api_response("User Fetched Successfully!", response, 200)


# Session user verification for modification and deletion for user data 
def verify_session(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        existed_user = Users.query.filter_by(**kwargs).first()

        if not existed_user:
            return error_response("User Not Found!", 404)

        verify_user = Users.query.filter_by(**kwargs).first()
        response = user_schema.dump(verify_user)

        session_key = next((key for key in ["username", "email"] if key in session), None)

        if session_key and response[session_key] == session[session_key]:
            return func(existed_user, *args, **kwargs)
        else:
            return error_response("Invalid or Unauthorized Session User!", 403)
    return secure_function


# Api route for update user data by uid - http://127.0.0.1:8100/api/users/update/<uid>
@app.route("/api/users/update/<uid>", methods=["PUT"])
@verify_session
def update_user(existed_user, **kwargs):
    user_data = request.get_json()

    if user_data and "username" or "email" in user_data:
        # check for existing username
        if "username" in user_data and Users.query.filter_by(username=user_data["username"]).first():
            return error_response("Username Already Exists!", 409)

        # check for existing email
        if "email" in user_data and Users.query.filter_by(email=user_data["email"]).first():
            return error_response("Email Already Exists!", 409)
    
    if not user_data or not any(key in user_data for key in ["username", "email", "fullname", "password"]):
        return error_response("User Data Required!", 403)

    username = user_data.get("username", None)
    email = user_data.get("email", None)
    fullname = user_data.get("fullname", None)
    password = user_data.get("password", None)
    
    if existed_user and user_data:
        existed_user.username = username if username is not None else existed_user.username
        existed_user.email = email if email is not None else existed_user.email
        existed_user.fullname = fullname if fullname is not None else existed_user.fullname
        existed_user.password = generate_hashed(password) if password is not None else existed_user.password

        db.session.commit()
        updated_user = Users.query.filter_by(**kwargs).first()
        response = user_schema.dump(updated_user)
        session.pop("username", None)
        session.pop("email", None)
        return api_response("User Updated Successfully!", response, 202)
    else:
        return api_response("User Data Not Modified!", None, 304)


# Api route for delete user by uid - http://127.0.0.1:8100/api/users/delete/<uid>
@app.route("/api/users/delete/<uid>", methods=["DELETE"])
@verify_session
def delete_user(existed_user):
    db.session.delete(existed_user)
    db.session.commit()
    session.pop("username", None)
    session.pop("email", None)
    return api_response("User Deleted Successfully!", None, 200)


# ! Basic Error/Exception handling!

@app.errorhandler(BadRequest)
def handle_bad_request_error(error):
    return error_response(f"Bad Request: {error.description}", error.code)


@app.errorhandler(NotFound)
def handle_not_found_error(error):
    return error_response(f"Not Found: {error.description} {request.url}", error.code)


@app.errorhandler(MethodNotAllowed)
def handle_method_not_allowed_error(error):
    return error_response(f"Method Not Allowed: {error.description}", error.code)


@app.errorhandler(HTTPException)
def handle_http_exception(error):
    return error_response(f"HTTP Exception: {error.description}", error.code)


@app.errorhandler(Exception)
def handle_generic_exception(error):
    return error_response(f"Some Error Occurred: {error}", 400)

# ! SQLAlchemy Error/Exception handling!

@app.errorhandler(InvalidRequestError)
def invalid_request_error(error):
    return error_response(f"Invalid Request: The database query is malformed! {error}", 400)


@app.errorhandler(OperationalError)
def operational_error(error):
    return error_response(f"Operational Error: An issue occurred with the database operation! {error}", 500)


@app.errorhandler(SQLAlchemyError)
def sqlalchemy_error(error):
    return error_response(f"SQLAlchemy Error: An unexpected issue occurred while processing your request! {error}", 500)
