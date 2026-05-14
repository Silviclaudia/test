from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from app import db
from app.models import Flashcard, StudySet, User


main = Blueprint("main", __name__)


def get_owned_study_set_or_404(study_set_id):
    study_set = StudySet.query.filter_by(
        id=study_set_id,
        user_id=current_user.id,
    ).first()
    if study_set is None:
        abort(404)
    return study_set


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
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        terms = request.form.get("terms")

        if not terms:
            flash("You must agree to the Terms and Conditions.", "danger")
            return render_template("register.html"), 400

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html"), 400

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("An account with that name or email already exists.", "danger")
            return render_template("register.html"), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created! Welcome!", "success")
        return redirect(url_for("main.index"))

    return render_template("register.html")

@main.route('/terms')
def terms():
    return render_template('terms.html')

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
            flash("Invalid email/username or password.", "danger")
            return render_template("login.html", email=login_identifier), 400

        user.update_streak()
        user.update_achievements()
        db.session.commit()

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


@main.route("/setting", methods=["GET", "POST"])
@main.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not username or not email:
            flash("Username and email are required.", "danger")
            return render_template("setting.html"), 400

        current_user.username = username
        current_user.email = email

        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for("main.settings"))

    return render_template("setting.html")

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
        streak=current_user.streak,        
        achievements=current_user.achievements,  
    )


@main.route("/profile")
@login_required
def profile():
    total_cards = sum(len(s.flashcards) for s in current_user.study_sets)
    return render_template(
        "profile.html",
        total_cards=total_cards,
        streak=current_user.streak,
        achievements=current_user.achievements,
        study_sets=current_user.study_sets,
    )


@main.route("/search")
@login_required
def search_public_sets():
    query_text = request.args.get("q", "").strip()
    owner_text = request.args.get("owner", "").strip()

    search_query = StudySet.query.join(User).filter(StudySet.is_public.is_(True))
    if query_text:
        pattern = f"%{query_text}%"
        search_query = search_query.filter(
            or_(StudySet.title.ilike(pattern), StudySet.description.ilike(pattern))
        )
    if owner_text:
        search_query = search_query.filter(User.username.ilike(f"%{owner_text}%"))

    results = search_query.order_by(StudySet.id.desc()).limit(30).all()
    return render_template(
        "search.html",
        results=results,
        query_text=query_text,
        owner_text=owner_text,
    )


@main.route("/study-sets/<int:study_set_id>")
@login_required
def study_set_detail(study_set_id):
    study_set = get_owned_study_set_or_404(study_set_id)
    return render_template("study_set.html", study_set=study_set)


@main.route("/study-sets/<int:study_set_id>/edit", methods=["GET", "POST"])
@login_required
def edit_study_set(study_set_id):
    study_set = get_owned_study_set_or_404(study_set_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        is_public = request.form.get("is_public") == "on"

        flashcard_ids = request.form.getlist("flashcard_id")
        terms = request.form.getlist("term")
        definitions = request.form.getlist("definition")

        flashcard_rows = []
        for flashcard_id, term, definition in zip(flashcard_ids, terms, definitions):
            clean_term = term.strip()
            clean_definition = definition.strip()

            if not clean_term and not clean_definition:
                continue
            if not clean_term or not clean_definition:
                flash("Each flashcard must include both term and definition.")
                return render_template("edit_studyset.html", study_set=study_set), 400

            flashcard_rows.append((flashcard_id, clean_term, clean_definition))

        if not title:
            flash("Set title is required.")
            return render_template("edit_studyset.html", study_set=study_set), 400

        if not flashcard_rows:
            flash("Add at least one complete flashcard.")
            return render_template("edit_studyset.html", study_set=study_set), 400

        existing_flashcards = {str(card.id): card for card in study_set.flashcards}
        kept_flashcard_ids = set()

        for flashcard_id, term, definition in flashcard_rows:
            if flashcard_id:
                existing_flashcard = existing_flashcards.get(flashcard_id)
                if existing_flashcard is None:
                    continue
                existing_flashcard.question = term
                existing_flashcard.answer = definition
                kept_flashcard_ids.add(flashcard_id)
            else:
                db.session.add(
                    Flashcard(question=term, answer=definition, study_set=study_set)
                )

        for card_id, card in existing_flashcards.items():
            if card_id not in kept_flashcard_ids:
                db.session.delete(card)

        study_set.title = title
        study_set.description = description
        study_set.is_public = is_public
        db.session.commit()

        flash("Study set updated.")
        return redirect(url_for("main.study_set_detail", study_set_id=study_set.id))

    return render_template("edit_studyset.html", study_set=study_set)


@main.route("/study-sets/<int:study_set_id>/delete", methods=["POST"])
@login_required
def delete_study_set(study_set_id):
    study_set = get_owned_study_set_or_404(study_set_id)
    db.session.delete(study_set)
    db.session.commit()
    flash("Study set deleted.")
    return redirect(url_for("main.study_sets"))


@main.route("/browse/study-sets/<int:study_set_id>")
@login_required
def browse_public_study_set(study_set_id):
    study_set = StudySet.query.filter_by(id=study_set_id, is_public=True).first()
    if study_set is None:
        abort(404)
    return render_template("browse_study_set.html", study_set=study_set)


@main.route("/study-sets/<int:study_set_id>/study")
@login_required
def study_set_study(study_set_id):
    study_set = get_owned_study_set_or_404(study_set_id)
    return render_template("study_mode.html", study_set=study_set)


@main.route("/analytics")
@login_required
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