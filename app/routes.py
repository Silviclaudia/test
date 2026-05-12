from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.models import Flashcard, StudySet, User


main = Blueprint("main", __name__)


@main.route("/")
def index():
    recent_public_sets = (
        StudySet.query.filter_by(is_public=True)
        .order_by(StudySet.id.desc())
        .limit(5)
        .all()
    )
    return render_template("index.html", recent_public_sets=recent_public_sets)


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
        return redirect(url_for("main.study_set_detail", study_set_id=study_set.id))

    return render_template("create_studyset.html")


@main.route("/study-sets")
@login_required
def study_sets():
    user_study_sets = (
        StudySet.query.filter_by(user_id=current_user.id)
        .order_by(StudySet.id.desc())
        .all()
    )
    total_cards = sum(len(study_set.flashcards) for study_set in user_study_sets)
    return render_template(
        "profile.html",
        study_sets=user_study_sets,
        total_cards=total_cards,
    )


@main.route("/study-sets/<int:study_set_id>")
@login_required
def study_set_detail(study_set_id):
    study_set = StudySet.query.filter_by(
        id=study_set_id,
        user_id=current_user.id,
    ).first()
    if study_set is None:
        abort(404)

    return render_template("study_set.html", study_set=study_set)


@main.route("/study-sets/<int:study_set_id>/study")
@login_required
def study_set_study(study_set_id):
    study_set = StudySet.query.filter_by(
        id=study_set_id,
        user_id=current_user.id,
    ).first()
    if study_set is None:
        abort(404)

    return render_template("study_mode.html", study_set=study_set)

@main.route('/analytics')

def analytics():
    user_study_sets = (
        StudySet.query.filter_by(user_id=current_user.id)
        .order_by(StudySet.id.desc())
        .all()
    )
    total_sets = len(user_study_sets)
    total_cards = sum(len(study_set.flashcards) for study_set in user_study_sets)
    public_sets = sum(1 for study_set in user_study_sets if study_set.is_public)
    average_cards = round(total_cards / total_sets, 1) if total_sets else 0

    recent_sets = user_study_sets[:7]
    raw_chart_values = [len(study_set.flashcards) for study_set in reversed(recent_sets)]
    chart_labels = [study_set.title[:10] for study_set in reversed(recent_sets)]
    if not raw_chart_values:
        raw_chart_values = [0]
        chart_labels = ["No sets"]

    max_value = max(raw_chart_values) or 1
    chart_data = [int((value / max_value) * 100) for value in raw_chart_values]

    return render_template(
        "analytics.html",
        total_cards=total_cards,
        total_sets=total_sets,
        public_sets=public_sets,
        average_cards=average_cards,
        chart_data=chart_data,
        chart_labels=chart_labels,
    )