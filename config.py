import os

DB_URL = os.environ.get("OZAUR_DB_URL", "(db url)")
DB_DEBUG_ECHO = os.environ.get("OZAUR_DB_DEBUG", "false").lower() == "true"
APP_DEBUG = os.environ.get("OZAUR_APP_DEBUG", "false").lower() == "true"

MAILGUN_API_KEY = os.environ.get("OZAUR_MAILGUN_API_KEY", "(none)")
MAILGUN_DOMAIN = os.environ.get("OZAUR_MAILGUN_DOMAIN", "(none)")


# For AWS Beanstalk
if "RDS_HOSTNAME" in os.environ:
  DB_URL = "postgresql://%s:%s@%s:%s/%s" % (
      os.environ['RDS_USERNAME'],
      os.environ['RDS_PASSWORD'],
      os.environ['RDS_HOSTNAME'],
      os.environ['RDS_PORT'],
      os.environ['RDS_DB_NAME'])


