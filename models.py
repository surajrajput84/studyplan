from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    plans    = db.relationship('StudyPlan', backref='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class StudyPlan(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    subject     = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weeks       = db.relationship('Week', backref='plan', cascade='all, delete-orphan')

class Week(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)
    title       = db.Column(db.String(200), nullable=False)
    plan_id     = db.Column(db.Integer, db.ForeignKey('study_plan.id'), nullable=False)
    days        = db.relationship('Day', backref='week', cascade='all, delete-orphan')

class Day(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    day_number   = db.Column(db.Integer, nullable=False)
    title        = db.Column(db.String(200), nullable=False)
    status       = db.Column(db.String(20), default='pending')
    date         = db.Column(db.Date, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    week_id      = db.Column(db.Integer, db.ForeignKey('week.id'), nullable=False)

class Activity(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    message    = db.Column(db.String(300), nullable=False)
    plan_title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
