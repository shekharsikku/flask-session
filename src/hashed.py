import bcrypt


def generate_hashed(plain_password):
    hashed_password = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return hashed_password


def check_hashed(plain_password, hashed_password):
    check_password = bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    return check_password
