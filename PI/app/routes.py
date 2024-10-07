from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from app import db
from app.models import User, Institute, Student, Inspector
from werkzeug.security import generate_password_hash

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/signup/<user_type>', methods=['GET', 'POST'])
def signup(user_type):
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('main.signup', user_type=user_type))
        
        if user_type == 'institute':
            gov_verification_number = request.form.get('gov_verification_number')
            phone = request.form.get('phone')
            user = Institute(email=email, gov_verification_number=gov_verification_number, phone=phone)
        elif user_type == 'student':
            gov_id = request.form.get('gov_id')
            user = Student(email=email, gov_id=gov_id)
        elif user_type == 'inspector':
            inspector_id = request.form.get('inspector_id')
            qualifications = request.form.get('qualifications')
            user = Inspector(email=email, inspector_id=inspector_id, qualifications=qualifications)
        else:
            flash('Invalid user type')
            return redirect(url_for('main.index'))
        
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registered successfully')
        return redirect(url_for('main.login'))
    
    return render_template(f'signup_{user_type}.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for(f'main.dashboard_{user.user_type}'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/dashboard/institute')
@login_required
def dashboard_institute():
    if not isinstance(current_user, Institute):
        flash('Access denied')
        return redirect(url_for('main.index'))
    return render_template('dashboard_institute.html')

@bp.route('/dashboard/student')
@login_required
def dashboard_student():
    if not isinstance(current_user, Student):
        flash('Access denied')
        return redirect(url_for('main.index'))
    return render_template('dashboard_student.html')

@bp.route('/dashboard/inspector')
@login_required
def dashboard_inspector():
    if not isinstance(current_user, Inspector):
        flash('Access denied')
        return redirect(url_for('main.index'))
    institutes = Institute.query.all()
    return render_template('dashboard_inspector.html', institutes=institutes)