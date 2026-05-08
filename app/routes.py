from flask import Blueprint, render_template


main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")

@main.route('/analytics')
@login_required
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