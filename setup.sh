#python -m venv .venv
#source venv/bin/activate
pyenv local 3.14

#apt install pipx -y
#pipx ensurepath
#pipx install poetry

poetry init
# only installing top level dependencies -- numpy, pandas, matplotlib are included
# Additional dependencies should be added below!

poetry add notebook geopandas geopy scikit-learn seaborn tensorflow tensorflow-datasets torch pre-commit
poetry install

pre-commit autoupdate
pre-commit install

mkdir data/raw
mkdir data/clean

rm setup.sh
