import requests

import config

from main import app
from database import db, Email, User
from hasher import random_email_hash


class Responder(object):
  def __init__(self, sender, trader):
    self.sender = sender
    self.trader = trader

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
      transaction = matched_email.transaction
      response_filttered = "\n".join(
        filter(lambda line: address_hash not in line,
          response.splitlines()))
      self.trader.question_asked(user, transaction, response_filttered)
      return True, "question asked!"

    def do_answer():
      transaction = matched_email.transaction
      response_filttered = "\n".join(
        filter(lambda line: address_hash not in line,
          response.splitlines()))
      self.trader.question_answered(user, transaction, response_filttered)
      return True, "response given!"

    def do_survey():
      # TODO: redirect to support!
      return True, "survey response given!"

    actions = {
      "verify": do_verify,
      "ask": do_ask,
      "answer": do_answer,
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
    if self._send_email(user, "Join the Ozaur! Buy and sell attention using bitcoin.", """
Welcome %(name)s!

You're about to join the attention marketplace!

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
How Ozaur works:

1. Interested in somebody's attention? Place a bid.
2. Each week you can get an question from other user. Please respond and we will pay you bitcoin from highest bidder.

Please be nice and be as helpful as you can.

Enjoy!

Thanks for joining,
Ozaur""")

  def send_question_email(self, transaction):
    email = Email(to_user_id = transaction.buyer.id,
      transaction_id = transaction.id,
      email_hash = random_email_hash(), # We need it b/c we use it before commit
      purpose = "ask")

    db.session.add(email)

    args = {"buyer": transaction.buyer.display_name,
        "seller": transaction.seller.display_name,
        "hash": email.email_hash }

    if self._send_email(transaction.buyer, "You won '%s' attention, ask him a question" % (transaction.seller.display_name), """
Hi %(buyer)s,

You won '%(seller)s' attention.

Ask this person a question by replying to this email.

Be concise, the question should be answerable in ~ 5 minutes.

You will get an email once we get an answer to your question.  

Thanks for buying the attention,
Ozaur

PS: Please try to write your question within 48 hours.

Hash: %(hash)s (please don't remove it)""" % args):
      db.session.commit()
    else:
      db.session.rollback()

  def send_answer_email(self, transaction, question):
    email = Email(to_user_id = transaction.seller.id,
      transaction_id = transaction.id,
      email_hash = random_email_hash(), # We need it b/c we use it before commit
      purpose = "answer")

    db.session.add(email)

    args = {"buyer": transaction.buyer.display_name,
        "seller": transaction.seller.display_name,
        "question": question,
        "hash": email.email_hash }

    if self._send_email(transaction.seller, "Answer the question from '%s', earn bitcoin!" % (transaction.buyer.display_name), """
Hi %(seller)s,

'%(buyer)s' have a question for you, please answer it by replying to this email. You will earn bitcoins for this response.

Please concentrate and try to spend at least 5 minutes on it. It is ok to decline requests, but please be as helpful as possible.

Question: '''
%(question)s
'''

Thanks for selling your attention,
Ozaur

PS: Please try to write your answer within 48 hours. Otherwise you may not earn bitcoin...

Hash: %(hash)s (please don't remove it)""" % args):
      db.session.commit()
    else:
      db.session.rollback()

  def send_result_email(self, transaction, answer):
    args = {"buyer": transaction.buyer.display_name,
        "seller": transaction.seller.display_name,
        "answer": answer }

    if self._send_email(transaction.buyer, "You got an answer from '%s'" % (transaction.seller.display_name), """
Hi %(buyer)s,

'%(seller)s' answered your question: '''
%(answer)s
'''

Thanks for tipping this user with bitcoin.

Thanks for buying the attention with us,
Ozaur""" % args):
      db.session.commit()
    else:
      db.session.rollback()










