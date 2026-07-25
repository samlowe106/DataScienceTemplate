# Data Science Template

[![Run Tests](https://github.com/samlowe106/DataScienceTemplate/actions/workflows/tests.yml/badge.svg)](https://github.com/samlowe106/DataScienceTemplate/actions/workflows/tests.yml)

This is a template for a data science project in a Python Jupyter notebook. This README is mostly a template, and should be customized accordingly during project creation. Here's a checklist after making a new repository from this template:

- [ ] Run `setup.sh` (Linux/macOS): installs [uv](https://docs.astral.sh/uv/), the pinned Python, every dependency, and the pre-commit hooks
- [ ] Declare your data sets in [datasets.toml](datasets.toml): a source URL, an output path, and optionally a transform, an API key, or provenance metadata (see the file's header for all keys)
- [ ] Run `uv run data/fetch.py --all` to download everything; each artifact's sha256 is pinned in `datasets.lock` for reproducibility
- [ ] Put per-source cleaning code in [data/transforms.py](data/transforms.py), referenced by name from the catalogue

Finally:

- [ ] Run `uv run data/fetch.py --credits` and paste the output into the [data set section](#data-set) of this README
- [ ] Fill in the [license](LICENSE) and (optionally) update the [license section](#license) of this README
- [ ] Fill out or delete the [contributing section](#contributing) of this README

## Data

Data lives under `data/` but is never committed: `data/raw/` holds files as downloaded, `data/clean/` holds analysis-ready artifacts, and `data/cache/` holds intermediate downloads. Only the catalogue ([datasets.toml](datasets.toml)) and the hash lockfile (`datasets.lock`) are checked in, which is enough for anyone to rebuild the exact same data with `uv run data/fetch.py --all`.

Running `uv run data/fetch.py` with no arguments lists every declared data set and whether it's present. Data sets that need an API key read it from `.env` (created by `setup.sh`), and manual data sets print instructions telling you where to get the file.

## Data Set

The data sets can be found [here]().

## License

Please consult the [license file](LICENSE).

## Installation

Make sure you have a compatible version of Python, as specified in the [pyproject.toml file](pyproject.toml), and that you've installed [uv](https://docs.astral.sh/uv/). Then run `uv sync` to install all dependencies, and `uv run pytest` to check that everything works: tests report coverage and the slowest test durations.

## Contributing
