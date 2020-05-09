from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

user_sync_table = db.Table("user-sync", db.Model.metadata,
                           db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
                           db.Column("sync_id", db.Integer, db.ForeignKey("sync.id"))
                           )


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    playlists = db.relationship("Playlist", cascade='delete')
    syncs = db.relationship("Sync", secondary=user_sync_table, back_populates="users")

    def __init__(self, **kwargs):
        self.username = kwargs.get("username", "")
        self.email = kwargs.get("email", "")

    def serialize(self):
        return {
            "username": self.username,
            "email": self.email,
            "playlists": [p.serialize() for p in self.playlists],
            "syncs": [s.sub_serialize() for s in self.syncs]
        }

    def sub_serialize(self):
        return {
            "username": self.username,
            "email": self.email
        }


class Playlist(db.Model):
    __tablename__ = "playlist"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    spotify_id = db.Column(db.String, nullable=False)
    songs = db.Column(db.String, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.spotify_id = kwargs.get("spotify_id")
        self.songs = kwargs.get("songs", "")
        self.user_id = kwargs.get("user_id", "")

    def serialize(self):
        return {
            "name": self.name,
            "spotify_id": self.spotify_id,
            "songs": self.songs.split(';')
        }


class Sync(db.Model):
    __tablename__ = "sync"
    id = db.Column(db.Integer, primary_key=True)
    sync = db.Column(db.String, default="")
    users = db.relationship("User", secondary=user_sync_table, back_populates="syncs")

    def __init__(self, **kwargs):
        self.sync = kwargs.get("sync", "")  # input through dao as a string

    def serialize(self):
        return {
            "users": [user.sub_serialize() for user in self.users],
            "synced_playlist": self.sync.split(';')
        }

    def sub_serialize(self):
        return {
            "sync": self.sync.split(';')
        }
