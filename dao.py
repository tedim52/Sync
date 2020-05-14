from db import db, User, Playlist, Sync
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Spotify API
client_id = os.environ["client_id"]
client_secret = os.environ["client_secret"]
cc = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=cc)

# Sendgrid API
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]


def send_email(receiver, spotify_username, sync):
    email_content = "<p> Hi, <br><br> Congratulations on your sync with " + spotify_username + \
                    ". Here are some songs you'll both be sure to enjoy.<br><br>" + sync.sync + \
                    "<br><br> Happy listening! <br> Team @Sync"

    message = Mail(
        from_email='tbm42@cornell.edu',
        to_emails=receiver,
        subject='Congratulations! Sync created with ' + spotify_username,
        html_content=email_content)
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)


def stringify_songs(playlist_id):
    """Takes in the spotify id of a playlist and returns the songs as a string seperated by a ';'. """
    songs = ""
    songs_list = sp.playlist_tracks(playlist_id).get("items")
    for song in songs_list:
        if song.get("track") is None:
            songs += ";"
        else:
            songs += song.get("track").get("name") + ";"
    return songs[:-1]


def stringify_sync(playlist_list):
    """Takes in a list of song names and returns them as a string seperated by a ';'. """
    songs = ""
    songs_list = playlist_list
    for song in songs_list:
        songs += song + ";"
    return songs[:-1]


def sync(playlist_one, playlist_two):
    """ Creates sync of two playlist.

        Takes in two lists of song names and returns a list
        of songs that appear in both playlists.
    """
    temp = set(playlist_two)
    lst3 = [song for song in playlist_one if song in temp]
    no_dups_lst3 = set(lst3)
    return list(no_dups_lst3)


def create_user(username, email, spotify_ids):
    new_user = User(username=username, email=email)
    db.session.add(new_user)
    db.session.commit()
    user_id = new_user.id

    playlists = spotify_ids.get("items")
    for playlist in playlists:
        name = playlist.get("name")
        spotify_id = playlist.get("id")
        songs = stringify_songs(spotify_id)
        new_playlist = Playlist(name=name,
                                spotify_id=spotify_id,
                                songs=songs,
                                user_id=user_id)
        db.session.add(new_playlist)
        db.session.commit()

    return new_user.serialize()


def get_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return None
    return user.serialize()


def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return None
    db.session.delete(user)
    db.session.commit()
    return user.serialize()


def add_playlist(username, name, spotify_id):
    user = User.query.filter_by(username=username).first()
    songs = stringify_songs(spotify_id)
    new_playlist = Playlist(name=name,
                            songs=songs,
                            spotify_id=spotify_id,
                            user_id=user.id)
    db.session.add(new_playlist)
    db.session.commit()
    return user.serialize()


def create_sync(user_one, user_two):
    user_one = User.query.filter_by(username=user_one).first()
    user_two = User.query.filter_by(username=user_two).first()

    user_one_playlists = []
    user_two_playlists = []
    user_one_songs = ""
    user_two_songs = ""

    for playlist in user_one.playlists:
        user_one_playlists.append(playlist.spotify_id)
    for playlist in user_two.playlists:
        user_two_playlists.append(playlist.spotify_id)
    for spotify_id in user_one_playlists:
        user_one_songs += stringify_songs(spotify_id)
    for spotify_id in user_two_playlists:
        user_two_songs += stringify_songs(spotify_id)

    synced_playlist = sync(user_one_songs.split(';'),
                           user_two_songs.split(';'))

    string_synced = stringify_sync(synced_playlist)
    new_sync = Sync(sync=string_synced)
    send_email(user_one.email, user_two.username, new_sync)
    send_email(user_two.email, user_one.username, new_sync)

    db.session.add(new_sync)
    user_one.syncs.append(new_sync)
    user_two.syncs.append(new_sync)
    db.session.commit()
    return new_sync.serialize()


def get_sync(user_one, user_two):
    user_one = User.query.filter_by(username=user_one).first()
    user_two = User.query.filter_by(username=user_two).first()

    syncs = db.session.query(Sync).all()
    for sync in syncs:
        sync_users = sync.serialize().get("users")
        if user_one.sub_serialize() in sync_users:
            if user_two.sub_serialize() in sync_users:
                return sync.serialize()
    return None
