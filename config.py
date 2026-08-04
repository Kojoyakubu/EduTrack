import os
from dotenv import load_dotenv

# Always refresh from .env so runtime config changes are picked up reliably.
load_dotenv(override=True)


def _build_db_uri():
    uri = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@localhost/edutrack'
    # Render gives a postgres:// URI — SQLAlchemy needs postgresql://
    if uri.startswith('postgres://'):
        uri = uri.replace('postgres://', 'postgresql://', 1)
    return uri


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'edu-track-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = _build_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@edutrack.com'

    # SMS configuration (Twilio)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID') or ''
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN') or ''
    TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER') or ''
    TWILIO_MESSAGING_SERVICE_SID = os.environ.get('TWILIO_MESSAGING_SERVICE_SID') or ''

    # WebAuthn / biometric config
    WEBAUTHN_RP_ID = os.environ.get('WEBAUTHN_RP_ID') or 'localhost'
    WEBAUTHN_RP_NAME = os.environ.get('WEBAUTHN_RP_NAME') or 'EDU TRACK'
    WEBAUTHN_ORIGIN = os.environ.get('WEBAUTHN_ORIGIN') or 'http://localhost:5000'

    # School info
    SCHOOL_NAME = 'Oyoko Methodist Senior High School'
    SCHOOL_SHORT = 'EDU TRACK'
