ozaur
=====

# Setup

1. virtualenv env
2. pip install -r requirements.txt # You may need to redo after requirements.txt get updated
3. Create config.py (look at config.sample.py)
3. Install AWS Elastic Beanstalk Command Line Tool:
  brew install aws-elasticbeanstalk
  http://aws.amazon.com/code/6752709412171743
3. Launch postgresapp (Postgres93)
4. Open psql and type: CREATE DATABASE ozaur;

## Setup staging environment

1. eb init
2. Enter keys (ask Jacek)
3. Region: Oregon
4. Application name: ozaur
5. Environment name: Default-Environment
6. Tier: WebServer 1
7. 20) 64bit Amazon Linux 2013.09 running Python 2.7
8. SingleInstancegt

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

Authors: Jacek Migdal, Gosia Migdal


