from database import db, Bid, Payout
from email import Sender

class Trader(object):
  """Controls Bid/Transaction logic. Checks ACL."""
  def __init__(self, sender):
    self.sender = sender

  def bid(self, buyer_user, seller_user, value_satoshi, coinbase_order = "TODO"):
    bid = Bid(value_satoshi = value_satoshi, coinbase_order = coinbase_order)
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
    if buyer_user.id != transaction.buyer_user_id:
      raise Exception("Invalid user tries to answer the question")

    if transaction.status != "wait_for_question":
      raise Exception("Question was already asked")

    transaction.status = "wait_for_answer"
    db.session.add(transaction)
    db.session.commit()

    self.sender.send_answer_email(transaction, question)

  def question_answered(self, seller_user, transaction, answer):
    if seller_user.id != transaction.seller_user_id:
      raise Exception("Invalid user tries to answer the question")

    if transaction.status != "wait_for_answer":
      raise Exception("Question was already answered")

    transaction.status = "success"
    payout = Payout(user_id = transaction.seller_user_id,
        value_satoshi = transaction.value_satoshi)
    transaction.payouts.append(payout)
    db.session.add(transaction)
    db.session.add(payout)
    db.session.commit()

    self.sender.send_result_email(transaction, answer)
