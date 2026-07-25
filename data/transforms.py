"""Post-download transforms, referenced by name from datasets.toml.

A transform turns the file pooch downloaded into the analysis-ready artifact
named by the catalogue entry's output_path. Every transform has the signature
(src, out): read the download at src (in data/cache/) and write the result to
out. This is where per-source cleaning lives: add one function per messy data
set, e.g. a pandas read + tidy + to_parquet.
"""

import zipfile
from pathlib import Path


def unzip(src: Path, out: Path) -> None:
    """Extract the whole archive into out's directory.

    out should name one of the extracted files; fetch.py uses it to tell
    whether the dataset is present.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src) as archive:
        archive.extractall(out.parent)
