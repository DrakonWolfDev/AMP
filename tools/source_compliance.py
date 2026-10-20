"""Validate or download AMP's pinned corresponding-source set."""

import argparse
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "legal/source-manifest.json"


def load_manifest(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("sources"), list):
        raise ValueError("Unsupported or malformed source manifest")
    return data


def unresolved_sources(data):
    return [entry["name"] for entry in data["sources"] if entry.get("status") != "pinned"]


def validate_pinned(entry):
    required = ("name", "version", "filename", "url", "sha256")
    missing = [field for field in required if not entry.get(field)]
    if missing:
        raise ValueError(f"{entry.get('name', 'source')}: missing {', '.join(missing)}")
    if len(entry["sha256"]) != 64 or any(c not in "0123456789abcdef" for c in entry["sha256"]):
        raise ValueError(f"{entry['name']}: invalid SHA-256")
    if not entry["url"].startswith("https://"):
        raise ValueError(f"{entry['name']}: source URL must use HTTPS")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_sources(data, output):
    if output.exists():
        raise ValueError("Choose a new output directory; source bundles are never overwritten")
    output.mkdir(parents=True)
    try:
        for entry in data["sources"]:
            if entry.get("status") != "pinned":
                continue
            validate_pinned(entry)
            destination = output / entry["filename"]
            with (
                urllib.request.urlopen(entry["url"], timeout=120) as response,
                destination.open("wb") as stream,
            ):
                shutil.copyfileobj(response, stream)
            actual = digest(destination)
            if actual != entry["sha256"]:
                raise ValueError(f"{entry['name']}: checksum mismatch ({actual})")
        shutil.copyfile(DEFAULT_MANIFEST, output / DEFAULT_MANIFEST.name)
        shutil.copyfile(ROOT / "THIRD_PARTY_NOTICES.md", output / "THIRD_PARTY_NOTICES.md")
        shutil.copyfile(ROOT / "docs/QT_REDISTRIBUTION.md", output / "QT_REDISTRIBUTION.md")
        shutil.copytree(ROOT / "LICENSES", output / "LICENSES")
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check-ready", action="store_true")
    parser.add_argument("--download", type=Path)
    args = parser.parse_args()
    data = load_manifest(args.manifest)
    for entry in data["sources"]:
        if entry.get("status") == "pinned":
            validate_pinned(entry)
    unresolved = unresolved_sources(data)
    if args.download:
        download_sources(data, args.download.resolve())
    if args.check_ready and unresolved:
        parser.error("unresolved source entries: " + "; ".join(unresolved))
    print(
        f"Pinned sources: {len(data['sources']) - len(unresolved)}; unresolved: {len(unresolved)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
