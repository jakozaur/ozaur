import requests

import config

class Mailer(object):
  def __init__(self):
    self.api_key = config.MAILGUN_API_KET
    self.domain = config.MAILGUN_DOMAIN

  def send_welcome_email(self, email, name, user_email_id):
    return requests.post(
        "https://api.mailgun.net/v2/%s/messages" % (self.domain),
        auth=("api", self.api_key),
        data={"from": "Ozaur messenger <%s.messenger@%s>" % (
              user_email_id, self.domain),
            "to": [email],
            "subject": "Welcome to Ozaur! Earn bitcoins soon...",
            "text": """
Welcome %(name)s!

You're about to join revolution!

If you have registered, please confirm by replying "JOIN OZAUR" to this email.
If you don't reply we can't proceed further.

Yours truly,
Ozaur

PS: If you didn't register to Ozaur, please ignore this message.
""" % {"name": name}})

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

