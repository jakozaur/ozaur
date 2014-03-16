ozaur
=====

# Setup

## Development environment

1. virtualenv env
2. pip install -r requirements.txt # You may need to redo after requirements.txt get updated
3. Append config to env/bin/activate:
```
    # Ozaur app settings
    export OZAUR_DB_URL="postgresql://jakozaur@localhost/ozaur"
    export OZAUR_DB_DEBUG="TRUE"
    export OZAUR_APP_DEBUG="TRUE"
    
    export OZAUR_MAILGUN_API_KEY="[[SOME KEY]]"
    export OZAUR_MAILGUN_DOMAIN="sandbox35839.mailgun.org"
```

4. Install postgresapp
5. Launch postgresapp (Postgres93)
6. Open psql and type: CREATE DATABASE ozaur;

## Setup staging environment

1. Install AWS Elastic Beanstalk Command Line Tool:
  brew install aws-elasticbeanstalk
  http://aws.amazon.com/code/6752709412171743
2. eb init
2. Enter keys (ask Jacek)
3. Region: Oregon
4. Application name: ozaur
5. Environment name: ozaur-dev
6. Tier: WebServer 1
7. 20) 64bit Amazon Linux 2013.09 running Python 2.7
8. SingleInstance

# Before each session

1. source env/bin/activate
2. Launch postgresapp (Postgres93)
3. python database.py create


# Usual workflow

## Get the code

git pull --rebase

# How to run website locally

python views.py

# Nice to have

1. Just show top N bds
2. Show names of people you bid on.
3. Reimport LinkedIn.
4. Active transactions.
5. Link to profile in ask question email.

# Security TODO

# Milestones

1. 2014-03-16 1:11 AM PST (first full transaction)

# Useful tools
http://postgresapp.com/

Authors: Jacek Migdal, Gosia Migdal


