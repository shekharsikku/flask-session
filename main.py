from logging import basicConfig, DEBUG, INFO
from src.app import app, socketio
from src.utils import envs


if __name__ == "__main__":
    try:
        is_development = envs["SERVER_MODE"] == "development"
        basicConfig(level=DEBUG if is_development else INFO, force=True)
        print(f"Flask app starting in {envs["SERVER_MODE"]} mode!")
        socketio.run(app=app, host="localhost", port=envs["PORT"], debug=is_development)
    except Exception as e:
        print(f"Error: {e}")
        