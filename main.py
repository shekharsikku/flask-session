from logging import basicConfig, DEBUG
from waitress import serve
from src.server import app


# Server Mode - development/deployment
server_mode = "development"


if __name__ == "__main__":
    try:
        if server_mode == "development":
            basicConfig(level=DEBUG)
            app.run(debug=True, host="0.0.0.0", port=8100)
        elif server_mode == "deployment":
            serve(app=app, host="127.0.0.1", port=8070)
        else:
            raise Exception("Unable to run Flask Application!")
    except Exception as e:
        print(f"{e}")
    

# >>> from server import app, db
# >>> with app.app_context():
# >>>     db.create_all()
