"""Offline tests for the dataset registry (data/fetch.py and data/transforms.py).

pytest puts data/ on the path (pythonpath in pyproject.toml), so the registry
modules import directly. Nothing here touches the network: download behaviour
is pooch's responsibility, and these tests cover the logic around it.
"""

import json
import zipfile

import fetch
import transforms


def test_download_name_prefers_explicit() -> None:
    spec = {"download_name": "renamed.csv", "output_path": "raw/x/data.zip"}
    assert (
        fetch._download_name(spec, "https://example.com/archive.zip") == "renamed.csv"
    )


def test_download_name_from_url_strips_query() -> None:
    spec = {"output_path": "raw/x/data.bin"}
    url = "https://example.com/files/archive.zip?token=abc"
    assert fetch._download_name(spec, url) == "archive.zip"


def test_manual_dataset_missing_prints_instructions(
    tmp_path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(fetch, "DATA_ROOT", tmp_path)
    spec = {
        "manual": True,
        "output_path": "raw/hand.csv",
        "instructions": "Get it from the portal.",
    }
    assert fetch.fetch("hand", spec, lock={}) == "missing"
    assert "Get it from the portal." in capsys.readouterr().out


def test_manual_dataset_present_is_recorded(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fetch, "DATA_ROOT", tmp_path)
    out = tmp_path / "raw" / "hand.csv"
    out.parent.mkdir(parents=True)
    out.write_text("a,b\n1,2\n")
    lock: dict[str, dict] = {}
    assert (
        fetch.fetch("hand", {"manual": True, "output_path": "raw/hand.csv"}, lock)
        == "cached"
    )
    assert lock["hand"]["sha256"] == fetch._sha256(out)


def test_missing_key_prints_instructions(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(fetch, "DATA_ROOT", tmp_path)
    monkeypatch.delenv("SOME_TEST_KEY", raising=False)
    spec = {
        "source_url": "https://example.com/data?key={key}",
        "output_path": "raw/keyed.json",
        "requires_key": True,
        "key_env": "SOME_TEST_KEY",
        "instructions": "Set SOME_TEST_KEY in .env",
    }
    assert fetch.fetch("keyed", spec, lock={}) == "missing"
    assert "Set SOME_TEST_KEY in .env" in capsys.readouterr().out


def test_existing_output_is_cached_and_locked(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fetch, "DATA_ROOT", tmp_path)
    out = tmp_path / "raw" / "present.csv"
    out.parent.mkdir(parents=True)
    out.write_text("data")
    lock: dict[str, dict] = {}
    spec = {
        "source_url": "https://example.com/present.csv",
        "output_path": "raw/present.csv",
    }
    assert fetch.fetch("present", spec, lock) == "cached"
    assert lock["present"]["source_url"] == "https://example.com/present.csv"


def test_lock_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(fetch, "LOCK_PATH", tmp_path / "datasets.lock")
    lock = {
        "name": {"sha256": "abc", "output_path": "raw/x", "retrieved": "2026-07-24"}
    }
    fetch.save_lock(lock)
    assert fetch.load_lock() == lock
    assert json.loads((tmp_path / "datasets.lock").read_text()) == lock


def test_credits_markdown_renders_provenance() -> None:
    catalog: dict[str, dict] = {
        "acs": {
            "source_url": "https://api.census.gov/data/2023/acs/acs5",
            "output_path": "raw/acs.json",
            "provenance": {
                "title": "ACS 5-Year Estimates",
                "source_url": "https://www.census.gov/programs-surveys/acs",
                "year": 2023,
                "license": "Public domain",
                "notes": "Tract-level tables.",
            },
        },
        "plain": {
            "source_url": "https://example.com/d.csv",
            "output_path": "raw/d.csv",
        },
    }
    md = fetch.credits_markdown(catalog)
    assert "**ACS 5-Year Estimates** (2023)" in md
    assert "<https://www.census.gov/programs-surveys/acs>" in md
    assert "Public domain" in md
    assert "Tract-level tables." in md
    # A dataset with no provenance table falls back to its name and download URL.
    assert "**plain**, <https://example.com/d.csv>" in md


def test_unzip_extracts_into_output_directory(tmp_path) -> None:
    src = tmp_path / "archive.zip"
    with zipfile.ZipFile(src, "w") as archive:
        archive.writestr("table.csv", "a,b\n1,2\n")
        archive.writestr("readme.txt", "hello")
    out = tmp_path / "raw" / "example" / "table.csv"
    transforms.unzip(src, out)
    assert out.read_text() == "a,b\n1,2\n"
    assert (out.parent / "readme.txt").exists()
