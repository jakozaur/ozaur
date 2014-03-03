from flask import Flask, render_template, request
import requests
app = Flask(__name__)

@app.route("/")
def main_page():
    return render_template("index.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/create_account", methods=["POST"])
def create_account():
  linkedin_oauth_token = request.form["linkedin_oauth_token"]
  r = requests.get("https://api.linkedin.com/v1/people::(~):(id,first-name,last-name,headline,location,industry,num-connections,summary,specialties,positions,picture-url,public-profile-url,email-address,associations,interests,publications,patents,languages,skills,certifications,educations,courses,volunteer,num-recommenders,honors-awards)",
      headers={"oauth_token": linkedin_oauth_token,
        "x-li-format": "json"})

  return "Response " + str(r.json())

if __name__ == "__main__":
    app.run(debug=True)

