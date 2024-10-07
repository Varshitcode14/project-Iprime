from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(20), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Institute(User):
    __tablename__ = 'institute'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    gov_verification_number = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_identity': 'institute',
    }

class Student(User):
    __tablename__ = 'student'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    gov_id = db.Column(db.String(50), unique=True, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }

class Inspector(User):
    __tablename__ = 'inspector'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    inspector_id = db.Column(db.String(50), unique=True, nullable=False)
    qualifications = db.Column(db.Text)

    __mapper_args__ = {
        'polymorphic_identity': 'inspector',
    }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))