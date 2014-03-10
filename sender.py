import requests

import config
from database import db, Email

class Sender(object):
  def __init__(self, user):
    self.api_key = config.MAILGUN_API_KEY
    self.domain = config.MAILGUN_DOMAIN
    self.user = user

  def send_welcome_email(self):
    if self.user.active:
      return # User is already active

    previous_email = Email.query.filter(Email.to_user_id == self.user.id, Email.purpose == "verify").first()
    if previous_email:
      return # Previous email was already sent

    email = Email(to_user_id = self.user.id,
      purpose = "verify")

    db.session.add(email) 
    db.session.commit()

    response = requests.post(
        "https://api.mailgun.net/v2/%s/messages" % (self.domain),
        auth=("api", self.api_key),
        data={"from": "Ozaur messenger <%s@%s>" % (
              self.user.address_hash, self.domain),
            "to": [self.user.email],
            "subject": "Welcome to Ozaur! Earn bitcoins soon...",
            "text": """
Welcome %(name)s!

You're about to join revolution!

If you have registered, please confirm by replying "JOIN OZAUR" to this email.
If you don't reply we can't proceed further.

Yours truly,
Ozaur

PS: If you didn't register to Ozaur, please ignore this message.

Hash: %(hash)s (please don't remove it)
""" % {"name": self.user.display_name, "hash": email.email_hash }})

    if not response.ok:
      pass # TODO: Do something

  def find_confirmations(self):
    emails = self.fetch_stored_emails()
    for email in emails:
      if self._is_confirmation(email):
        yield (email["recipients"], email)

  def fetch_stored_emails(self):
    response = requests.get("https://api.mailgun.net/v2/%s/events" % (self.domain),
        auth=("api", self.api_key),
        params={"event": "stored"})
    if response.ok:
      for item in  response.json()["items"]:
        url = item["storage"]["url"]
        yield requests.get(url, auth=("api", self.api_key)).json()
    else:
      raise Exception("Can't fetch emails: " + a.text)

  def _is_confirmation(self, email):
    return "JOIN OZAUR" in email["stripped-text"].upper()

