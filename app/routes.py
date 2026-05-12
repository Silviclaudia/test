from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import User


main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html"), 400

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("An account with that name or email already exists.")
            return render_template("register.html"), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created. You can now sign in.")
        return redirect(url_for("main.index"))

    return render_template("register.html")

@main.route('/analytics')

def analytics():
    totalcards = sum(len(s_set.flashcards) for s_set in current_user.study_sets)

    #data for the visuals 
    stats = {
        'cards': totalcards, 
        'accuracy': 90,
        'streak': 13, 
        'chart_data': [50, 65, 78, 42, 61, 20, 40]
    }

    return render_template('analytics.html', **stats)

@main.route('/register')
def register():
    return render_template('register.html')

@main.route('/create')
@login_required
def create_studyset():
    return render_template('create_studyset.html')