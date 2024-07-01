from typing import Dict, Any
from dotenv import load_dotenv
from os import getenv


class EnvConfig:
    def __init__(self):
        load_dotenv()

        required_keys = ["DATABASE_URI", "REDIS_URI", "SECRET_KEY"]

        self.__variables: Dict[str, Any] = {
            "DATABASE_URI": getenv("DATABASE_URI"),
            "REDIS_URI": getenv("REDIS_URI"),
            "SECRET_KEY": getenv("SECRET_KEY"),
            "CORS_ORIGIN": getenv("CORS_ORIGIN", "*"),
            "SERVER_MODE": getenv("SERVER_MODE", "development"),
            "PORT": int(getenv("PORT", "4000"))
        }

        missing = [key for key in required_keys if not self.__variables[key]]

        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    def __contains__(self, key: str) -> bool:
        return key in self.__variables
    
    def __getitem__(self, key) -> (Any | None):
        return self.__variables.get(key)


class CorsConfig:
    def __init__(self):
        self.__variables: Dict[str, Any] = {
            "ALLOWED_ORIGIN": envs["CORS_ORIGIN"].split(", "),
            "WITH_CREDENTIAL": True
        }
    
    def __contains__(self, key: str) -> bool:
        return key in self.__variables
    
    def __getitem__(self, key) -> (Any | None):
        return self.__variables.get(key)


envs = EnvConfig()
cors = CorsConfig()
