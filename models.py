from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('admin', 'staff'), nullable=False, default='staff')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(120))

    students = db.relationship('Student', backref='class_', lazy='dynamic')

    def __repr__(self):
        return f'<Class {self.name}>'


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('Male', 'Female'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    rfid_tag = db.Column(db.String(50), unique=True)
    photo = db.Column(db.String(256))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guardians = db.relationship('Guardian', backref='student', lazy='dynamic',
                                 cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='student', lazy='dynamic',
                                          cascade='all, delete-orphan')

    def primary_guardian(self):
        return self.guardians.filter_by(is_primary=True).first() or self.guardians.first()

    def __repr__(self):
        return f'<Student {self.student_id} - {self.full_name}>'


class Guardian(db.Model):
    __tablename__ = 'guardians'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    is_primary = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Guardian {self.full_name} for student {self.student_id}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    arrival_time = db.Column(db.DateTime)
    departure_time = db.Column(db.DateTime)
    arrival_marked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    departure_marked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.Enum('present', 'late', 'absent', 'excused'), default='present')
    notes = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'date', name='unique_student_date'),
    )

    def __repr__(self):
        return f'<Attendance student={self.student_id} date={self.date}>'


class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'))
    event_type = db.Column(db.Enum('arrival', 'departure', 'absent', 'late'), nullable=False)
    channel = db.Column(db.Enum('email', 'sms', 'both'), nullable=False, default='email')
    recipient_contact = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('sent', 'failed', 'pending'), default='pending')
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)

    student = db.relationship('Student', backref='notifications')
    guardian = db.relationship('Guardian', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.event_type} to {self.recipient_contact}>'


class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(80), unique=True, nullable=False)
    setting_value = db.Column(db.Text)
    description = db.Column(db.String(256))

    @staticmethod
    def get(key, default=None):
        s = Setting.query.filter_by(setting_key=key).first()
        return s.setting_value if s else default

    @staticmethod
    def set(key, value):
        s = Setting.query.filter_by(setting_key=key).first()
        if s:
            s.setting_value = value
        else:
            s = Setting(setting_key=key, setting_value=value)
            db.session.add(s)
        db.session.commit()
