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


# helper function for socket connections

def add_user_sockets(user_id: str, socket_id: str):
    rc.sadd(f"sockets:{user_id}", socket_id)
    rc.set(f"sid:{socket_id}", user_id)


def get_user_sockets(user_id: str):
    socket_ids = rc.smembers(f"sockets:{user_id}")
    return [sid.decode() for sid in socket_ids]


def get_connected_users():
    user_ids = []

    for key in rc.scan_iter("sockets:*"):
        key = key.decode()
        if key.startswith("sockets:"):
            user_id = key[len("sockets:"):]
            if rc.scard(key) > 0:
                user_ids.append(user_id)

    return user_ids


def get_connected_sockets():
    all_socket_ids = []

    for key in rc.scan_iter("sockets:*"):
        socket_ids = rc.smembers(key)
        decoded_sockets = [sid.decode() for sid in socket_ids]
        all_socket_ids.extend(decoded_sockets)

    return all_socket_ids


def get_connections_details():
    user_socket_map = {}

    for raw_key in rc.scan_iter("sockets:*"):
        key = raw_key.decode() 
        user_id = key[len("sockets:"):]
        socket_ids = rc.smembers(raw_key)
        decoded_sockets = [sid.decode() for sid in socket_ids]
        user_socket_map[user_id] = decoded_sockets

    return user_socket_map


def remove_socket_by_sid(socket_id: str):
    user_id = rc.get(f"sid:{socket_id}")
    if not user_id:
        return None

    if isinstance(user_id, bytes):
        user_id = user_id.decode()

    user_key = f"sockets:{user_id}"

    rc.srem(user_key, socket_id)

    rc.delete(f"sid:{socket_id}")

    if rc.scard(user_key) == 0:
        rc.delete(user_key)

    return user_id
