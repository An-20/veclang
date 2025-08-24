import os
from bottle import Bottle, static_file, run

dist_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../")

app = Bottle()


@app.route("/")
def index():
    return static_file("index.html", root="/path/to/your/static/directory")


@app.route("/dist/<filepath:path>")
def serve_static(filepath):
    return static_file(filepath, root="/path/to/your/static/directory")


run(app, host="0.0.0.0", port=8080)
