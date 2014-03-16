from database import db, Bid
from email import Sender

class Trader(object):
  """Controls Bid/Transaction logic. Checks ACL."""
  def __init__(self, sender):
    self.sender = sender

  def bid(self, buyer_user, seller_user, value_satoshi):
    bid = Bid(value_satoshi = value_satoshi, coinbase_order = "TODO")
    bid.buyer = buyer_user
    bid.seller = seller_user
    db.session.add(bid)
    db.session.commit()
    # TODO: Send email on first bid
    return True

  def accept_bid(self, seller_user, bid):
    if seller_user.id != bid.seller_user_id:
      raise Exception("Invalid user tries to accept the bid")

    transaction = bid.to_transaction()
    db.session.add(transaction)
    db.session.delete(bid)
    db.session.commit() # TODO: catch exception?
    db.session.refresh(transaction)

    self.sender.send_question_email(transaction)

  def question_asked(self, buyer_user, transaction, question):
    pass

  def question_answered(self, seller_user, transaction, answer):
    pass

trader = Trader(Sender())
