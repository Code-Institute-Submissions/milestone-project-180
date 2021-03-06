import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_spots")
def get_spots():
    spots = list(mongo.db.spots.find())
    return render_template("spots.html", spots=spots)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    spots = list(mongo.db.spots.find({"$text": {"$search": query}}))
    return render_template("spots.html", spots=spots)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into session cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_spot", methods=["GET", "POST"])
def add_spot():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        recommend = "on" if request.form.get("recommend") else "off"
        spot = {
            "category_name": request.form.get("category_name"),
            "spot_name": request.form.get("spot_name"),
            "address": request.form.get("address"),
            "visit_date": request.form.get("visit_date"),
            "whats_good": request.form.get("whats_good"),
            "recommend": recommend,
            "created_by": session["user"]
        }
        mongo.db.spots.insert_one(spot)
        flash("Spot Successfully Added")
        return redirect(url_for("get_spots"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_spot.html", categories=categories)


@app.route ("/edit_spot/<spot_id>", methods=["GET", "POST"])
def edit_spot(spot_id):
    if request.method == "POST":
        recommend = "on" if request.form.get("recommend") else "off"
        submit = {
            "category_name": request.form.get("category_name"),
            "spot_name": request.form.get("spot_name"),
            "address": request.form.get("address"),
            "visit_date": request.form.get("visit_date"),
            "whats_good": request.form.get("whats_good"),
            "recommend": recommend,
            "created_by": session["user"]
        }
        mongo.db.spots.update({"_id": ObjectId(spot_id)}, submit)
        flash("Spot Successfully Edited")
        return redirect(url_for("get_spots"))

    spot = mongo.db.spots.find_one({"_id": ObjectId(spot_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_spot.html", spot=spot, categories=categories)


@app.route("/delete_spot/<spot_id>")
def delete_spot(spot_id):
    mongo.db.spots.remove({"_id": ObjectId(spot_id)})
    flash("Spot Successfully Deleted")
    return redirect(url_for("get_spots"))

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
