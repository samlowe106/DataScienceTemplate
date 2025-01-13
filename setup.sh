apt install pipx
pipx ensurepath

pipx install poetry

poetry init
poetry add matplotlib notebook numpy pandas scikit-learn seaborn tensorflow torch
poetry install
