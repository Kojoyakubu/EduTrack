from flask import Blueprint, render_template
from flask_login import login_required
from datetime import date, datetime, timedelta
from sqlalchemy import func
from extensions import db
from models import Student, Attendance, NotificationLog, User

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = date.today()

    total_students = Student.query.filter_by(is_active=True).count()
    present_today = Attendance.query.filter(
        Attendance.date == today,
        Attendance.status.in_(['present', 'late'])
    ).count()
    absent_today = Attendance.query.filter(
        Attendance.date == today,
        Attendance.status == 'absent'
    ).count()
    late_today = Attendance.query.filter(
        Attendance.date == today,
        Attendance.status == 'late'
    ).count()
    departed_today = Attendance.query.filter(
        Attendance.date == today,
        Attendance.departure_time.isnot(None)
    ).count()

    # Recent arrivals
    recent_arrivals = db.session.query(Attendance, Student).join(
        Student, Attendance.student_id == Student.id
    ).filter(
        Attendance.date == today,
        Attendance.arrival_time.isnot(None)
    ).order_by(Attendance.arrival_time.desc()).limit(10).all()

    # Recent notifications
    recent_notifications = NotificationLog.query.order_by(
        NotificationLog.sent_at.desc()
    ).limit(8).all()

    # Weekly attendance chart data
    week_labels = []
    week_present = []
    week_absent = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        week_labels.append(day.strftime('%a %d'))
        p = Attendance.query.filter(
            Attendance.date == day,
            Attendance.status.in_(['present', 'late'])
        ).count()
        a = Attendance.query.filter(
            Attendance.date == day,
            Attendance.status == 'absent'
        ).count()
        week_present.append(p)
        week_absent.append(a)

    return render_template('dashboard/index.html',
        today=today,
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        late_today=late_today,
        departed_today=departed_today,
        recent_arrivals=recent_arrivals,
        recent_notifications=recent_notifications,
        week_labels=week_labels,
        week_present=week_present,
        week_absent=week_absent
    )
