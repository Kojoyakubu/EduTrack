from flask import Blueprint, render_template, request, make_response
from flask_login import login_required
from datetime import date, timedelta
from sqlalchemy import func
from extensions import db
from models import Student, Attendance, Class

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    start_str = request.args.get('start', (date.today() - timedelta(days=29)).isoformat())
    end_str = request.args.get('end', date.today().isoformat())
    class_filter = request.args.get('class_id', '')

    try:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
    except ValueError:
        start = date.today() - timedelta(days=29)
        end = date.today()

    # Summary per student
    query = db.session.query(
        Student,
        func.count(Attendance.id).label('total_days'),
        func.sum(db.case((Attendance.status.in_(['present', 'late']), 1), else_=0)).label('present_days'),
        func.sum(db.case((Attendance.status == 'absent', 1), else_=0)).label('absent_days'),
        func.sum(db.case((Attendance.status == 'late', 1), else_=0)).label('late_days'),
    ).outerjoin(
        Attendance,
        (Attendance.student_id == Student.id) &
        (Attendance.date >= start) &
        (Attendance.date <= end)
    ).filter(Student.is_active == True)

    if class_filter:
        query = query.filter(Student.class_id == int(class_filter))

    report_data = query.group_by(Student.id).order_by(Student.full_name).all()

    classes = Class.query.order_by(Class.name).all()

    # School-wide totals
    school_days = (end - start).days + 1
    total_present = sum(r.present_days or 0 for _, *r in [(s, *rest) for s, *rest in report_data])

    return render_template('reports/index.html',
                           report_data=report_data,
                           start=start,
                           end=end,
                           classes=classes,
                           class_filter=class_filter,
                           school_days=school_days)


@reports_bp.route('/student/<int:student_id>')
@login_required
def student_report(student_id):
    student = Student.query.get_or_404(student_id)
    start_str = request.args.get('start', (date.today() - timedelta(days=29)).isoformat())
    end_str = request.args.get('end', date.today().isoformat())

    try:
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
    except ValueError:
        start = date.today() - timedelta(days=29)
        end = date.today()

    records = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date >= start,
        Attendance.date <= end
    ).order_by(Attendance.date.desc()).all()

    present = sum(1 for r in records if r.status in ('present', 'late'))
    absent = sum(1 for r in records if r.status == 'absent')
    late = sum(1 for r in records if r.status == 'late')

    return render_template('reports/student.html',
                           student=student,
                           records=records,
                           start=start,
                           end=end,
                           present=present,
                           absent=absent,
                           late=late)
