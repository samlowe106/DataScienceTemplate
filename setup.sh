#!/usr/bin/bash

set -euo pipefail

OS="$(uname -s)"

if [[ ! "$OS" == "Linux" && ! "$OS" == "Darwin" ]]; then
    echo "Unsupported OS: $OS" >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found. Installing..."

    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add uv to PATH for current shell session
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "verified $(uv --version)"
fi

# Installs the pinned Python (.python-version) and every dependency in uv.lock,
# including the dev group (pre-commit, notebook).
uv sync

# Holds API keys for gated datasets (see datasets.toml); loaded by data/fetch.py.
touch .env

# Bump hooks to their latest tags, then enable them for this clone.
uv run pre-commit autoupdate
uv run pre-commit install

rm setup.sh
