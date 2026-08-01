"""Instagram Reels uploader via Meta Graph API.

Required env vars:
    META_ACCESS_TOKEN              (long-lived user access token, ig_content_publish scope)
    META_INSTAGRAM_BUSINESS_ID     (Instagram Business Account ID)

Prerequisite:
- Instagram Business Account connected to a Facebook Page
- The video must be hosted at a publicly accessible URL (Instagram pulls it).
  This module expects `meta["instagram_video_url"]` to be a public URL,
  OR `INSTAGRAM_VIDEO_BASE_URL` env var + `final.mp4` already uploaded externally
  (e.g., to S3, Cloudflare R2, GitHub Release asset).

Reference: https://developers.facebook.com/docs/instagram-api/guides/content-publishing
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import requests

API_BASE = "https://graph.facebook.com/v18.0"


def _resolve_video_url(entry_dir: Path, meta: dict) -> str:
    url = meta.get("instagram_video_url")
    if url:
        return url
    base = os.environ.get("INSTAGRAM_VIDEO_BASE_URL")
    if base:
        return f"{base.rstrip('/')}/{entry_dir.name}/final.mp4"
    raise RuntimeError(
        "Instagram requires a public video URL. "
        "Set meta['instagram_video_url'] or INSTAGRAM_VIDEO_BASE_URL env var."
    )


def _resolve_caption(meta: dict) -> str:
    caption = meta.get("instagram_caption") or meta.get("description", "")
    if len(caption) > 2200:
        caption = caption[:2197] + "..."
    return caption


def upload(entry_dir: Path, meta: dict) -> str:
    token = os.environ.get("META_ACCESS_TOKEN")
    ig_id = os.environ.get("META_INSTAGRAM_BUSINESS_ID")
    if not token or not ig_id:
        raise RuntimeError("META_ACCESS_TOKEN and META_INSTAGRAM_BUSINESS_ID required")

    video_url = _resolve_video_url(entry_dir, meta)
    caption = _resolve_caption(meta)

    create_res = requests.post(
        f"{API_BASE}/{ig_id}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
            "access_token": token,
        },
    )
    create_res.raise_for_status()
    creation_id = create_res.json()["id"]

    # Poll until processed (Instagram processes the video asynchronously)
    for _ in range(60):
        status_res = requests.get(
            f"{API_BASE}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
        )
        status_res.raise_for_status()
        if status_res.json().get("status_code") == "FINISHED":
            break
        time.sleep(5)
    else:
        raise RuntimeError("Instagram media processing timed out (5 min)")

    publish_res = requests.post(
        f"{API_BASE}/{ig_id}/media_publish",
        params={"creation_id": creation_id, "access_token": token},
    )
    publish_res.raise_for_status()
    media_id = publish_res.json()["id"]
    return f"https://www.instagram.com/reel/{media_id}/"
