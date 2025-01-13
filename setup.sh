apt install pipx
pipx ensurepath

pipx install poetry

poetry init
poetry add matplotlib notebook pandas scikit-learn seaborn tensorflow torch
poetry add numpy # tensorflow etc require a lower version of numpy than current release
poetry install
