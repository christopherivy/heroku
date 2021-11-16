from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Tweet
from forms import UserForm, TweetForm
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///auth_demo"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "postgresql:///auth_demo"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "Red747")
# print(app.config["SECRET_KEY"])
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False


connect_db(app)

toolbar = DebugToolbarExtension(app)

# ******************************************************** HOME PAGE
@app.route("/")
def home_page():
    return render_template("index.html")


# ******************************************************** SHOW TWEET
@app.route("/tweets", methods=["GET", "POST"])
def show_tweets():
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect("/")
    form = TweetForm()
    all_tweets = Tweet.query.all()
    if form.validate_on_submit():
        text = form.text.data
        new_tweet = Tweet(text=text, user_id=session["user_id"])
        db.session.add(new_tweet)
        db.session.commit()
        flash("Tweet Created!", "success")
        return redirect("/tweets")

    return render_template("tweets.html", form=form, tweets=all_tweets)


# ******************************************************** DELETE A TWEET
@app.route("/tweets/<int:id>", methods=["POST"])
def delete_tweet(id):
    """Delete tweet"""
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    tweet = Tweet.query.get_or_404(id)
    if tweet.user_id == session["user_id"]:
        db.session.delete(tweet)
        db.session.commit()
        flash("Tweet deleted!", "info")
        return redirect("/tweets")
    flash("You don't have permission to do that!", "danger")
    return redirect("/tweets")


# ******************************************************** REGISTER A USER
@app.route("/register", methods=["GET", "POST"])
def register_user():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        new_user = User.register(username, password)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append("Username taken.  Please pick another")
            return render_template("register.html", form=form)
        session["user_id"] = new_user.id
        flash("Welcome! Successfully Created Your Account!", "success")
        return redirect("/tweets")

    return render_template("register.html", form=form)


# ******************************************************** USER LOGIN
@app.route("/login", methods=["GET", "POST"])
def login_user():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session["user_id"] = user.id
            session["user_name"] = user.username
            return redirect("/tweets")
        else:
            form.username.errors = ["Invalid username/password."]

    return render_template("login.html", form=form)


# ******************************************************** LOG OUT
@app.route("/logout")
def logout_user():
    session.pop("user_id")
    flash("Goodbye!", "info")
    return redirect("/")
