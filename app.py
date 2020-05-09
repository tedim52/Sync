# =================================================================
# Tedi Mitiku tbm42
# BackendDesign Final Project: Sync
# =================================================================
from flask import Flask, request, render_template
from db import db
import dao
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

app = Flask(__name__)
db_filename = "spotify.db"

# SQLAlchemy setup config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = False


db.init_app(app)
with app.app_context():
    db.create_all()

# Spotify API
client_id = os.environ["client_id"]
client_secret = os.environ["client_secret"]
cc = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=cc)


def success_response(data, code=200):
    return json.dumps({"success": True, "data": data}), code


def failure_response(message, code=404):
    return json.dumps({"success": False, "error": message}), code


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/api/users/", methods=["POST"])
def create_user():
    body = json.loads(request.data)
    username = body.get("username")
    email = body.get("email")
    try:
        spotify_ids = sp.user_playlists(username)
    except spotipy.exceptions.SpotifyException:
        return failure_response("No Spotify account with given username.")
    user = dao.create_user(username, email, spotify_ids)
    return success_response(user)


@app.route("/api/users/<username>/", methods=["GET"])
def get_user(username):
    user = dao.get_user(username)
    if user is None:
        return failure_response("Username not saved. Create user first.")
    return success_response(user)


@app.route("/api/users/<username>/", methods=["DELETE"])
def delete_user(username):
    user = dao.delete_user(username)
    if user is None:
        return failure_response("Username not saved.")
    return success_response(user)


@app.route("/api/users/<username>/", methods=["POST"])
def add_playlist_user(username):
    body = json.loads(request.data)
    user = dao.get_user(username)
    if user is None:
        return failure_response("Username not saved.")
    dao.add_playlist(username,
                     body.get("name"),
                     body.get("playlist"))
    return success_response(user)


@app.route("/api/syncs/", methods=["POST"])
def create_sync():
    body = json.loads(request.data)
    user_one = body.get("user_one")
    user_two = body.get("user_two")

    if dao.get_user(user_one) is None:
        return failure_response("User one not saved.")
    if dao.get_user(user_two) is None:
        return failure_response("User two not saved.")

    sync = dao.create_sync(user_one, user_two)
    return success_response(sync)


@app.route("/api/syncs/", methods=["GET"])
def get_sync():
    body = json.loads(request.data)
    user_one = body.get("user_one")
    user_two = body.get("user_two")

    if dao.get_user(user_one) is None:
        return failure_response("User one not saved.")
    if dao.get_user(user_two) is None:
        return failure_response("User two not saved.")

    sync = dao.get_sync(user_one, user_two)
    if sync is None:
        return failure_response("Sync not saved.")
    return success_response(sync)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
