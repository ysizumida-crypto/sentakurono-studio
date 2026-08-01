#!/usr/bin/env python3
"""
Multi-platform scheduler for personal_brand pipeline.

Walks personal_brand/videos/ and personal_brand/posts/, finds entries whose
metadata.yml has scheduled_at <= now and platform-specific status == "pending",
then dispatches to the appropriate uploader.

After successful upload, updates metadata.yml status field and writes back.

Usage:
    python scheduler.py [--dry-run] [--root <path>]

Designed to be run on a cron / GitHub Actions schedule (every 5-10 min).

Environment variables (per platform) — see automation_roadmap.md for full list.
"""
import argparse
import datetime as dt
import importlib
import sys
from pathlib import Path

import yaml

REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[2]
PERSONAL_BRAND_DIR = "personal_brand"

PLATFORM_MODULES = {
    "youtube": "platforms.youtube",
    "x": "platforms.x",
    "linkedin": "platforms.linkedin",
    "instagram": "platforms.instagram",
    "tiktok": "platforms.tiktok",
}


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def parse_iso(value) -> dt.datetime:
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
    s = str(value).replace("Z", "+00:00")
    return dt.datetime.fromisoformat(s)


def find_entries(root: Path):
    """Yield (entry_dir, meta_path, meta_dict) for every entry that has metadata.yml."""
    base = root / PERSONAL_BRAND_DIR
    for sub in ("videos", "posts"):
        target = base / sub
        if not target.exists():
            continue
        for meta_path in target.rglob("metadata.yml"):
            with meta_path.open() as f:
                meta = yaml.safe_load(f) or {}
            yield meta_path.parent, meta_path, meta


def dispatch(entry_dir: Path, platform: str, meta: dict, dry_run: bool) -> str:
    """Returns new status: 'uploaded', 'skipped', or 'failed:<reason>'."""
    if dry_run:
        return "skipped:dry-run"
    module_name = PLATFORM_MODULES.get(platform)
    if module_name is None:
        return f"failed:unknown_platform"
    try:
        mod = importlib.import_module(module_name)
        result = mod.upload(entry_dir, meta)
        return f"uploaded:{result}" if result else "uploaded"
    except Exception as e:
        return f"failed:{type(e).__name__}:{e}"


def process_entry(entry_dir: Path, meta_path: Path, meta: dict, dry_run: bool) -> bool:
    platforms = meta.get("platforms") or []
    if not platforms:
        return False

    scheduled_at = meta.get("scheduled_at")
    if scheduled_at:
        try:
            scheduled = parse_iso(scheduled_at)
        except ValueError:
            print(f"  [skip] {entry_dir.name}: invalid scheduled_at={scheduled_at}")
            return False
        if scheduled > now_utc():
            return False  # not yet due

    status_block = meta.setdefault("status", {})
    changed = False
    for platform in platforms:
        current = status_block.get(platform, "pending")
        if current != "pending":
            continue
        print(f"  → {entry_dir.name} / {platform} ...", end=" ", flush=True)
        new_status = dispatch(entry_dir, platform, meta, dry_run)
        print(new_status)
        status_block[platform] = new_status
        changed = True

    if changed and not dry_run:
        with meta_path.open("w") as f:
            yaml.safe_dump(meta, f, allow_unicode=True, sort_keys=False)
    return changed


def main():
    parser = argparse.ArgumentParser(description="Multi-platform scheduler for personal_brand")
    parser.add_argument("--root", default=str(REPO_ROOT_DEFAULT), help="Repo root directory")
    parser.add_argument("--dry-run", action="store_true", help="Do not actually upload")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    sys.path.insert(0, str(root / PERSONAL_BRAND_DIR / "upload"))

    print(f"scheduler running at {now_utc().isoformat()} (root={root})")
    if args.dry_run:
        print("  DRY RUN — no uploads will occur")

    any_changes = False
    for entry_dir, meta_path, meta in find_entries(root):
        if process_entry(entry_dir, meta_path, meta, args.dry_run):
            any_changes = True

    if not any_changes:
        print("  nothing due")


if __name__ == "__main__":
    main()
