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





if __name__ == '__main__':
  unittest.main()


