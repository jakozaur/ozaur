from database import db, Bid
from email import Sender

class Trader(object):
  def __init__(self, sender):
    self.sender = sender

  def bid(self, buyer_user, seller_user, value_satoshi):
    bid = Bid(value_satoshi = value_satoshi, coinbase_order = "TODO")
    bid.buyer = buyer_user
    bid.seller = seller_user
    db.session.add(bid)
    db.session.commit()
    return True

trader = Trader(Sender())
