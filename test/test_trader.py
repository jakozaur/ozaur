import os

os.environ["OZAUR_DB_URL"] = "sqlite://" # in memory
os.environ["OZAUR_DB_DEBUG"] = "false"

import unittest
from mock import Mock

from database import create_schema, delete_schema, db, User, Bid, Transaction
from ozaur.trader import Trader


class TestTrader(unittest.TestCase):
  def setUp(self):
    create_schema()
    self.sender = Mock()
    self.trader = Trader(self.sender)
    self.buyer = User(email = "buyer@example.com", display_name = "Buyer")
    self.seller = User(email = "seller@example.com", display_name = "Seller")
    db.session.add(self.buyer)
    db.session.add(self.seller)
    db.session.commit()

  def tearDown(self):
    delete_schema()

  def test_bid_accept(self):
    self.trader.bid(self.buyer, self.seller, 100)

    self.assertEquals(len(self.seller.seller_bid), 1)
    self.assertEquals(len(self.buyer.buyer_bid), 1)
    self.assertEquals(len(self.seller.seller_transaction), 0)
    self.assertEquals(len(self.buyer.buyer_transaction), 0)

    self.trader.accept_bid(self.seller, self.seller.seller_bid[0])

    self.assertEquals(len(self.seller.seller_bid), 0)
    self.assertEquals(len(self.buyer.buyer_bid), 0)
    self.assertEquals(len(self.seller.seller_transaction), 1)
    self.assertEquals(len(self.buyer.buyer_transaction), 1)

  def test_bid_accept_permissions(self):
    self.trader.bid(self.buyer, self.seller, 100)

    fail = False
    try:
      self.trader.accept_bid(self.buyer, self.seller.seller_bid[0])
    except:
      fail = True

    self.assert_(fail)
    self.assertEquals(len(self.seller.seller_bid), 1)
    self.assertEquals(len(self.seller.seller_transaction), 0)

  def test_bid_accept_email(self):
    self.trader.bid(self.buyer, self.seller, 100)
    self.trader.accept_bid(self.seller, self.seller.seller_bid[0])
    transaction = self.seller.seller_transaction[0]
    self.sender.send_question_email.assert_called_with(transaction)

  def test_question_asked_permissions(self):
    self.trader.bid(self.buyer, self.seller, 100)
    self.trader.accept_bid(self.seller, self.seller.seller_bid[0])
    fail = False
    try:
      self.trader.question_asked(self.seller, self.seller.seller_transaction[0], "Why?")
    except:
      fail = True
    self.assert_(fail)

  def test_question_asked_double(self):
    self.trader.bid(self.buyer, self.seller, 100)
    self.trader.accept_bid(self.seller, self.seller.seller_bid[0])
    fail = False
    try:
      self.trader.question_asked(self.buyer, self.buyer.buyer_transaction[0], "Why?")
      self.trader.question_asked(self.buyer, self.buyer.buyer_transaction[0], "Why?")
    except:
      fail = True
    self.assert_(fail)

  def test_question_asked(self):
    self.trader.bid(self.buyer, self.seller, 100)
    self.trader.accept_bid(self.seller, self.seller.seller_bid[0])
    self.trader.question_asked(self.buyer, self.buyer.buyer_transaction[0], "Why?")

    self.assertEquals(len(self.buyer.buyer_transaction), 1)
    transaction = self.buyer.buyer_transaction[0]
    self.assertEquals(transaction.status, "wait_for_answer")
    self.sender.send_answer_email.assert_called_with(transaction, "Why?")


if __name__ == '__main__':
  unittest.main()


