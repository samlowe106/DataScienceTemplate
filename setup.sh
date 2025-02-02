python -m venv venv
source venv/bin/activate

#apt install pipx -y
#pipx ensurepath
#pipx install poetry

poetry init
# Additional dependencies should be added below!
poetry add matplotlib notebook pandas scikit-learn seaborn tensorflow torch
poetry install

mkdir data
rm setup.sh