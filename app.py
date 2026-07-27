from flask import Flask
from datetime import datetime
from config import Config
from extensions import db, login_manager
from models import User, Class, Setting
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError


def _resolve_database_uri(config):
    """Use configured DB, but fall back to SQLite when MySQL is unreachable."""
    uri = config.get('SQLALCHEMY_DATABASE_URI', '')

    if not uri.startswith('mysql'):
        return uri

    try:
        engine = create_engine(uri, pool_pre_ping=True)
        with engine.connect():
            pass
        engine.dispose()
        return uri
    except SQLAlchemyError:
        return 'sqlite:///edutrack.db'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = _resolve_database_uri(app.config)

    db.init_app(app)
    login_manager.init_app(app)

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.students import students_bp
    from routes.attendance import attendance_bp
    from routes.reports import reports_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    with app.app_context():
        db.create_all()
        _seed_defaults()

    return app


def _seed_defaults():
    """Seed default admin user, classes, and settings if they don't exist."""
    # Default admin
    if not User.query.filter_by(email='admin@edutrack.com').first():
        admin = User(
            full_name='System Administrator',
            email='admin@edutrack.com',
            role='admin',
            is_active=True
        )
        admin.set_password('Admin@1234')
        db.session.add(admin)

    # Default classes
    default_classes = [
        ('Form 1A', 'First Year - Section A'),
        ('Form 1B', 'First Year - Section B'),
        ('Form 2A', 'Second Year - Section A'),
        ('Form 2B', 'Second Year - Section B'),
        ('Form 3A', 'Third Year - Section A'),
        ('Form 3B', 'Third Year - Section B'),
    ]
    for name, desc in default_classes:
        if not Class.query.filter_by(name=name).first():
            db.session.add(Class(name=name, description=desc))

    # Default settings
    defaults = [
        ('school_arrival_start', '06:00', 'Time from which arrivals are recorded'),
        ('school_arrival_end', '07:30', 'Latest on-time arrival'),
        ('school_departure_time', '15:30', 'Expected departure time'),
        ('late_threshold_minutes', '30', 'Minutes after arrival_end to mark as late'),
        ('notifications_enabled', '1', 'Enable/disable all notifications'),
        ('notification_channel', 'email', 'Default notification channel'),
    ]
    for key, val, desc in defaults:
        if not Setting.query.filter_by(setting_key=key).first():
            db.session.add(Setting(setting_key=key, setting_value=val, description=desc))

    db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
