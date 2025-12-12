# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)   # login
    fullname = db.Column(db.String(120))
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student'
    student_id = db.Column(db.String(50), nullable=True)
    class_name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Activity(db.Model):
    __tablename__ = "activities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(50))
    max_score = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Registration(db.Model):
    __tablename__ = "registrations"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled = db.Column(db.Boolean, default=False)

    user = db.relationship("User", backref="registrations")
    activity = db.relationship("Activity", backref="registrations")

class Evaluation(db.Model):
    __tablename__ = "evaluations"
    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey("registrations.id"), unique=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    level = db.Column(db.String(30))  # 'none','attend','active'
    percent = db.Column(db.Float)     # 0,80,100
    note = db.Column(db.String(300))
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)

    registration = db.relationship("Registration", backref="evaluation")
    teacher = db.relationship("User", foreign_keys=[teacher_id])
