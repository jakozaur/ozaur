from flask import render_template, request
from sqlalchemy.exc import IntegrityError
import json
import requests

import config
from database import db, User, Profile
from main import app

@app.route("/")
def main_page():
  return render_template("index.html")

@app.route("/signup")
def signup():
  return render_template("signup.html")

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
  # TODO: Change when we will have more profiles per user
  profile = user.profiles[0]

  linkedin = json.loads(profile.data_json)

  return render_template("profile.html", user=user, linkedin=linkedin)

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
  except IntegrityError, e:
    db.session.rollback()
    user = User.query.filter(User.email == user_json["emailAddress"]).first()
    # TODO: Change when we will have more profiles per user
    profile = user.profiles[0]

  linkedin = json.loads(profile.data_json)

  return render_template("profile.html", user = user, linkedin = linkedin)

if __name__ == "__main__":
    app.run(debug=config.APP_DEBUG)

