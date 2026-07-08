"""
tests/test_notification.py — Mixtape

Tests for notification creation when songs are rated or added to playlists.
"""

import pytest

from app import create_app, db
from models import Notification, Playlist, Song, User, playlist_entries
from services.notification_service import add_to_playlist, rate_song


@pytest.fixture
def app():
	app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
	with app.app_context():
		db.create_all()
		yield app
		db.drop_all()


def test_rate_song_creates_notification_for_song_sharer(app):
	"""Rating a shared song should notify the user who shared it."""
	with app.app_context():
		sharer = User(username="sharer", email="sharer@example.com")
		rater = User(username="rater", email="rater@example.com")
		db.session.add_all([sharer, rater])
		db.session.flush()

		song = Song(
			title="Shared Song",
			artist="Artist",
			genre="indie",
			shared_by=sharer.id,
		)
		db.session.add(song)
		db.session.commit()

		rating = rate_song(rater.id, song.id, 5)

		notifications = Notification.query.filter_by(user_id=sharer.id).all()
		assert rating.score == 5
		assert len(notifications) == 1
		assert notifications[0].notification_type == "song_rated"
		#assert notifications[0].body == "rater rated your song 'Shared Song' with a 5/5."


def test_add_to_playlist_creates_notification_for_song_sharer(app):
	"""Adding a shared song to a playlist should notify the user who shared it."""
	with app.app_context():
		sharer = User(username="sharer", email="sharer@example.com")
		adder = User(username="adder", email="adder@example.com")
		db.session.add_all([sharer, adder])
		db.session.flush()

		song = Song(
			title="Playlist Song",
			artist="Artist",
			genre="hip-hop",
			shared_by=sharer.id,
		)
		playlist = Playlist(name="My Playlist", created_by=adder.id)
		db.session.add_all([song, playlist])
		db.session.flush()

		db.session.execute(
			playlist_entries.insert().values(
				playlist_id=playlist.id,
				song_id=song.id,
				position=1,
				added_by=adder.id,
			)
		)
		db.session.commit()

		add_to_playlist(playlist.id, song.id, adder.id)

		notifications = Notification.query.filter_by(user_id=sharer.id).all()
		assert len(notifications) == 1
		assert notifications[0].notification_type == "song_added_to_playlist"
		#assert notifications[0].body == "adder added your song 'Playlist Song' to the playlist 'My Playlist'."
