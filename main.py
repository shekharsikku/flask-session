from logging import basicConfig, DEBUG
from src.app import app, socketio
from src.utils import envs


if __name__ == "__main__":
    try:
        basicConfig(level=DEBUG)
        socketio.run(app=app, host="localhost", port=envs["PORT"], debug=True)
    except Exception as e:
        print(f"Error: {e}")
        