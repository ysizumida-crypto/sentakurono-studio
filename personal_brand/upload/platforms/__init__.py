"""Platform-specific uploaders for the personal_brand pipeline.

Each module exposes:
    upload(entry_dir: Path, meta: dict) -> str | None
        Performs the platform-specific upload, returns the URL/ID of the
        uploaded item on success, or raises on failure.
"""
