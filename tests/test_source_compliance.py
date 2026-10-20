import json

import pytest

from tools.source_compliance import load_manifest, unresolved_sources, validate_pinned


def test_release_source_manifest_is_well_formed():
    manifest = load_manifest("legal/source-manifest.json")
    assert manifest["distribution"]["signing"] == "unsigned"
    for entry in manifest["sources"]:
        if entry["status"] == "pinned":
            validate_pinned(entry)


def test_unresolved_entries_remain_visible():
    manifest = load_manifest("legal/source-manifest.json")
    unresolved = unresolved_sources(manifest)
    assert unresolved == []


def test_rejects_invalid_source_hash():
    with pytest.raises(ValueError, match="invalid SHA-256"):
        validate_pinned(
            {
                "name": "example",
                "version": "1",
                "filename": "example.tar.gz",
                "url": "https://example.invalid/example.tar.gz",
                "sha256": "bad",
            }
        )


def test_rejects_malformed_manifest(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"schema": 2, "sources": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        load_manifest(path)
