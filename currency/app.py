from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/currency_converter"
mongo = PyMongo(app)

# Load the API key from the .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Fetch live currency rates with API key
def get_currency_rate(from_currency, to_currency):
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{from_currency}"
    response = requests.get(url).json()
    
    if response.get("result") == "success":
        return response["conversion_rates"].get(to_currency)
    else:
        flash("Error fetching conversion rates!")
        return None

# Generate a graph for conversion history
def generate_graph(history):
    currencies = [entry["to_currency"] for entry in history]
    values = [entry["converted_amount"] for entry in history]
    plt.figure(figsize=(10, 6))
    plt.bar(currencies, values, color='teal')
    plt.title("Conversion History")
    plt.xlabel("Currency")
    plt.ylabel("Converted Amount")
    plt.savefig("static/graph.png")
    plt.close()

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = mongo.db.users.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            return redirect(url_for("dashboard"))
        flash("Invalid credentials!")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({"username": username, "password": hashed_password})
        flash("Registration successful! Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    history = list(mongo.db.history.find({"username": session["username"]}))
    return render_template("dashboard.html", username=session["username"], history=history)

@app.route("/convert", methods=["GET", "POST"])
def convert():
    if "username" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        from_currency = request.form["from_currency"]
        to_currency = request.form["to_currency"]
        amount = float(request.form["amount"])
        
        rate = get_currency_rate(from_currency, to_currency)
        if rate:
            converted_amount = round(amount * rate, 2)
            mongo.db.history.insert_one({
                "username": session["username"],
                "from_currency": from_currency,
                "to_currency": to_currency,
                "amount": amount,
                "converted_amount": converted_amount
            })
            flash(f"Converted {amount} {from_currency} to {converted_amount} {to_currency}")
        else:
            flash("Could not fetch conversion rate!")
        
        return redirect(url_for("dashboard"))
    return render_template("convert.html")

@app.route("/graph")
def graph():
    if "username" not in session:
        return redirect(url_for("login"))
    history = list(mongo.db.history.find({"username": session["username"]}))
    if history:
        generate_graph(history)
    return render_template("graph.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out successfully!")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
