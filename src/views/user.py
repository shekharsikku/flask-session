from flask import Blueprint, request, session, g, make_response
from marshmallow import ValidationError
from functools import wraps

from src.configs import db
from src.models.user import User
from src.utils import ApiResponse, Hashed, Helpers
from src.utils.schema import (register_user_schema, login_user_schema, user_data_schema, login_data_schema,
                              update_user_schema)


user = Blueprint("user", __name__, url_prefix="/api/user")


@user.before_request
def before_request():
    Helpers.global_session_user()


@user.after_request
def after_request(response):
    Helpers.global_session_user()
    print(f"Current session user: {g.user} & uid: {g.uid}")
    return response


# Api route for register user - "/api/users/register"
@user.route("/register", methods=["POST"])
def register_user():
    try:
        user_data = register_user_schema.load(request.get_json())

        if User.query.filter(User.email == user_data["email"]).first():
            return ApiResponse(409, "Email already exits!")

        hashed_password = Hashed.generate(user_data["password"])

        new_user = User(email=user_data["email"], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        created_user = user_data_schema.dump(new_user)

        return ApiResponse(201, "User registered successfully!", created_user)

    except ValidationError as e:
        return ApiResponse(400, "Validation errors occurred!", None, e.messages)

    except Exception as e:
        return ApiResponse(500, "An unexpected error occurred!", None, str(e))


# Api route for login user - "/api/users/login"
@user.route("/login", methods=["POST"])
def login_user():
    try:
        login_data = login_user_schema.load(request.get_json())
        
        email = login_data.get("email")
        username = login_data.get("username")
        password = login_data.get("password")

        if not any([username, email]):
            return ApiResponse(400, "Username or Email is required!")
        
        exists_user = None
        session_key = None

        fields = {"username": username, "email": email}

        for key, value in fields.items():
            if value:
                session_key = key
                exists_user = User.query.filter_by(**{key: value}).first()
                break

        if not exists_user:
            Helpers.clear_session_cookies()
            return ApiResponse(404, "User not found!")
        
        user_data = login_data_schema.dump(exists_user)
        is_verify = Hashed.verify(password, user_data["password"])

        if not is_verify:
            Helpers.clear_session_cookies()
            return ApiResponse(403, "Incorrect password!")

        session[session_key] = user_data[session_key]
        session["uid"] = user_data["id"]

        response_data = user_data_schema.dump(exists_user)
        return ApiResponse(200, "User login successfully!", response_data)
    
    except ValidationError as e:
        return ApiResponse(400, "Validation errors occurred!", None, e.messages)

    except Exception as e:
        return ApiResponse(500, "An unexpected error occurred!", None, str(e))


# Api route for logout user - "/api/users/logout"
@user.route("/logout", methods=["DELETE"])
def logout_user():
    session_value = Helpers.clear_session_cookies()
    response = make_response(session_value)
    response.set_cookie("session", "", expires=0)
    return ApiResponse(response.status_code, "User logout successfully!")


# Login required decorator function for access session user
def login_required(func):
    @wraps(func)
    def secure_function(*args, **kwargs):
        if any(key in session for key in ["username", "email"]):
            session_key = next((key for key in ["username", "email"] if key in session), None)
            session_uid = session.get("uid")

            if session_key and session_uid:
                session_user = User.query.filter_by(**{session_key: session[session_key], "id": session_uid}).first()
                
                if session_user:
                    return func(session_user, session_uid, *args, **kwargs)

            return func(*args, **kwargs)
        else:
            return ApiResponse(401, "Unauthorized user!")
    return secure_function


# Api route for check session user - "/api/user/user-information"
@user.route("/user-information", methods=["GET"])
@login_required
def get_session_user(session_user, session_uid, *args, **kwargs):
    if g.user and g.uid and session_user:
        response_data = user_data_schema.dump(session_user)
        return ApiResponse(200, "User information!", response_data)
    return ApiResponse(401, "Unauthorized user!")


# Api route for update user profile - "/api/user/update-profile"
@user.route("/update-profile", methods=["PUT", "PATCH"])
@login_required
def update_user(session_user, session_uid, *args, **kwargs):
    try:
        user_data = update_user_schema.load(request.get_json())

        username = user_data["username"]

        if username != session_user.username:
            if User.query.filter(username=username).first():
                return ApiResponse(409, "Username already exits!")

        is_empty = Helpers.has_empty_field(user_data)

        if not is_empty:
            user_data.update({"setup": True})

        update_result = User.update_user(id=session_uid, data=user_data)

        if update_result:
            response_data = user_data_schema.dump(update_result)
            return ApiResponse(200, "Profile updated successfully!", response_data)

        return ApiResponse(400, "Profile update not completed!")
    
    except ValidationError as e:
        return ApiResponse(400, "Validation errors occurred!", None, e.messages)

    except Exception as e:
        return ApiResponse(500, "An unexpected error occurred!", None, str(e))
