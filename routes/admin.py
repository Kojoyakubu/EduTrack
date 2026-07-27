from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models import User, Class, Setting, NotificationLog
from werkzeug.security import generate_password_hash
from utils.notifications import refresh_pending_sms_logs

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Administrator access required.', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def index():
    return redirect(url_for('admin.users'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.full_name).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'staff')

        if not all([full_name, email, password]):
            flash('All fields are required.', 'danger')
            return render_template('admin/create_user.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return render_template('admin/create_user.html')

        if User.query.filter_by(email=email).first():
            flash('A user with this email already exists.', 'danger')
            return render_template('admin/create_user.html')

        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'User {full_name} created successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/create_user.html')


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'{user.full_name} has been {status}.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/classes')
@login_required
@admin_required
def classes():
    all_classes = Class.query.order_by(Class.name).all()
    return render_template('admin/classes.html', classes=all_classes)


@admin_bp.route('/classes/add', methods=['POST'])
@login_required
@admin_required
def add_class():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    if not name:
        flash('Class name is required.', 'danger')
    elif Class.query.filter_by(name=name).first():
        flash('A class with this name already exists.', 'danger')
    else:
        db.session.add(Class(name=name, description=description))
        db.session.commit()
        flash(f'Class {name} added.', 'success')
    return redirect(url_for('admin.classes'))


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        keys = [
            'school_arrival_start', 'school_arrival_end',
            'school_departure_time', 'late_threshold_minutes',
            'notifications_enabled', 'notification_channel'
        ]
        for key in keys:
            val = request.form.get(key, '').strip()
            if val:
                Setting.set(key, val)
        flash('Settings saved.', 'success')
        return redirect(url_for('admin.settings'))

    all_settings = {s.setting_key: s.setting_value
                    for s in Setting.query.all()}
    return render_template('admin/settings.html', settings=all_settings)


@admin_bp.route('/notifications')
@login_required
@admin_required
def notifications():
    refresh_pending_sms_logs(limit=100)
    page = request.args.get('page', 1, type=int)
    logs = NotificationLog.query.order_by(
        NotificationLog.sent_at.desc()
    ).paginate(page=page, per_page=30)
    return render_template('admin/notifications.html', logs=logs)


@admin_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password', '')
        new_pw = request.form.get('new_password', '')
        confirm_pw = request.form.get('confirm_password', '')

        if not current_user.check_password(current_pw):
            flash('Current password is incorrect.', 'danger')
        elif len(new_pw) < 8:
            flash('New password must be at least 8 characters.', 'danger')
        elif new_pw != confirm_pw:
            flash('Passwords do not match.', 'danger')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('dashboard.index'))

    return render_template('admin/change_password.html')
