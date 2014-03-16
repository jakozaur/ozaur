import os

DB_URL = os.environ.get("OZAUR_DB_URL", "(db url)")
DB_DEBUG_ECHO = os.environ.get("OZAUR_DB_DEBUG", "false").lower() == "true"
APP_DEBUG = os.environ.get("OZAUR_APP_DEBUG", "false").lower() == "true"

SECRET_KEY = os.environ.get("OZAUR_APP_SECRET", "5f627d297474ec984dfab25b763485ae")

MAILGUN_API_KEY = os.environ.get("OZAUR_MAILGUN_API_KEY", "(none)")
MAILGUN_DOMAIN = os.environ.get("OZAUR_MAILGUN_DOMAIN", "(none)")

MAX_BID_SATOSHI = 10 ** 7 # 0.1 Bitcoin


# For AWS Beanstalk
if "RDS_HOSTNAME" in os.environ:
  DB_URL = "postgresql://%s:%s@%s:%s/%s" % (
      os.environ['RDS_USERNAME'],
      os.environ['RDS_PASSWORD'],
      os.environ['RDS_HOSTNAME'],
      os.environ['RDS_PORT'],
      os.environ['RDS_DB_NAME'])

# Constants
SATOSHI_IN_MICRO = 100


