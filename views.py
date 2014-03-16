# coding=utf-8

from flask import render_template, request, url_for, redirect, flash
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
import json
import requests

import config
from database import db, User, Profile, Bid, Payout
from main import app
from ozaur.email import Sender, Responder
from ozaur.trader import Trader
from coinbase import Coinbase

_sender = Sender()
trader = Trader(_sender)
process_incoming_email = Responder(_sender, trader).process_email
coinbase = Coinbase()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    return User.query.filter(User.id == userid).first()

@app.route("/")
def main_page():
  return render_template("index.html")

@app.route("/signup")
def signup():
  return render_template("signup.html")

@app.route("/login", methods=["POST"])
def login_post():
  linkedin_oauth_token = request.form["linkedin_oauth_token"]
  r = requests.get("https://api.linkedin.com/v1/people::(~):(id,email-address)",
      headers={"oauth_token": linkedin_oauth_token,
        "x-li-format": "json"})

  user = User.query.filter(User.email == r.json()["values"][0]["emailAddress"]).first()
  flash("You have log in. Welcome aboard! Who are you going to bid today?")
  login_user(user)
  return redirect(request.form["back_url"])

@app.route("/logout")
@login_required
def logout():
  flash("You have loged out successfully. Bye bye.")
  logout_user()
  return redirect(url_for("main_page"))

@app.route("/team")
def team():
  return render_template("team.html")

@app.route("/profiles", defaults={'page': 1})
@app.route("/profiles/page/<int:page>")
def profiles(page):
  pagination = User.query.paginate(page)
  return render_template("profiles.html", pagination=pagination)

@app.route("/profile/<int:id>")
def public_profile(id):
  user = User.query.filter(User.id == id).first()
  if user:
    # TODO: Change when we will have more profiles per user
    profile = user.profiles[0]

    bids = Bid.query.filter(Bid.seller_user_id == id).order_by(desc(Bid.value_satoshi)).all()

    linkedin = json.loads(profile.data_json)

    return render_template("bid_profile.html", user=user, linkedin=linkedin,
        bids=bids,
        max_bid=config.MAX_BID_SATOSHI / config.SATOSHI_IN_MICRO)
  else:
    flash("Given user profile does not exist.")
    return redirect(url_for("profiles"))

@app.route("/profile/<int:id>/bid", methods=["POST"])
@login_required
def bid_profile(id):
  user = User.query.filter(User.id == id).first()
  if not user:
    flash("Given user profile does not longer exist.")
    return redirect(url_for("profiles"))

  if "attention-bid" not in request.form or \
      not request.form["attention-bid"].isdigit() or \
      int(request.form["attention-bid"]) == 0:
    flash("Your bid value has invalid format!")
    return redirect(url_for("public_profile", id=id))

  # Micro (10^-6 to satoshi 10^-8)
  value_micro = int(request.form["attention-bid"])
  value_satoshi = value_micro * config.SATOSHI_IN_MICRO

  if value_satoshi > config.MAX_BID_SATOSHI:
    flash(u"Your bid %d μBTC is over maximal value %d μBTC." %
        (value_micro, config.MAX_BID_SATOSHI / config.SATOSHI_IN_MICRO))
    return redirect(url_for("public_profile", id=id))

  #try:
  #  trader.bid(current_user, user, value_satoshi)
  #  flash(u"You have successfully bidded %s μBTC on '%s'." % (value_micro, user.display_name))
  #except:
  #  flash(u"Your bid on '%s' was unsuccessful." % (user.display_name))

  # TODO: add urls 
  urls = {
    "callback": request.url_root[:-1] + url_for("coinbase_notification"),
    "cancel": request.url_root[:-1] + url_for("public_profile", id=id)
  }
  payment_url = coinbase.generate_payment_link(current_user, user, value_satoshi, urls)
  return redirect(payment_url)

@app.route("/create_account", methods=["POST"])
def create_account():
  linkedin_oauth_token = request.form["linkedin_oauth_token"]
  r = requests.get("https://api.linkedin.com/v1/people::(~):(id,first-name,last-name,headline,location,industry,num-connections,summary,specialties,positions,picture-url,public-profile-url,email-address,associations,interests,publications,patents,languages,skills,certifications,educations,courses,volunteer,num-recommenders,honors-awards)",
      headers={"oauth_token": linkedin_oauth_token,
        "x-li-format": "json"})

  user_json = r.json()["values"][0]

  user = User(email = user_json["emailAddress"],
      display_name = "%s %s" % (user_json["firstName"], user_json["lastName"]),
      headline = user_json["headline"],
      industry = user_json["industry"],
      location = user_json["location"]["name"],
      interested_in = "",
      photo_url = user_json["pictureUrl"]
      )

  profile = Profile(external_key = user_json["id"],
      data_json = json.dumps(user_json))

  user.profiles.append(profile)

  db.session.add(user)
  db.session.add(profile)

  try:
    db.session.commit()

    sender = Sender()
    sender.send_invitation_email(user)
  except IntegrityError, e:
    db.session.rollback()
    user = User.query.filter(User.email == user_json["emailAddress"]).first()

  login_user(user)

  return redirect(url_for("my_profile"))

@app.route("/account")
@login_required
def account():
  payouts = Payout.query.filter(Payout.user_id == current_user.id, Payout.is_paid == False).all()
  return render_template("account.html", payouts = payouts)

@app.route("/account/accept_bid", methods=["POST"])
@login_required
def accept_bid():
  bids = current_user.seller_bid
  if bids:
    best_bid = max(bids, key = lambda b: b.value_satoshi)
    trader.accept_bid(current_user, best_bid)
    flash(u"You have accepted the best bid for %s μBTC. Now wait until bidder asks a question, then will send it to you." % (best_bid.value_micro()))
  else:
    flash("You have no seller bids.")
  return redirect(url_for("account"))

@app.route("/my_profile")
@login_required
def my_profile():
  # TODO: Change when we will have more profiles per user
  profile = current_user.profiles[0]
  linkedin = json.loads(profile.data_json)
  return render_template("my_profile.html", user = current_user, linkedin = linkedin)


# AJAX API
@app.route("/my_profile/interested_in", methods=["POST"])
@login_required
def save_interested_in():
  current_user.interested_in = request.form["interested_in"]
  db.session.commit()
  return "OK"

# Email receiver api
@app.route("/notify/mail", methods=["POST"])
def mailgun_notification():
  # TODO: check if it is mailgun

  # TODO: ensure it is not autoresponder

  recipient = request.form["recipient"]
  # sender = request.form["sender"]
  body = request.form["body-plain"]
  stripped = request.form["stripped-text"]

  process_incoming_email(recipient, body, stripped)

  return "OK"

# The obfuscated endpoint is just to not let amateur hackers pollute our security logs.
# We still check every transaction with Coinbase...
@app.route("/notify/coinbase/7cc941e5c7e26026f3a3de1ad28927cb", methods=["POST"])
def coinbase_notification():
  app.logger.info("Coinbase notify %s" % (request.data))
  if request.json:
    order = request.json["order"]
    custom_field = order["custom"]
    value_satoshi = order["total_native"]["cents"]
    coinbase_order_id = order["id"]
    status = order["status"]

    if not coinbase.verify_order_validity(coinbase_order_id, value_satoshi, custom_field, status):
      return "Don't be evil!", 401

    if status == "canceled":
      app.logger.error("Order '%s' is canceled" % (coinbase_order_id))
      bid = Bid.query.filter(Bid.coinbase_order == coinbase_order_id).first()
      if bid:
        db.session.delete(bid)
        db.session.commit()
        app.logger.info("Bid for order '%s' removed." % (coinbase_order_id))
      else:
        app.logger.error("Bid for order '%s' was not found!" % (coinbase_order_id))
      return "Canceled"

    customs = custom_field.split(":")
    if len(customs) != 2:
      app.logger.error("Invalid custom field '%s'" % (custom_field))
      return "Invalid custom field", 500

    try:
      buyer = User.query.filter(User.id == int(customs[0])).first()
      seller = User.query.filter(User.id == int(customs[1])).first()
    except:
      app.logger.error("Invalid custom field (ints) '%s'" % (custom_field))
      return "Invalid custom field", 500

    if not buyer or not seller:
      app.logger.error("One of the users with id %d or %d doesn't exists" % (int(customs[0]), int(customs[1])))
      return "Invalid custom field", 500

    try:
      trader.bid(buyer, seller, value_satoshi, coinbase_order_id)
    except:
      app.logger.error("Likely somebody was trying to use same payment twice for order '%s'!" % (coinbase_order_ids))
      return "Don't be super evil!", 401

    return "OK"
  else:
    app.logger.error("Request from coinbase is not a json.")
    return "Invalid request format", 400


if __name__ == "__main__":
    print "Gosia, our site is running!"
    app.run(debug=config.APP_DEBUG)

