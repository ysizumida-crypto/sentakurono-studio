"""TikTok uploader via Content Posting API (Direct Post).

Required env vars:
    TIKTOK_ACCESS_TOKEN     (OAuth, video.upload + video.publish scopes)

Behavior:
- Initiates upload session
- Uploads final.mp4 in chunks (or single PUT for files <= 64 MB)
- Submits for publish

Note: As of 2026 the TikTok Content Posting API requires app review and
approved scopes. For unverified accounts, upload via Direct Post will land
in Inbox as draft, requiring manual publish from the app.

Reference: https://developers.tiktok.com/doc/content-posting-api-reference-direct-post
"""
from __future__ import annotations

import os
from pathlib import Path

import requests

API_BASE = "https://open.tiktokapis.com/v2"


def _headers() -> dict:
    token = os.environ.get("TIKTOK_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("TIKTOK_ACCESS_TOKEN not set")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def upload(entry_dir: Path, meta: dict) -> str:
    video_path = entry_dir / "final.mp4"
    if not video_path.exists():
        raise FileNotFoundError(f"final.mp4 not found in {entry_dir}")

    file_size = video_path.stat().st_size
    title = (meta.get("tiktok_caption") or meta.get("title", ""))[:150]

    init_res = requests.post(
        f"{API_BASE}/post/publish/video/init/",
        headers=_headers(),
        json={
            "post_info": {
                "title": title,
                "privacy_level": "SELF_ONLY",
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1,
            },
        },
    )
    init_res.raise_for_status()
    init_data = init_res.json()["data"]
    upload_url = init_data["upload_url"]
    publish_id = init_data["publish_id"]

    with video_path.open("rb") as f:
        put_res = requests.put(
            upload_url,
            headers={
                "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
                "Content-Type": "video/mp4",
            },
            data=f.read(),
        )
    put_res.raise_for_status()

    return f"tiktok:publish_id:{publish_id}"
