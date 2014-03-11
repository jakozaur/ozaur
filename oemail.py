import requests

import config
from main import app
from database import db, Email


class Responder(object):
  def __init__(self, sender):
    self.sender = sender

  def process_email(self, recipient, body, response):
    address_hash = recipient.split("@")[0]
    user = User.query.filter(User.address_hash == address_hash).first()

    if not user:
      app.logger.warn("Unknown user [To=%s]" % (recipient))
      return

    app.logger.info("Processing emails from user '%s', waiting for (%s)" % (
      user.email,
      ", ".join([e.purpose for e in user.active_emails])))

    matched_emails = filter(lambda e: e.email_hash in body, user.active_emails)

    if len(matched_emails) == 0:
      app.logger.warn("Email reply from user '%s' doesn't match any expected emails: '%s'" % (user.email, body))
      # TODO: sent to support ?
      return

    matched_email = matched_emails[0]
    if len(matched_emails) > 1:
      app.logger.warn("Email from user '%s' matches multiple expected emails: %s" % (
        user.email,
        ", ".join(map(lambda x: str(x), matched_emails))))
      # we can keep going


    def do_verify():
      if "JOIN OZAUR" in response.upper():
        user.active = True
        # TODO: send welcome letter
        return True, "joined us!"
      else:
        return False, "'%s' doesn't have JOIN OZAUR!"

    def do_ask():
      # TODO: change the status of email!
      return True, "question asked!"

    def do_respond():
      # TODO: close the transaction
      return True, "response given!"

    def do_survey():
      # TODO: redirect to support!
      return True, "survey response given!"

    actions = {
      "verify": do_verify,
      "ask": do_ask,
      "respond": do_respond,
      "survey": do_survey
    }

    if matched_email.purpose not in actions:
      app.logger.error("Unknown purpose '%s'" % (matched_email.purpose))
      return

    ok, status = actions[matched_email.purpose]()

    app.logger.info("User '%s', action '%s', status '%s'" % (self.user.email, self.matched_email.purpose, status))

    if self.ok:
      archive = self.matched_email.to_archive(status)
      db.session.delete(self.matched_email)
      db.session.add(archive)
      db.session.commit()



class Sender(object):
  def __init__(self):
    self.api_key = config.MAILGUN_API_KEY
    self.domain = config.MAILGUN_DOMAIN

  def _send_email(self, user, subject, body):
    response = requests.post(
        "https://api.mailgun.net/v2/%s/messages" % (self.domain),
        auth=("api", self.api_key),
        data={"from": "Ozaur messenger <%s@%s>" % (
              user.address_hash, self.domain),
            "to": [user.email],
            "subject": subject,
            "text": body})
    if response.ok:
      app.logger.info("Email sent to '%s', subject '%s'" % (user.email, subject))
    else:
      app.logger.error("Couldn't sent email to '%s', subject '%s' reason '%s'" % (user.email, subject, response.text))
    return response.ok


  def send_invitation_email(self, user):
    if user.active:
      app.logger.warn("User '%s' is already activate" % (user.email))
      return

    previous_email = Email.query.filter(Email.to_user_id == self.user.id, Email.purpose == "verify").first()
    if previous_email:
      app.logger.warn("We already sent email to '%s'" % (user.email))
      return

    email = Email(to_user_id = self.user.id,
      purpose = "verify")

    db.session.add(email) 
    if self._send_email(user, "Join the Ozaur! (meaningful email/earn bitcon on each email)", """
Welcome %(name)s!

You're about to join revolution!

If you have registered, please confirm by replying "JOIN OZAUR" to this email.
If you don't reply we can't proceed further.

Yours truly,
Ozaur

PS: If you didn't register to Ozaur, please ignore this message.

Hash: %(hash)s (please don't remove it)
""" % {"name": user.display_name, "hash": email.email_hash }):
      db.session.commit()
    else:
      db.session.rollback()

  def send_welcome_email(self, user):
    self._send_email(user, "Welcome the awesome human!", """TODO: explain how Ozaur works""")
    pass
 

process_email = Responder(Sender()).process_email
