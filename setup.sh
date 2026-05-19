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

uv python pin 3.13.9 # tensorflow isn't compatible with 3.14 yet
uv init
# uv add pre-commit pytest python-dotenv
# touch .env

# only installing top level dependencies -- numpy, pandas, matplotlib are included
# Additional dependencies should be added below!
uv add geopandas geopy httpx huggingface notebook pre-commit scikit-learn seaborn tensorflow tensorflow-datasets torch

pre-commit autoupdate
pre-commit install

rm setup.sh
