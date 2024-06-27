from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from src.models.user import User


class RegisterUserSchema(Schema):
    email = fields.Str(required=True, validate=validate.Email())
    password = fields.Str(required=True, validate=validate.Length(min=6))


class LoginUserSchema(Schema):
    email = fields.Email(allow_none=True)
    username = fields.Str(allow_none=True)
    password = fields.Str(required=True)

    @validates_schema
    def validate_email_or_username(self, data, **kwargs):
        if not data.get("email") and not data.get("username"):
            raise ValidationError("Username or Email is required!", field_names=["email", "username"])


class UpdateUserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=30))
    username = fields.Str(required=True, validate=[
            validate.Length(min=3, max=15),
            validate.Regexp(r'^(?![_-])[a-z0-9_-]{3,15}(?<![_-])$', 
                            error="Only small letters, numbers, hyphen and underscores is allow with no space!")
        ])
    gender = fields.Str(required=True, validate=validate.OneOf(["Male", "Female", "Other"], 
                                                               error="Gender must be 'Male', 'Female', or 'Other'!"))
    bio = fields.Str(allow_none=True)


register_user_schema = RegisterUserSchema()
login_user_schema = LoginUserSchema()
update_user_schema = UpdateUserSchema()


class UserDataSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True

    def __init__(self, exclude=True, *args, **kwargs):
        kwargs.setdefault("exclude", [])
        
        if exclude and "password" not in kwargs["exclude"]:
            kwargs["exclude"].append("password")

        super().__init__(*args, **kwargs)


user_data_schema = UserDataSchema()
users_data_schema = UserDataSchema(many=True)
login_data_schema = UserDataSchema(exclude=False)


# try:
#     data = register_schema.load({"email": "test@example.com", "password": "secure123"})
#     print("Valid data:", data)
# except ValidationError as e:
#     print("Validation errors:", e.messages)
