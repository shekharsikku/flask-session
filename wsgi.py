from src.app import app, socketio
from src.utils import envs


if __name__ == "__main__":
    try:
        socketio.run(app=app, host="0.0.0.0", port=envs["PORT"])
    except Exception as e:
        print(f"Error: {e}")
        