from flask import Flask, render_template, request
app = Flask(__name__)

@app.route("/")
def main_page():
    return render_template("index.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/create_profile", methods=["POST"])
def create_profile():
  linkedin_oauth_token = request.form["linkedin_oauth_token"]
  return "Response " + linkedin_oauth_token

if __name__ == "__main__":
    app.run(debug=True)

