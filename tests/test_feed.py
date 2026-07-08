"""
tests/test_feed.py — Mixtape

Tests for friends listening now and activity feed logic.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app import create_app, db
from models import ListeningEvent, Song, User, friendships
from services.feed_service import get_friends_listening_now


@pytest.fixture
def app():
	app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
	with app.app_context():
		db.create_all()
		yield app
		db.drop_all()


def test_get_friends_listening_now_excludes_yesterday_events(app):
	"""Events older than today should not appear in the feed."""
	with app.app_context():
		current_user = User(username="current", email="current@example.com")
		friend_yesterday = User(username="yesterday_friend", email="yesterday@example.com")
		friend_recent = User(username="recent_friend", email="recent@example.com")
		db.session.add_all([current_user, friend_yesterday, friend_recent])
		db.session.flush()

		db.session.execute(
			friendships.insert().values(user_id=current_user.id, friend_id=friend_yesterday.id)
		)
		db.session.execute(
			friendships.insert().values(user_id=current_user.id, friend_id=friend_recent.id)
		)

		yesterday_song = Song(
			title="Yesterday Song",
			artist="Old Friend",
			genre="indie",
			shared_by=current_user.id,
		)
		recent_song = Song(
			title="Recent Song",
			artist="New Friend",
			genre="indie",
			shared_by=current_user.id,
		)
		db.session.add_all([yesterday_song, recent_song])
		db.session.flush()
		now = datetime(2024, 6, 15, 8, 0, 0, tzinfo=timezone.utc)
		yesterday_night = datetime(2024, 6, 14, 23, 0, 0, tzinfo=timezone.utc)


		db.session.add(
			ListeningEvent(
				user_id=friend_yesterday.id,
				song_id=yesterday_song.id,
				listened_at=yesterday_night,
			)
		)
		db.session.add(
			ListeningEvent(
				user_id=friend_recent.id,
				song_id=recent_song.id,
				listened_at=now,
			)
		)
		db.session.commit()

		results = get_friends_listening_now(current_user.id, now=now)

		titles = [item["song"]["title"] for item in results]
		assert "Recent Song" in titles
		assert "Yesterday Song" not in titles
		assert len(results) == 1
