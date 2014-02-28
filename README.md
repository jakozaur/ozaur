ozaur
=====

# Setup

1. virtualenv env
2. pip install -r requirements.txt # You may need to redo after requirements.txt get updated
3. Create config.py (look at config.sample.py)
3. Launch postgresapp (Postgres93)
4. Open psql and type: CREATE DATABASE ozaur;

# Before each session

1. source env/bin/activate
2. Launch postgresapp (Postgres93)
3. python database.py create


# Usual workflow

## Get the code

git pull --rebase

# How to run website locally

python views.py

# Useful tools
http://postgresapp.com/


