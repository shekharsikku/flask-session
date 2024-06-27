from flask import session, g


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
