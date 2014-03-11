import os

os.environ["OZAUR_DB_URL"] = "sqlite://" # in memory

import unittest
from mock import Mock

from database import create_schema, delete_schema, db, Email, User
from oemail import Responder

class TestResponder(unittest.TestCase):
  def setUp(self):
    create_schema()

  def tearDown(self):
    delete_schema()

  def test_accept_invitation(self):
    user = User(email = "user@example.com", display_name = "First Last")
    email = Email(purpose = "verify")
    user.active_emails.append(email)
    db.session.add(user)
    db.session.commit()
    sender = Mock()
    responder = Responder(sender)
    responder.process_email(user.address_hash + "@", "JOIN OZAUR; %s" % (email.email_hash), "JOIN OZAUR")

if __name__ == '__main__':
  unittest.main()


