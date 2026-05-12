from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models import Flashcard, StudySet, User


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


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        login_identifier = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter(
            (User.email == login_identifier) | (User.username == login_identifier)
        ).first()

        if user is None or not user.check_password(password):
            flash("Invalid email/username or password.")
            return render_template("login.html"), 400

        login_user(user)
        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("main.index"))

    return render_template("login.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.")
    return redirect(url_for("main.index"))


@main.route("/study-sets/new", methods=["GET", "POST"])
@login_required
def create_study_set():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        terms = request.form.getlist("term")
        definitions = request.form.getlist("definition")

        flashcards = [
            Flashcard(question=term.strip(), answer=definition.strip())
            for term, definition in zip(terms, definitions)
            if term.strip() and definition.strip()
        ]

        if not title or not flashcards:
            flash("Add a title and at least one complete flashcard.")
            return render_template("create_studyset.html"), 400

        study_set = StudySet(
            title=title,
            description=description,
            owner=current_user,
            flashcards=flashcards,
        )
        db.session.add(study_set)
        db.session.commit()

        flash("Study set created.")
        return redirect(url_for("main.index"))

    return render_template("create_studyset.html")

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