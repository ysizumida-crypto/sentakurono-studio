"""LinkedIn uploader (personal profile posts).

Uses LinkedIn UGC Post API.

Required env vars:
    LINKEDIN_ACCESS_TOKEN   (3-legged OAuth, w_member_social scope)
    LINKEDIN_PERSON_URN     (urn:li:person:XXXX, fetched via /v2/me)

Behavior:
- For posts: text-only share using `linkedin_summary` (or `description`).
- For videos: registers asset → uploads final.mp4 → creates UGC post with video.

Note: For company pages (买收会社 PR), set LINKEDIN_ORG_URN and use that instead.

Reference: https://learn.microsoft.com/en-us/linkedin/marketing/integrations/community-management/shares/ugc-post-api
"""
from __future__ import annotations

import os
from pathlib import Path

import requests

API_BASE = "https://api.linkedin.com/v2"


def _headers() -> dict:
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("LINKEDIN_ACCESS_TOKEN not set")
    return {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }


def _author_urn(meta: dict) -> str:
    urn = meta.get("linkedin_urn") or os.environ.get("LINKEDIN_PERSON_URN")
    if not urn:
        raise RuntimeError("LINKEDIN_PERSON_URN not set and no linkedin_urn in meta")
    return urn


def _resolve_text(meta: dict) -> str:
    return (meta.get("linkedin_summary") or meta.get("description", "")).strip()


def _register_video_asset(author_urn: str) -> tuple[str, str]:
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
            "owner": author_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    res = requests.post(f"{API_BASE}/assets?action=registerUpload", headers=_headers(), json=payload)
    res.raise_for_status()
    data = res.json()["value"]
    asset = data["asset"]
    upload_url = data["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    return asset, upload_url


def _upload_video_bytes(upload_url: str, video_path: Path) -> None:
    with video_path.open("rb") as f:
        res = requests.put(
            upload_url,
            headers={"Authorization": _headers()["Authorization"]},
            data=f.read(),
        )
    res.raise_for_status()


def upload(entry_dir: Path, meta: dict) -> str:
    text = _resolve_text(meta)
    if not text:
        raise ValueError("no text for LinkedIn post (linkedin_summary / description)")

    author = _author_urn(meta)
    video_path = entry_dir / "final.mp4"

    body: dict = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    if video_path.exists():
        asset_urn, upload_url = _register_video_asset(author)
        _upload_video_bytes(upload_url, video_path)
        body["specificContent"]["com.linkedin.ugc.ShareContent"].update(
            {
                "shareMediaCategory": "VIDEO",
                "media": [
                    {
                        "status": "READY",
                        "media": asset_urn,
                        "title": {"text": meta.get("title", "")[:200]},
                    }
                ],
            }
        )

    res = requests.post(f"{API_BASE}/ugcPosts", headers=_headers(), json=body)
    res.raise_for_status()
    post_urn = res.json().get("id") or res.headers.get("x-restli-id", "")
    return f"https://www.linkedin.com/feed/update/{post_urn}"
