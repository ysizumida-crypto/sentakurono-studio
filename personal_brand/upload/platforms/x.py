"""X (formerly Twitter) uploader.

Uses Tweepy with OAuth 1.0a User Context (required for media upload).

Required env vars:
    X_API_KEY
    X_API_SECRET
    X_ACCESS_TOKEN
    X_ACCESS_SECRET

Behavior:
- For posts/<entry>/metadata.yml: posts the `x_excerpt` text (or `description` truncated to 280 chars).
- For videos/<entry>/metadata.yml: uploads final.mp4 (<= 512 MB, <= 140 sec for free tier) with `x_excerpt` text.

Reference: https://docs.tweepy.org/en/stable/client.html
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    import tweepy
except ImportError as exc:
    tweepy = None
    _import_err = exc


def _client() -> "tweepy.Client":
    if tweepy is None:
        raise RuntimeError(f"tweepy not installed: {_import_err}")
    required = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"missing env vars: {missing}")
    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )


def _v1_api() -> "tweepy.API":
    if tweepy is None:
        raise RuntimeError(f"tweepy not installed: {_import_err}")
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"],
        os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"],
        os.environ["X_ACCESS_SECRET"],
    )
    return tweepy.API(auth)


def _resolve_text(meta: dict) -> str:
    text = meta.get("x_excerpt") or meta.get("excerpt") or meta.get("description", "")
    text = text.strip()
    if len(text) > 280:
        text = text[:277] + "..."
    return text


def upload(entry_dir: Path, meta: dict) -> str:
    text = _resolve_text(meta)
    if not text:
        raise ValueError("no text to post (x_excerpt / excerpt / description)")

    media_ids = []
    video_path = entry_dir / "final.mp4"
    if video_path.exists():
        api = _v1_api()
        media = api.media_upload(
            filename=str(video_path),
            media_category="tweet_video",
            chunked=True,
        )
        media_ids.append(media.media_id)

    client = _client()
    response = client.create_tweet(
        text=text,
        media_ids=media_ids if media_ids else None,
    )
    tweet_id = response.data["id"]
    return f"https://x.com/i/status/{tweet_id}"
