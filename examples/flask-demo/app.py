from flask import Flask
import os
import socket

app = Flask(__name__)


@app.route("/")
def hello():
    return {
        "message": "Hej fra Flask",
        "hostname": socket.gethostname(),
        "environment": os.environ.get("APP_ENV", "local"),
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
