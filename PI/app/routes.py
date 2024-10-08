from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user # type: ignore
from app import db
from app.models import User, Institute, Student, Inspector, Announcement
from werkzeug.security import generate_password_hash
from sqlalchemy import or_
import json
from datetime import datetime

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
            flash('Email already registered', 'danger')
            return redirect(url_for('main.signup', user_type=user_type))
        
        if user_type == 'institute':
            name = request.form.get('name')
            gov_verification_number = request.form.get('gov_verification_number')
            phone = request.form.get('phone')
            address = request.form.get('address')
            website = request.form.get('website')
            user = Institute(email=email, name=name, gov_verification_number=gov_verification_number, phone=phone, address=address, website=website)
        elif user_type == 'student':
            gov_id = request.form.get('gov_id')
            institute_id = request.form.get('institute_id')
            user = Student(email=email, gov_id=gov_id, institute_id=institute_id)
        elif user_type == 'inspector':
            inspector_id = request.form.get('inspector_id')
            qualifications = request.form.get('qualifications')
            user = Inspector(email=email, inspector_id=inspector_id, qualifications=qualifications)
        else:
            flash('Invalid user type', 'danger')
            return redirect(url_for('main.index'))
        
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registered successfully', 'success')
        return redirect(url_for('main.login'))
    
    institutes = Institute.query.all() if user_type == 'student' else None
    return render_template(f'signup_{user_type}.html', institutes=institutes)

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
            flash('Invalid email or password', 'danger')
    
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
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    students = Student.query.filter_by(institute_id=current_user.id).all()
    faculty_data = json.loads(current_user.faculty_data) if current_user.faculty_data else []
    return render_template('dashboard_institute.html', students=students, faculty_data=faculty_data)

@bp.route('/dashboard/student')
@login_required
def dashboard_student():
    if not isinstance(current_user, Student):
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    faculty_data = json.loads(current_user.institute.faculty_data) if current_user.institute.faculty_data else []
    return render_template('dashboard_student.html', faculty_data=faculty_data)

@bp.route('/dashboard/inspector')
@login_required
def dashboard_inspector():
    if not isinstance(current_user, Inspector):
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    institutes = Institute.query.all()
    return render_template('dashboard_inspector.html', institutes=institutes)

@bp.route('/search_institutes')
@login_required
def search_institutes():
    if not isinstance(current_user, Inspector):
        return jsonify([])
    
    query = request.args.get('query', '')
    institutes = Institute.query.filter(or_(
        Institute.name.ilike(f'%{query}%'),
        Institute.email.ilike(f'%{query}%'),
        Institute.gov_verification_number.ilike(f'%{query}%')
    )).all()
    
    return jsonify([{
        'id': institute.id,
        'name': institute.name,
        'email': institute.email,
        'gov_verification_number': institute.gov_verification_number,
        'phone': institute.phone,
        'address': institute.address,
        'website': institute.website
    } for institute in institutes])

@bp.route('/institute/<int:institute_id>')
@login_required
def institute_details(institute_id):
    if not isinstance(current_user, Inspector):
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    institute = Institute.query.get_or_404(institute_id)
    students = Student.query.filter_by(institute_id=institute_id).all()
    faculty_data = json.loads(institute.faculty_data) if institute.faculty_data else []
    return render_template('institute_details.html', institute=institute, students=students, faculty_data=faculty_data)

@bp.route('/institute/announcements', methods=['GET', 'POST'])
@login_required
def institute_announcements():
    if not isinstance(current_user, Institute):
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        new_announcement = Announcement(title=title, content=content, institute_id=current_user.id)
        db.session.add(new_announcement)
        db.session.commit()
        flash('Announcement posted successfully', 'success')
    
    announcements = Announcement.query.filter_by(institute_id=current_user.id).order_by(Announcement.created_at.desc()).all()
    return render_template('institute_announcements.html', announcements=announcements)

@bp.route('/get_announcements')
@login_required
def get_announcements():
    if isinstance(current_user, Student):
        institute_id = current_user.institute_id
    elif isinstance(current_user, Institute):
        institute_id = current_user.id
    else:
        return jsonify([])

    announcements = Announcement.query.filter_by(institute_id=institute_id).order_by(Announcement.created_at.desc()).all()
    return jsonify([{
        'id': announcement.id,
        'title': announcement.title,
        'content': announcement.content,
        'created_at': announcement.created_at.isoformat()
    } for announcement in announcements])

@bp.route('/update_faculty_data', methods=['POST'])
@login_required
def update_faculty_data():
    if not isinstance(current_user, Institute):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    faculty_data = request.json.get('faculty_data')
    if faculty_data is None:
        return jsonify({'success': False, 'message': 'No faculty data provided'}), 400

    try:
        current_user.faculty_data = json.dumps(faculty_data)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Faculty data updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating faculty data: {str(e)}'}), 500

@bp.route('/update_institute_info', methods=['POST'])
@login_required
def update_institute_info():
    if not isinstance(current_user, Institute):
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    try:
        current_user.address = request.form.get('address')
        current_user.website = request.form.get('website')
        current_user.phone = request.form.get('phone')
        db.session.commit()
        return jsonify({'success': True, 'message': 'Institute information updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating institute information: {str(e)}'}), 500