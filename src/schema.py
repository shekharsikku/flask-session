from flask_marshmallow import Marshmallow

ma = Marshmallow()


class UserSchema(ma.Schema):
    class Meta:
        fields = ("uid", "username", "email", "fullname", "date")


user_schema = UserSchema()
users_schema = UserSchema(many=True)


class LoginUserSchema(ma.Schema):
    class Meta:
        fields = ("uid", "username", "email", "fullname", "password", "date")


login_user_schema = LoginUserSchema()
