from flask import session, g
from redis import RedisError
from typing import Any, Optional
import json

from src.configs import rc


def has_empty_field(fields: dict) -> bool:
    return any(value in ("", None) for value in fields.values())


def global_session_user():
    session_key = next((key for key in ["username", "email"] if key in session), None)
    g.user = session.get(session_key, None)
    g.uid = session.get("uid", None)


def clear_session_cookies() -> object:
    session_key = next((key for key in ["username", "email"] if key in session), None)
    session_user = session.pop(session_key, None)
    session_uid = session.pop("uid", None)
    session.clear()
    return {"user": session_user, "uid": session_uid}


def store_to_redis(type: str, key: str, data: Any) -> bool:
    store_key = f"{type}:{key}"
    try:
        store_data = json.dumps(data)
        return rc.set(store_key, store_data, 3600)
    except (RedisError, TypeError, ValueError) as e:
        print(f"Failed to store data in Redis: {e}")
        return False


def retrieve_from_redis(type: str, key: str) -> Optional[Any]:
    store_key = f"{type}:{key}"
    try:
        store_value = rc.get(store_key)
        if store_value:
            return json.loads(store_value.decode("utf-8"))
    except (RedisError, json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Failed to retrieve data from Redis: {e}")
    return None
