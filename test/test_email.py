import os

os.environ["OZAUR_DB_URL"] = "sqlite://" # in memory
os.environ["OZAUR_DB_DEBUG"] = "false"

import unittest
from mock import Mock

from database import create_schema, delete_schema, db, Email, User, EmailArchive, Transaction
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
    self.user = User(email = "user@example.com", display_name = "First Last")
    self.another_user = User(email = "another@example.com", display_name = "Yet another User")
    db.session.add(self.user)
    db.session.add(self.another_user)
    db.session.commit()
    self.sender = Sender()
    self.sender._send_email = Mock()

  def tearDown(self):
    delete_schema()

  def test_invitation_email(self):
    self.sender.send_invitation_email(self.user)
    self.assertEqual(len(self.user.active_emails), 1)
    self.assertEqual(len(self.sender._send_email.call_args_list), 1)
    email = self.user.active_emails[0]
    args, kwargs = self.sender._send_email.call_args
    self.assertIn(email.email_hash, args[-1])

  def test_welcome_email(self):
    self.sender.send_welcome_email(self.user)
    self.assertEqual(len(self.user.active_emails), 0)
    self.assertEqual(len(self.sender._send_email.call_args_list), 1)
    args, kwargs = self.sender._send_email.call_args
    self.assertIn("welcome", args[-2].lower())

  def test_question_email(self):
    transaction = Transaction(bid_id_old = 42,
        bid_created_at = self.user.created_at,
        buyer_user_id = self.user.id,
        seller_user_id = self.another_user.id,
        value_satoshi = 100,
        coinbase_order = "unknown",
        status = "wait_for_question")
    db.session.add(transaction)
    db.session.commit()
    self.sender.send_question_email(transaction)
    self.assertEqual(len(self.user.active_emails), 1)
    self.assertEqual(len(self.another_user.active_emails), 0)
    self.assertEqual(len(self.sender._send_email.call_args_list), 1)
    email = self.user.active_emails[0]
    args, kwargs = self.sender._send_email.call_args
    self.assertIn(email.email_hash, args[-1])
    self.assertEqual(args[0], self.user)


if __name__ == '__main__':
  unittest.main()


