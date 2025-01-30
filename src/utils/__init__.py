from flask import make_response, jsonify, session, g
from bcrypt import hashpw, gensalt, checkpw
from typing import Dict, Any
from dotenv import load_dotenv
from os import getenv


class EnvConfig:
    load_dotenv()

    def __init__(self):
        self.__variables = {
            "DATABASE_URI": getenv("DATABASE_URI"),
            "SECRET_KEY": getenv("SECRET_KEY"),
            "CORS_ORIGIN": getenv("CORS_ORIGIN", "*"),
            "SERVER_MODE": getenv("SERVER_MODE", "development"),
        }

    def environments(self) -> Dict[str, Any]:
        return self.__variables


class CorsConfig:
    def __init__(self):
        self.__variables = {
            "ALLOWED_ORIGIN": envs["CORS_ORIGIN"].split(", "),
            "WITH_CREDENTIAL": True
        }

    def configs(self) -> Dict[str, Any]:
        return self.__variables
    

envs = EnvConfig().environments()
cors = CorsConfig().configs()


class Hashed:
    def __init__(self):
        pass

    @staticmethod
    def generate(plain_text: str) -> str:
        return hashpw(plain_text.encode("utf-8"), gensalt()).decode()

    @staticmethod
    def verify(plain_text: str, hashed_text: str) -> bool:
        return checkpw(plain_text.encode("utf-8"), hashed_text.encode("utf-8"))


class ApiResponse:
    def __init__(self, code: int, message: str, data: any = None, error: any = None):
        self.code = code
        self.message = message
        self.data = data
        self.error = error

    def api_response(self):
        success = True if self.code < 400 else False
        response = {"message": self.message, "success": success}

        if self.data is not None:
            response["data"] = self.data

        if self.error is not None:
            response["error"] = self.error

        return response

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance.__init__(*args, **kwargs)
        return make_response(jsonify(instance.api_response()), instance.code)


class Helpers:
    def __init__(self):
        pass

    @staticmethod
    def has_empty_field(fields: dict) -> bool:
        return any(value in ("", None) for value in fields.values())

    @staticmethod
    def global_session_user():
        session_key = next((key for key in ["username", "email"] if key in session), None)
        g.user = session.get(session_key, None)
        g.uid = session.get("uid", None)
    
    @staticmethod
    def clear_session_cookies() -> object:
        session_key = next((key for key in ["username", "email"] if key in session), None)
        session_user = session.pop(session_key, None)
        session_uid = session.pop("uid", None)
        session.clear()
        return {"user": session_user, "uid": session_uid}
