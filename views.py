# coding=utf-8

from flask import render_template, request, url_for, redirect, flash
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
import json
import requests

import config
from database import db, User, Profile, Bid
from main import app
from ozaur.email import Sender, process_incoming_email
from ozaur.trader import trader

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

  try:
    trader.bid(current_user, user, value_satoshi)
    flash(u"You have successfully bidded %s μBTC on '%s'." % (value_micro, user.display_name))
  except:
    flash(u"Your bid on '%s' was unsuccessful." % (user.display_name))

  return redirect(url_for("public_profile", id=id))

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

if __name__ == "__main__":
    print "Gosia our site is running!"
    app.run(debug=config.APP_DEBUG)

