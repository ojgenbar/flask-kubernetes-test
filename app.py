from flask import Flask
from flask import request
import socket

app = Flask(__name__)
application = app

hostname = socket.gethostname()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/hostinfo")
def hostinfo():
    data = {
        "request.remote_addr": request.remote_addr,
        "request.host": request.host,
        "request.host_url": request.host_url,
        'system.hostname': hostname,
    }
    return data
