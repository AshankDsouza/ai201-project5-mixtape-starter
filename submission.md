
Report
Show What You Know: Mixtape Bug Hunt

## Codebase Map


```
      App ./app.py  (Python Flask app, serves as the entry point of the API service)
        |
        |
        V
      Routes  ./routes (REST API endpoints grouped together by entity)
        |
        |
        V
     Services ./services (used across routes in service of various functions)
        |
        |
        V
     Models ./models (data layer; represents entities of the relational database)

        Ʌ
        |
        |
     seed_data.py (inserts data into data layer - SQLAlchemy)


     ./tests (tests most services and functions)
```

The REST APIs are grouped in routes with other related REST APIs which pertain to the same entity.

```
      App ./app.py  (Python Flask app, serves as the entry point of the API service)
        |
        |
        V
      Routes  ./routes (REST API endpoints grouped together by entity)
        |
        |
        V
     Services ./services (used across routes in service of various functions)
        |
        |
        V
     Models ./models (data layer; represents entities of the relational database)

        Ʌ
        |
        |
     seed_data.py (inserts data into data layer - SQLAlchemy)


     ./tests (tests most services and functions)
```

The REST APIs are grouped in routes with other related REST APIs which pertain to the same entity.


- [app.py](app.py) creates the Flask app, initializes SQLAlchemy, and registers the route blueprints.
- [models.py](models.py) defines the database tables and relationships for users, songs, playlists, listening events, ratings, notifications, and tags.
- [routes/songs.py](routes/songs.py), [routes/playlists.py](routes/playlists.py), [routes/users.py](routes/users.py), and [routes/feed.py](routes/feed.py) expose the API endpoints and delegate the real work to services.
- [services/streak_service.py](services/streak_service.py) updates and reads listening streak state when a user records a listen.
- [services/feed_service.py](services/feed_service.py) builds the friends-listening-now and activity feed views from listening events.
- [services/search_service.py](services/search_service.py) searches songs by title or artist and returns tag data.
- [services/notification_service.py](services/notification_service.py) creates notifications when a song is added to a playlist or rated.
- [services/playlist_service.py](services/playlist_service.py) fetches playlist metadata and ordered playlist songs.
- [tests/](tests/) contains the regression tests for the service layer.
- [seed_data.py](seed_data.py) seeds sample rows for manual exploration.

One example data flow is rating a song: a request enters `routes/songs.py`, the route calls `services/notification_service.rate_song()`, that service creates or updates the `Rating` row in `models.py`, and then it creates a `Notification` for the original song sharer.

## Bug Fixes

### Issue 1: Sunday streak reset

Reproduction steps: create a user, record a listening event on Saturday, then record another on Sunday. Before the fix, the streak stayed at 1 instead of incrementing to 2.

Navigation strategy: I traced the `/users/<user_id>/streak` route in [routes/users.py](routes/users.py), followed it into [services/streak_service.py](services/streak_service.py), and checked the `update_listening_streak()` branch that compared `days_since_last` and `today.weekday()`.

Root cause: the function had an extra condition that refused to increment when `today.weekday() == 6`, which is Sunday. That meant a perfectly valid consecutive day pair, Saturday to Sunday, took the reset path even though the dates were only one day apart.

Fix: I removed the Sunday-specific check so any `days_since_last == 1` increments the streak.

Side-effect check: I reran the focused streak test for the Sunday case and also checked the same-day path conceptually, because the change only affects the one-day difference branch and should not change the "already listened today" behavior.

### Issue 2: Friends listening now showed yesterday's events

Reproduction steps: create friend listening events where one happened yesterday and one happened today, then call the friends-listening-now flow. Before the fix, events from the previous day could still appear if they were less than 24 hours old.

Navigation strategy: I followed the feed route into [services/feed_service.py](services/feed_service.py), compared the intended behavior in the issue description with the `RECENT_THRESHOLD` filter, and confirmed the query was time-window based instead of calendar-day based.

Root cause: `get_friends_listening_now()` used a 24-hour cutoff (`datetime.now(timezone.utc) - timedelta(hours=24)`) instead of comparing the event date to the current date. That allowed late-night yesterday events to leak into today's feed.

Fix: I changed the logic to filter by `event.listened_at.date() == today` so only events from the current calendar day are shown.

Side-effect check: I ran the feed test that puts one event on the previous day and one on the current day to confirm the previous-day event is excluded while the current-day event still appears.

### Issue 3: Duplicate songs in search

Reproduction steps: search for a song that has multiple tags. Before the fix, the same song could appear multiple times in the results because the join against the tag table produced repeated rows.

Navigation strategy: I followed the search route into [services/search_service.py](services/search_service.py), inspected the query that joined `song_tags`, and compared it with the model relationships in [models.py](models.py) to understand why the row count could expand.

Root cause: the outer join to `song_tags` returned one row per tag association, but the query did not de-duplicate the `Song` rows before materializing them into result dicts. Songs with multiple tags therefore came back multiple times.

Fix: I added `.distinct()` to the song query so each song is returned once even when the join fan-outs into multiple matching rows.

Side-effect check: I checked a no-tag song and a single-tag song path in the search tests to make sure the fix only removes duplicates and does not suppress valid results.

### Issue 4: Rating a song did not notify the sharer

Reproduction steps: have one user share a song and another user rate it. Before the fix, the playlist-add notification existed, but the rating path did not create the equivalent notification for the sharer.

Navigation strategy: I compared the working playlist notification flow and the rating flow in [services/notification_service.py](services/notification_service.py). The playlist path already called `create_notification()`, so I looked for the missing equivalent in `rate_song()`.

Root cause: the `rate_song()` function updated or created the `Rating` row and committed it, but it never created a notification for `song.shared_by`. The architectural pattern was already present in `add_to_playlist()`, but it was missing from the rating path.

Fix: after saving the rating, I added a `create_notification()` call that sends a `song_rated` notification to the original sharer, using the rater's username and the score in the body.

Side-effect check: I checked that self-rating still does not generate a notification, because the existing `if song.shared_by != user_id` guard should continue to block notifications when the sharer rates their own song.

### Issue 5: The last song in a playlist never showed up

Reproduction steps: create a playlist with one song, or inspect a playlist and count the returned songs. Before the fix, the final entry was always missing from the returned list.

Navigation strategy: I followed the playlist route into [services/playlist_service.py](services/playlist_service.py), then looked at the list slicing in `get_playlist_songs()` after the ordered query to see where the final element disappeared.

Root cause: the function returned `songs[:-1]`, which intentionally drops the last item in the list. That turned a correct ordered query into an off-by-one bug that removed the final playlist song every time.

Fix: I changed the return value to `songs` so the service returns all ordered songs from the query result.

Side-effect check: I verified that the ordering logic still works and added a regression test for a single-song playlist, because that case would have failed most obviously if the last element were still being dropped.

## Regression Test

I added `test_single_song_playlist_returns_that_song()` in [tests/test_playlists.py](tests/test_playlists.py) as a regression test for Issue 5. It specifically catches the off-by-one bug that removed the final playlist entry.

## AI Usage


### Instance 1

**Original Usage / Prompt:** Add a test to test if a notification is created when a song is rated and when it is added to a playlist. The notification should be created for the person who shared the song.

**Result:** Produced two unit tests for the notification service.

**Change / Learnt:** Learnt how to write unit tests and got the boilerplate for testing the notification service. Everything seemed in order and no change was needed.

### Instance 2

**Original Usage / Prompt:** Help me figure out how to reproduce the #3 issue in the app, which pertains to duplicate songs returned from a search query.

**Result:** Gave a plausible bug fix but with no steps to help reproduce the bug and confirm it was actually fixed.

**Change / Learnt:** Some less common bugs are so esoteric that they cannot be reproduced by AI, which is trained on routine problems/tasks.

### Additonal usage:
I used AI tools in two concrete ways during this project. First, I asked for help tracing the notification path when a song is rated so I could compare it with the working playlist notification flow. That helped me identify the missing `create_notification()` call in `rate_song()`.

Second, I asked for help reproducing the duplicate-search issue. The AI pointed me toward the search query and the tag join, but I still had to verify the result against the real tests and confirm that the duplicate rows came from the join fan-out.

One place where I had to course-correct was the search bug: the AI suggestion alone was not enough, so I checked the actual query results and the test cases before making the fix. I also used AI to help write and structure the notification tests, then confirmed the generated tests matched the intended behavior.






