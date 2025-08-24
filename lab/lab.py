import os
from bottle import Bottle, static_file, run

DIST_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/dist/")

if not os.path.exists(DIST_DIR):
    raise RuntimeError("dist dir does not exist! run npm build first!")


app = Bottle()


@app.route("/")
def index():
    return static_file("index.html", root=DIST_DIR)


@app.route("/<filepath:path>")
def serve_static(filepath):
    return static_file(filepath, root=DIST_DIR)


run(app, port=8080)
