"""Fetch every dataset declared in datasets.toml into data/.

Each [datasets.NAME] table in datasets.toml (at the repo root) declares one
dataset; see that file's header comment for the full set of keys. Raw files
land under data/raw/, cleaned artifacts under data/clean/, and intermediate
downloads under data/cache/.

Usage:
    uv run data/fetch.py               # list datasets and their status
    uv run data/fetch.py NAME [...]    # fetch specific datasets
    uv run data/fetch.py --all         # fetch everything
    uv run data/fetch.py --all --force # refetch even if already present
    uv run data/fetch.py --credits     # print Markdown citations for the README

Every successful fetch records the output's sha256 in datasets.lock
(committed), so collaborators can verify they work from byte-identical data.
"""

import argparse
import hashlib
import json
import os
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import pooch
import transforms
from dotenv import load_dotenv

DATA_ROOT = Path(__file__).resolve().parent
REPO_ROOT = DATA_ROOT.parent
CATALOG_PATH = REPO_ROOT / "datasets.toml"
LOCK_PATH = REPO_ROOT / "datasets.lock"
CACHE_DIR = DATA_ROOT / "cache"


def load_catalog() -> dict[str, dict]:
    with open(CATALOG_PATH, "rb") as f:
        return tomllib.load(f).get("datasets", {})


def load_lock() -> dict[str, dict]:
    if LOCK_PATH.exists():
        return json.loads(LOCK_PATH.read_text())
    return {}


def save_lock(lock: dict[str, dict]) -> None:
    LOCK_PATH.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_name(spec: dict, url: str) -> str:
    """Filename for the intermediate download in data/cache/."""
    if spec.get("download_name"):
        return spec["download_name"]
    return url.rsplit("/", 1)[-1].split("?", 1)[0] or Path(spec["output_path"]).name


def _record(
    lock: dict[str, dict], name: str, spec: dict, out: Path, retrieved: str | None
) -> None:
    """Pin the materialized output in the lockfile.

    retrieved=None means the file was already on disk (manual, or fetched before
    locking existed), so its mtime is the best fetch-date estimate. The recorded
    source_url keeps any {key} placeholder unformatted so secrets never land in
    the lockfile.
    """
    if retrieved is None:
        retrieved = (
            datetime.fromtimestamp(out.stat().st_mtime, tz=UTC).date().isoformat()
        )
    lock[name] = {
        "output_path": spec["output_path"],
        "retrieved": retrieved,
        "sha256": _sha256(out),
        "source_url": spec.get("source_url"),
    }


def fetch(name: str, spec: dict, lock: dict[str, dict], force: bool = False) -> str:
    """Materialize one dataset; returns a status string for the summary line."""
    out = DATA_ROOT / spec["output_path"]

    if spec.get("manual"):
        if not out.exists():
            print(spec.get("instructions", f"Place the file at {out} by hand."))
            return "missing"
        if name not in lock or force:
            _record(lock, name, spec, out, retrieved=None)
        return "cached"

    if out.exists() and not force:
        if name not in lock:
            _record(lock, name, spec, out, retrieved=None)
        return "cached"

    url = spec["source_url"]
    if spec.get("requires_key"):
        key_env = spec.get("key_env", "API_KEY")
        key = os.environ.get(key_env)
        if not key:
            print(spec.get("instructions", f"Set {key_env} in your .env file."))
            return "missing"
        url = url.format(key=key)

    if force:
        out.unlink(missing_ok=True)
        (CACHE_DIR / _download_name(spec, url)).unlink(missing_ok=True)

    known_hash = f"sha256:{spec['sha256']}" if spec.get("sha256") else None
    out.parent.mkdir(parents=True, exist_ok=True)

    transform_name = spec.get("transform")
    if transform_name:
        transform = getattr(transforms, transform_name)
        src = pooch.retrieve(
            url,
            known_hash=known_hash,
            fname=_download_name(spec, url),
            path=CACHE_DIR,
            progressbar=True,
        )
        transform(Path(src), out)
        if not out.exists():
            raise FileNotFoundError(
                f"transform {transform_name!r} did not produce {out}"
            )
    else:
        pooch.retrieve(
            url,
            known_hash=known_hash,
            fname=out.name,
            path=out.parent,
            progressbar=True,
        )

    _record(lock, name, spec, out, retrieved=datetime.now(tz=UTC).date().isoformat())
    return "fetched"


def credits_markdown(catalog: dict[str, dict]) -> str:
    """One Markdown citation bullet per dataset, for the README's Data Set section."""
    lines = []
    for name, spec in sorted(catalog.items()):
        prov = spec.get("provenance", {})
        entry = f"**{prov.get('title', name)}**"
        if prov.get("year"):
            entry += f" ({prov['year']})"
        url = prov.get("source_url", spec.get("source_url"))
        if url:
            entry += f", <{url}>"
        if prov.get("license"):
            entry += f", {prov['license']}"
        if prov.get("notes"):
            entry += f". {prov['notes']}"
        lines.append(f"- {entry}")
    return "\n".join(lines)


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "names", nargs="*", help="datasets to fetch (default: list status)"
    )
    parser.add_argument(
        "--all", action="store_true", help="fetch every declared dataset"
    )
    parser.add_argument(
        "--force", action="store_true", help="refetch even if already present"
    )
    parser.add_argument(
        "--credits", action="store_true", help="print Markdown citations and exit"
    )
    args = parser.parse_args()

    catalog = load_catalog()
    if args.credits:
        print(credits_markdown(catalog))
        return 0
    if not catalog:
        print("No datasets declared yet: add [datasets.NAME] tables to datasets.toml.")
        return 0

    if not args.names and not args.all:
        for name, spec in sorted(catalog.items()):
            status = (
                "present" if (DATA_ROOT / spec["output_path"]).exists() else "missing"
            )
            print(
                f"[{status:>7}] {name}: {spec.get('description', spec['output_path'])}"
            )
        print("\nFetch with: uv run data/fetch.py --all (or name one or more datasets)")
        return 0

    names = sorted(catalog) if args.all else args.names
    unknown = [n for n in names if n not in catalog]
    if unknown:
        parser.error(
            f"unknown dataset(s): {', '.join(unknown)}; run with no arguments to list"
        )

    lock = load_lock()
    failures = 0
    for name in names:
        try:
            status = fetch(name, catalog[name], lock, force=args.force)
        # Broad catch by design: one bad dataset shouldn't stop the remaining fetches.
        except Exception as exc:  # noqa: BLE001
            status = "error"
            print(f"{name}: {exc}")
        if status in ("missing", "error"):
            failures += 1
        print(f"[{status:>7}] {name}")
    save_lock(lock)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
