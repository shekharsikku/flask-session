from src.app import app, socketio


if __name__ == "__main__":
    try:
        socketio.run(app=app, host="0.0.0.0", port=4000)
    except Exception as e:
        print(f"Error: {e}")
        