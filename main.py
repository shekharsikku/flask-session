from src.server import app, server_mode
from waitress import serve


if __name__ == "__main__":
    try:
        if server_mode == "development":
            app.run(debug=True, host="0.0.0.0", port=8100)  # * Debug/Development
        elif server_mode == "deployment":
            serve(app=app, host="127.0.0.1", port=8070)     # ? Production/Deployment
        else:
            raise Exception("Please Specify, Server Mode either Development or Deployment!")
    except Exception as e:
        print(f"Unable to run your Flask Application! \n{e}")
    

# >>> from server import app, db
# >>> with app.app_context():
# >>>     db.create_all()
