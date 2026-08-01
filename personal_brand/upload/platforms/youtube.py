"""YouTube Shorts uploader (refactored as scheduler-compatible module).

Reuses the OAuth flow from upload_to_youtube.py so the existing token.json
keeps working.

Required env vars (for headless / GitHub Actions runs):
    YOUTUBE_CLIENT_SECRETS_JSON   (full JSON content of client_secrets.json)
    YOUTUBE_REFRESH_TOKEN         (refresh token from a previous local OAuth)

Falls back to the file-based flow (client_secrets.json + token.json next to
upload_to_youtube.py) when env vars are absent — useful for local testing.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
UPLOAD_DIR = Path(__file__).resolve().parents[1]
CLIENT_SECRETS_FILE = UPLOAD_DIR / "client_secrets.json"
TOKEN_FILE = UPLOAD_DIR / "token.json"


def _credentials() -> Credentials:
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    secrets_json = os.environ.get("YOUTUBE_CLIENT_SECRETS_JSON")

    if refresh_token and secrets_json:
        secrets = json.loads(secrets_json)
        client = secrets.get("installed") or secrets.get("web") or secrets
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=client.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=client["client_id"],
            client_secret=client["client_secret"],
            scopes=SCOPES,
        )
        creds.refresh(Request())
        return creds

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())
        return creds

    if not CLIENT_SECRETS_FILE.exists():
        raise RuntimeError(
            "YouTube credentials not configured. Either set "
            "YOUTUBE_CLIENT_SECRETS_JSON + YOUTUBE_REFRESH_TOKEN, or place "
            f"client_secrets.json at {CLIENT_SECRETS_FILE} and run upload_to_youtube.py once locally."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())
    return creds


def upload(entry_dir: Path, meta: dict) -> str:
    video_path = entry_dir / "final.mp4"
    if not video_path.exists():
        raise FileNotFoundError(f"final.mp4 not found in {entry_dir}")

    youtube = build("youtube", "v3", credentials=_credentials())

    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta.get("description", ""),
            "tags": meta.get("tags", []),
            "categoryId": str(meta.get("category_id", "22")),
            "defaultLanguage": meta.get("language", "ja"),
            "defaultAudioLanguage": meta.get("language", "ja"),
        },
        "status": {
            "privacyStatus": meta.get("privacy", "private"),
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }
    if meta.get("scheduled_at"):
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = meta["scheduled_at"]

    media = MediaFileUpload(
        str(video_path),
        chunksize=-1,
        resumable=True,
        mimetype="video/mp4",
    )
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )
    response = None
    while response is None:
        status, response = request.next_chunk()

    return f"https://youtu.be/{response['id']}"
