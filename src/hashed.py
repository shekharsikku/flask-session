from bcrypt import hashpw, gensalt, checkpw


def generate_hashed(plain_password):
    return hashpw(plain_password.encode("utf-8"), gensalt()).decode("utf-8")


def check_hashed(plain_password, hashed_password):
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
