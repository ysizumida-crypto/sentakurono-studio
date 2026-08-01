#!/usr/bin/env python3
"""
YouTube Shorts auto-uploader for ぷろたん personal_brand pipeline.

Usage:
    python upload_to_youtube.py <video_dir>

Example:
    python upload_to_youtube.py ../videos/001_iwanagahime_short

Expects in <video_dir>:
    final.mp4       - the video file (vertical 9:16, <=60s for Shorts)
    metadata.yml    - title, description, tags, privacy, scheduled_at, etc.

First-run setup:
    1. Place client_secrets.json in this directory (from Google Cloud Console).
    2. Install dependencies: pip install -r requirements.txt
    3. Run this script. Browser will open for OAuth consent.
    4. token.json will be saved for subsequent automated runs.
"""
import argparse
import os
import sys
from pathlib import Path

import yaml
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SCRIPT_DIR = Path(__file__).resolve().parent
CLIENT_SECRETS_FILE = SCRIPT_DIR / "client_secrets.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"


def get_authenticated_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRETS_FILE.exists():
                sys.exit(
                    f"client_secrets.json not found at {CLIENT_SECRETS_FILE}\n"
                    "Download it from Google Cloud Console (APIs & Services → Credentials → OAuth Client ID for Desktop app)."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(video_dir: Path) -> str:
    video_path = video_dir / "final.mp4"
    metadata_path = video_dir / "metadata.yml"

    if not video_path.exists():
        sys.exit(f"final.mp4 not found in {video_dir}")
    if not metadata_path.exists():
        sys.exit(f"metadata.yml not found in {video_dir}")

    with metadata_path.open() as f:
        meta = yaml.safe_load(f)

    required = ("title",)
    for key in required:
        if key not in meta:
            sys.exit(f"metadata.yml missing required field: {key}")

    youtube = get_authenticated_service()

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

    print(f"uploading {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)...")
    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"  progress: {int(status.progress() * 100)}%")
        except HttpError as e:
            sys.exit(f"upload failed: {e}")

    video_id = response["id"]
    url = f"https://youtu.be/{video_id}"
    print(f"\nuploaded: {url}")

    if meta.get("scheduled_at"):
        print(f"scheduled to publish at: {meta['scheduled_at']}")
    else:
        print(f"privacy: {body['status']['privacyStatus']}")

    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload a video to YouTube from a personal_brand video directory.")
    parser.add_argument("video_dir", help="Path to video directory containing final.mp4 and metadata.yml")
    args = parser.parse_args()
    upload(Path(args.video_dir).resolve())


if __name__ == "__main__":
    main()
