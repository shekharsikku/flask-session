from logging import basicConfig, DEBUG
from src.app import app, socketio


if __name__ == "__main__":
    try:
        basicConfig(level=DEBUG)
        socketio.run(app=app, host="localhost", port=4000, debug=True)
    except Exception as e:
        print(f"Error: {e}")
        