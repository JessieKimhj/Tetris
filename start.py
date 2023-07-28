from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route("/")
def index():
    #127.0.0.1/html/css/b.css
    return send_from_directory('html', "index.html")

 #127.0.0.1/css/b.css
@app.route('/<path:name>')
def start(name):
    return send_from_directory('html', name)

