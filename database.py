from sqlalchemy import create_engine, Column, Integer, BigInteger, \
   Enum, Boolean, String, Index, ForeignKey, Text, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy

from main import app
import config
from ozaur.hasher import random_address_hash, random_email_hash

app.config["SQLALCHEMY_DATABASE_URI"] = config.DB_URL
app.config["SQLALCHEMY_ECHO"] = config.DB_DEBUG_ECHO

db = SQLAlchemy(app)

class TimeMixin(object):
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ValueMixin(object):
  value_satoshi = Column(BigInteger, nullable=False)

  def value_micro(self):
    return self.value_satoshi / config.SATOSHI_IN_MICRO


class User(db.Model, UserMixin, TimeMixin):
  __tablename__ = "user"

  id = Column(Integer, primary_key=True, autoincrement=True)
  email = Column(String(256), nullable=False)
  active = Column(Boolean, nullable=False, default=False)
  address_hash = Column(String(40), default=random_address_hash, nullable=False)
  display_name = Column(String(64), nullable=False)
  headline = Column(String(128), default="Yet another human", nullable=False)
  industry = Column(String(64), default="Communication", nullable=False)
  location = Column(String(64), default="Earth", nullable=False)
  interested_in = Column(String(256), default="Earning bitcoins", nullable=False)
  photo_url = Column(String(256))

  __table_args__ = (Index("user_email_idx", "email", unique=True),
    Index("user_address_hash_idx", "address_hash", unique=True),)


class Profile(db.Model, TimeMixin):
  __tablename__ = "profile"

  id = Column(Integer, primary_key=True, autoincrement=True)
  user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

  external_key = Column(String(128))
  data_json = Column(Text)

  user = relationship("User", backref="profiles")

  __table_args__ = (Index("profile_user_id_idx", "user_id"),)


class Bid(db.Model, ValueMixin, TimeMixin):
  __tablename__ = "bid"

  id = Column(Integer, primary_key=True, autoincrement=True)
  buyer_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  seller_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  coinbase_order = Column(String(64), nullable=False)

  buyer = relationship("User", foreign_keys=[buyer_user_id], backref="buyer_bid")
  seller = relationship("User", foreign_keys=[seller_user_id], backref="seller_bid")

  __table_args__ = (Index("bid_buyer_user_id_idx", "buyer_user_id"), Index("bid_seller_user_id_idx", "seller_user_id"),)

  def to_transaction(self):
    return Transaction(bid_id_old = self.id,
      bid_created_at = self.created_at,
      buyer_user_id = self.buyer_user_id,
      seller_user_id = self.seller_user_id,
      coinbase_order = self.coinbase_order,
      value_satoshi = self.value_satoshi,
      status = "wait_for_question")


class Transaction(db.Model, ValueMixin, TimeMixin):
  __tablename__ = "transaction"

  id = Column(Integer, primary_key=True, autoincrement=True)
  bid_id_old = Column(Integer, nullable=False)
  bid_created_at = Column(DateTime, nullable=False)
  buyer_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  seller_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  coinbase_order = Column(String(64), nullable=False)
  status = Column(Enum("wait_for_question", "wait_for_answer", "success", "timeout_on_question", "timeout_on_answer",
    name="transaction_status_type"), nullable=False)

  buyer = relationship("User", foreign_keys=[buyer_user_id], backref="buyer_transaction")
  seller = relationship("User", foreign_keys=[seller_user_id], backref="seller_transaction")

  __table_args__ = (Index("transaction_buyer_user_id_idx", "buyer_user_id"),
      Index("transaction_seller_user_id_idx", "seller_user_id"),
      Index("transaction_bid_id_old", "bid_id_old", unique=True))


class Payout(db.Model, ValueMixin, TimeMixin):
  __tablename__ = "payout"

  id = Column(Integer, primary_key=True, autoincrement=True)
  transaction_id = Column(Integer, ForeignKey("transaction.id"), nullable=False)
  user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  paid_date = Column(DateTime)
  is_paid = Column(Boolean, nullable=False, default=False)

  user = relationship("User", backref="payouts")
  transaction = relationship("Transaction", backref="payouts")

  __table_args__ = (Index("payout_user_id_idx", "user_id"), Index("payout_transaction_id_idx", "transaction_id"),)


email_purpose_type = Enum("verify", "ask", "answer", "survey", name="email_purpose_type")

class Email(db.Model, TimeMixin):
  __tablename__ = "email"

  id = Column(Integer, primary_key=True, autoincrement=True)
  to_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  transaction_id = Column(Integer, ForeignKey("transaction.id"))
  email_hash = Column(String(64), default=random_email_hash, nullable=False)
  purpose = Column(email_purpose_type, nullable=False)

  user = relationship("User", backref="active_emails")
  transaction = relationship("Transaction", backref="active_emails")

  __table_args__ = (Index("email_to_user_id_idx", "to_user_id"),
    Index("email_transaction_id_idx", "transaction_id"),
    Index("email_email_hash_idx", "email_hash", unique=True),)

  def to_archive(self, result = "OK"):
    return EmailArchive(
      to_user_id = self.to_user_id,
      transaction_id = self.transaction_id,
      email_hash = self.email_hash,
      purpose = self.purpose,
      result = result,
      email_id_old = self.id,
      email_created_at = self.created_at)

class EmailArchive(db.Model, TimeMixin):
  __tablename__ = "email_archive"

  id = Column(Integer, primary_key=True, autoincrement=True)
  transaction_id = Column(Integer, ForeignKey("transaction.id"))
  to_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
  email_hash = Column(String(64), nullable=False)
  purpose = Column(email_purpose_type, nullable=False)
  result = Column(String(128), nullable=False)

  email_id_old = Column(Integer, nullable=False)
  email_created_at = Column(DateTime, nullable=False)

  user = relationship("User", backref="archive_emails")
  transaction = relationship("Transaction", backref="archive_mails")

  __table_args__ = (Index("email_archive_to_user_id_idx", "to_user_id"),
    Index("email_archive_transaction_id_idx", "transaction_id"),
    Index("email_archive_email_hash_idx", "email_hash"),)



def create_schema():
  db.create_all()

def delete_schema():
  db.drop_all()

if __name__ == '__main__':
  from sys import argv
  if len(argv) != 2 or argv[1] not in ["create", "delete"]:
    print "Invalid argument"
    print "Please use %s create|delete" % (argv[0])
  else:
    if argv[1] == "create":
      print "Creating DB schema"
      create_schema()
    elif argv[1] == "delete":
      print "Deleting all DB tables"
      delete_schema()



