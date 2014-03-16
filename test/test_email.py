import os

os.environ["OZAUR_DB_URL"] = "sqlite://" # in memory

import unittest
from mock import Mock

from database import create_schema, delete_schema, db, Email, User, EmailArchive
from ozaur.email import Responder, Sender


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
    self.assertEqual(len(sender.send_welcome_email.call_args_list), 1)

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


class TestSender(unittest.TestCase):
  def setUp(self):
    create_schema()

  def tearDown(self):
    delete_schema()

  def test_invitation_email(self):
    user = User(email = "user@example.com", display_name = "First Last")
    db.session.add(user)
    db.session.commit()
    sender = Sender()
    sender._send_email = Mock()
    sender.send_invitation_email(user)
    self.assertEqual(len(user.active_emails), 1)
    self.assertEqual(len(sender._send_email.call_args_list), 1)
    email = user.active_emails[0]
    args, kwargs = sender._send_email.call_args
    self.assertIn(email.email_hash, args[-1])


if __name__ == '__main__':
  unittest.main()


