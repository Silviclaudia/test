from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from app.models import User
from app import db

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Change 'username' to 'email' to match your HTML name="email"
        email_or_user = request.form.get('email') 
        password = request.form.get('password')
        
        # Search by email instead
        user = User.query.filter_by(email=email_or_user).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.analytics'))
        else:
            flash('Invalid email or password')
            
    return render_template('login.html')
   
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