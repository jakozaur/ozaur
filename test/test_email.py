import os

os.environ["OZAUR_DB_URL"] = "sqlite://" # in memory

import unittest
from mock import Mock

from database import create_schema, delete_schema, db, Email, User, EmailArchive
from ozaur.email import Responder

class TestResponder(unittest.TestCase):
  def setUp(self):
    create_schema()

  def tearDown(self):
    delete_schema()

  def create_sandbox(self):
    user = User(email = "user@example.com", display_name = "First Last")
    email = Email(purpose = "verify")
    user.active_emails.append(email)
    db.session.add(user)
    db.session.commit()
    sender = Mock()
    responder = Responder(sender)
    return user, email, sender, responder

  def test_accept_invitation(self):
    user, email, sender, responder = self.create_sandbox()
    responder.process_email(user.address_hash + "@example.com", "JOIN OZAUR; %s" % (email.email_hash), "JOIN OZAUR")
    db.session.refresh(user)
    self.assertEqual(user.active, True)
    self.assertEqual(Email.query.filter(Email.id == email.id).first(), None)
    archive = EmailArchive.query.filter(EmailArchive.email_id_old == email.id).first()
    self.assertNotEqual(archive, None)
    self.assertEqual(archive.email_hash, email.email_hash)
    sender.send_welcome_email.assert_called_once()

  def test_ignore_invalid_address(self):
    user, email, sender, responder = self.create_sandbox()
    responder.process_email("invalid@email.com", "JOIN OZAUR; %s" % (email.email_hash), "JOIN OZAUR")
    db.session.refresh(user)
    self.assertEqual(user.active, False)

  def test_ignore_invalid_hash(self):
    user, email, sender, responder = self.create_sandbox()
    responder.process_email(user.address_hash + "@example.com", "JOIN OZAUR; without code", "JOIN OZAUR")
    db.session.refresh(user)
    self.assertEqual(user.active, False)

  def test_ignore_invalid_invalid_word(self):
    user, email, sender, responder = self.create_sandbox()
    responder.process_email(user.address_hash + "@example.com", "JOIN OZAUR; without code", "not joining")
    db.session.refresh(user)
    self.assertEqual(user.active, False)



if __name__ == '__main__':
  unittest.main()


