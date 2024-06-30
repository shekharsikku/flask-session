from flask import Blueprint, request, session, g, make_response
from bcrypt import hashpw, gensalt, checkpw
from marshmallow import ValidationError
from functools import wraps
from logging import getLogger

from src.configs import db, rc
from src.models.user import User
from src.utils.response import ApiResponse
from src.utils.uploads import upload_image_on_cloudinary, delete_image_from_cloudinary, extract_uuid_from_url
from src.utils.helpers import (has_empty_field, global_session_user, clear_session_cookies, store_to_redis, 
                               retrieve_from_redis)
from src.utils.schema import (register_user_schema, login_user_schema, user_data_schema, login_data_schema,
                              update_user_schema, change_password_schema)


user = Blueprint("user", __name__, url_prefix="/api/user")


def generate_hash(plain_text: str) -> str:
    return hashpw(plain_text.encode("utf-8"), gensalt()).decode()


def verify_hash(plain_text: str, hashed_text: str) -> bool:
    return checkpw(plain_text.encode("utf-8"), hashed_text.encode("utf-8"))


@user.before_request
def before_request():
    global_session_user()


@user.after_request
def after_request(response):
    global_session_user()
    logger = getLogger("session")
    logger.info(f" * Session is active for {g.user}@{g.uid}")
    return response


# Api route for register user - "/api/users/register"
@user.route("/register", methods=["POST"])
def register_user():
    try:
        user_data = register_user_schema.load(request.get_json())

        if User.query.filter(User.email == user_data["email"]).first():
            return ApiResponse(409, "Email already exits!")

        hashed_password = generate_hash(user_data["password"])

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
            clear_session_cookies()
            return ApiResponse(404, "User not found!")
        
        user_data = login_data_schema.dump(exists_user)
        is_verified = verify_hash(password, user_data["password"])

        if not is_verified:
            clear_session_cookies()
            return ApiResponse(403, "Incorrect password!")

        session[session_key] = user_data[session_key]
        session["uid"] = user_data["id"]

        response_data = user_data_schema.dump(exists_user)
        store_to_redis("user", response_data["id"], response_data)
        return ApiResponse(200, "User login successfully!", response_data)
    
    except ValidationError as e:
        return ApiResponse(400, "Validation errors occurred!", None, e.messages)

    except Exception as e:
        return ApiResponse(500, "An unexpected error occurred!", None, str(e))


# Api route for logout user - "/api/users/logout"
@user.route("/logout", methods=["GET", "DELETE"])
def logout_user():
    session_value = clear_session_cookies()
    rc.delete(f"user:{session_value['uid']}")
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
                cache_data = retrieve_from_redis("user", session_uid)
                
                if cache_data is not None:
                    return func(cache_data, session_uid, *args, **kwargs)

                session_user = User.query.filter_by(**{session_key: session[session_key], "id": session_uid}).first()

                if session_user:
                    query_data = user_data_schema.dump(session_user)
                    store_to_redis("user", session_uid, query_data)
                    return func(query_data, session_uid, *args, **kwargs)

            return func(*args, **kwargs)
        else:
            return ApiResponse(401, "Unauthorized user!")
    return secure_function


# Api route for check session user - "/api/user/user-information"
@user.route("/user-information", methods=["GET"])
@login_required
def get_session_user(session_user, session_uid, *args, **kwargs):
    if g.user and g.uid and session_user:
        return ApiResponse(200, "User information!", session_user)
    return ApiResponse(401, "Unauthorized user!")


# Api route for update user profile - "/api/user/update-profile"
@user.route("/update-profile", methods=["PUT", "PATCH"])
@login_required
def update_user(session_user, session_uid, *args, **kwargs):
    try:
        user_data = update_user_schema.load(request.get_json())

        username = user_data["username"]

        if username != session_user["username"]:
            if User.query.filter_by(username=username).first():
                return ApiResponse(409, "Username already exits!")

        is_empty = has_empty_field(user_data)

        if not is_empty:
            user_data.update({"setup": True})

        update_result = User.update_user(id=session_uid, data=user_data)

        if update_result:
            response_data = user_data_schema.dump(update_result)
            store_to_redis("user", session_uid, response_data)
            return ApiResponse(200, "Profile updated successfully!", response_data)

        return ApiResponse(400, "Profile update not completed!")
    
    except ValidationError as e:
        return ApiResponse(400, "Validation errors occurred!", None, e.messages)

    except Exception as e:
        return ApiResponse(500, "An unexpected error occurred!", None, str(e))


# Api route for change user password - "/api/user/change-password"
@user.route("/change-password", methods=["PUT", "PATCH"])
@login_required
def change_password(session_user, session_uid, *args, **kwargs):
    try:
        user_data = change_password_schema.load(request.get_json())
        
        old_password = user_data.get("old_password")
        new_password = user_data.get("new_password")

        if old_password == new_password:
            return ApiResponse(400, "Please, choose a different password!")

        req_user = User.query.filter_by(id=session_uid).first()
        req_data = login_data_schema.dump(req_user)

        is_verified = verify_hash(old_password, req_data["password"])

        if not is_verified:
            return ApiResponse(403, "Incorrect old password!")
        
        hashed_password = generate_hash(new_password)

        update_result = User.update_user(id=session_uid, data={"password": hashed_password})

        if update_result:
            response_data = user_data_schema.dump(update_result)
            store_to_redis("user", session_uid, response_data)
            return ApiResponse(200, "Password changed successfully!", response_data)

        return ApiResponse(400, "Password cannot changed!")

    except ValidationError as e:
        return ApiResponse(400, "Validation errors occurred!", None, e.messages)

    except Exception as e:
        return ApiResponse(500, "An unexpected error occurred!", None, str(e))
    

@user.route("/update-image", methods=["PUT", "PATCH"])
@login_required
def update_image(session_user, session_uid, *args, **kwargs):
    try:
        if "image" not in request.files:
            return ApiResponse(400, "Image file is required!")

        image_file = request.files["image"]

        if image_file.filename == "":
            return ApiResponse(400, "No any selected file!")

        if session_user["image"] and session_user["image"] != "":
            public_uuid = extract_uuid_from_url(session_user["image"])
            delete_image_from_cloudinary(public_uuid)

        upload_result = upload_image_on_cloudinary(image_file)

        secure_url = upload_result.get("secure_url")
        public_id = upload_result.get("public_id")

        if not secure_url or not public_id:
            return ApiResponse(500, "Image file upload error!")
        
        update_result = User.update_user(id=session_uid, data={"image": secure_url})

        if update_result:
            response_data = user_data_schema.dump(update_result)
            store_to_redis("user", session_uid, response_data)
            return ApiResponse(200, "Image uploaded successfully!", response_data)

        return ApiResponse(400, "Failed to update image!")

    except Exception as e:
        return ApiResponse(500, "An unexpected error occurred!", None, str(e))
    

@user.route("/delete-image", methods=["DELETE"])
@login_required
def delete_image(session_user, session_uid, *args, **kwargs):
    try:
        if session_user["image"] and session_user["image"] != "":
            public_uuid = extract_uuid_from_url(session_user["image"])
            result = delete_image_from_cloudinary(public_uuid)

            if result:
                update_result = User.update_user(id=session_uid, data={"image": None})
                if update_result:
                    response_data = user_data_schema.dump(update_result)
                    store_to_redis("user", session_uid, response_data)
                    return ApiResponse(200, "Image deleted successfully!", response_data)
                
            return ApiResponse(400, "Failed to delete image!")
        return ApiResponse(400, "Image file not available!")

    except Exception as e:
        return ApiResponse(500, "An unexpected error occurred!", None, str(e))
    