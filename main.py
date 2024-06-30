from logging import basicConfig, DEBUG
from src.app import app, socketio
from src.utils import envs


if __name__ == "__main__":
    try:
        is_development = envs["SERVER_MODE"] == "development"
        if is_development:
            basicConfig(level=DEBUG)
        socketio.run(app=app, host="localhost", port=envs["PORT"], debug=is_development)
    except Exception as e:
        print(f"Error: {e}")
        