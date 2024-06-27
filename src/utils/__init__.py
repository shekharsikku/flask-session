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
            "PORT": int(getenv("PORT", "4000"))
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
