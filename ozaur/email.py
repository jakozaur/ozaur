import requests

import config

from main import app
from database import db, Email, User
from hasher import random_email_hash


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
        self.sender.send_welcome_email(user)
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

    app.logger.info("User '%s', action '%s', status '%s'" % (user.email, matched_email.purpose, status))

    if ok:
      archive = matched_email.to_archive(status)
      db.session.delete(matched_email)
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

    previous_email = Email.query.filter(Email.to_user_id == user.id, Email.purpose == "verify").first()
    if previous_email:
      app.logger.warn("We already sent email to '%s'" % (user.email))
      return

    email = Email(to_user_id = user.id,
      email_hash = random_email_hash(), # We need it b/c we use it before commit
      purpose = "verify")

    db.session.add(email) 
    if self._send_email(user, "Join the Ozaur! Buy and sell attention using bitcoins.", """
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
    self._send_email(user, "Welcome the awesome human!", """
      Thanks again joining Ozaur! Let me explain quickly, how it all works: 
      1. Your profile on Ozaur has just been created using your LinkedIn data. 
      We do not display any of your contact info. 
      2. Now you can go ahead and browse the others profiles.
       On each profile you will see, how much bitcoins people are willing to pay for this user attention. 
      3. Interested in somebody's attention and want to bid? 
      First you need to have this amount of bitcoins on your account. Simply: ("TODO: Jacek!!!!!!")
      4. Simply type how much you want to pay for user attention. 
      5. Now this amount of bitcoins is freezed on your account. It means, that you can not use it, until auction is solved.
      It is solved every week on Tuesday at 2pm PST. 
      6. If you bidded with the biggest amount of bitcoins - you are the winner! Go ahead and send an email to this user via Ozaur. 
      7. User whose attention you won has 48 hours to respond to you. Done the job? You are charged. Not responded? Monay are active again on your account.
      8. Remember - people will be bidding on your profile as well! When got weekly email from winner, try to respond nicely and withing 48 hours. 
      Therefore bitcoins will land on your account:)

    Questions? Ask us anything using this email.

    Enjoy!

    Your truly, 
    Ozaur 
      """)

  def send_question_email(self, transaction):
    """
    Hi there,

    Congratulations! You have just winned another user attention. You are now allowed to write this person an email.
    Please, try to do that within next 48 hours. 
    Simply go ahead and respond to this email with your message. 
    We will securely pass it to the right user.

    This person also will try to respond within 48 hours. 
    You will be charged only if you got the answer.

    Stay tuned!

    Yours truly,
    Ozaur

    """
    pass # TODO: implement

process_incoming_email = Responder(Sender()).process_email









