from datetime import datetime, timezone
from uuid import uuid4

from src.configs import db 


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(30), nullable=True)
    email = db.Column(db.String(30), nullable=False, unique=True)
    username = db.Column(db.String(15), nullable=True, unique=True, index=True)
    password = db.Column(db.String(150), nullable=False)
    gender = db.Column(db.Enum("Male", "Female", "Other", name="gender"), nullable=True)
    image = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.String(50), nullable=True)
    setup = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                           onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def __repr__(self):
        return f"<User id: {self.id}>"

    @staticmethod
    def update_user(id: str, data: dict):
        user = User.query.get(id)

        if not user:
            return None

        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        db.session.commit()
        return user
    