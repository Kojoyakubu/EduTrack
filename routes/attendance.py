from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import date, datetime
from extensions import db
from models import Student, Attendance, Setting
from utils.notifications import notify_guardians

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


def _get_late_threshold():
    try:
        return int(Setting.get('late_threshold_minutes', '30'))
    except ValueError:
        return 30


def _is_late(arrival_time: datetime) -> bool:
    end_str = Setting.get('school_arrival_end', '07:30')
    h, m = map(int, end_str.split(':'))
    cutoff = datetime(arrival_time.year, arrival_time.month, arrival_time.day, h, m)
    threshold = _get_late_threshold()
    from datetime import timedelta
    return arrival_time > cutoff + timedelta(minutes=threshold)


@attendance_bp.route('/')
@login_required
def index():
    selected_date = request.args.get('date', date.today().isoformat())
    try:
        selected_date = date.fromisoformat(selected_date)
    except ValueError:
        selected_date = date.today()

    class_filter = request.args.get('class_id', '')
    search = request.args.get('search', '').strip()

    query = db.session.query(Student, Attendance).outerjoin(
        Attendance,
        (Attendance.student_id == Student.id) & (Attendance.date == selected_date)
    ).filter(Student.is_active == True)

    if class_filter:
        query = query.filter(Student.class_id == int(class_filter))
    if search:
        query = query.filter(
            (Student.full_name.ilike(f'%{search}%')) |
            (Student.student_id.ilike(f'%{search}%'))
        )

    records = query.order_by(Student.full_name).all()

    from models import Class
    classes = Class.query.order_by(Class.name).all()

    total = len(records)
    present = sum(1 for _, a in records if a and a.status in ('present', 'late'))
    absent = sum(1 for _, a in records if a and a.status == 'absent')
    not_marked = sum(1 for _, a in records if not a)

    return render_template('attendance/index.html',
                           records=records,
                           selected_date=selected_date,
                           classes=classes,
                           class_filter=class_filter,
                           search=search,
                           total=total,
                           present=present,
                           absent=absent,
                           not_marked=not_marked)


@attendance_bp.route('/mark-arrival', methods=['GET', 'POST'])
@login_required
def mark_arrival():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        if not identifier:
            flash('Please enter a student ID or RFID tag.', 'warning')
            return render_template('attendance/mark_arrival.html')

        student = (Student.query.filter_by(student_id=identifier, is_active=True).first() or
                   Student.query.filter_by(rfid_tag=identifier, is_active=True).first())

        if not student:
            flash(f'No active student found with ID or RFID: {identifier}', 'danger')
            return render_template('attendance/mark_arrival.html')

        today = date.today()
        now = datetime.now()

        record = Attendance.query.filter_by(student_id=student.id, date=today).first()

        if record and record.arrival_time:
            flash(f'{student.full_name} has already been marked as arrived today at '
                  f'{record.arrival_time.strftime("%I:%M %p")}.', 'warning')
            return render_template('attendance/mark_arrival.html')

        late = _is_late(now)
        status = 'late' if late else 'present'

        if record:
            record.arrival_time = now
            record.arrival_marked_by = current_user.id
            record.status = status
        else:
            record = Attendance(
                student_id=student.id,
                date=today,
                arrival_time=now,
                arrival_marked_by=current_user.id,
                status=status
            )
            db.session.add(record)

        db.session.commit()

        event_type = 'late' if late else 'arrival'
        notify_guardians(student, event_type, now)

        msg = f'{student.full_name} marked as {"LATE" if late else "PRESENT"} at {now.strftime("%I:%M %p")}.'
        flash(msg, 'warning' if late else 'success')
        return render_template('attendance/mark_arrival.html', last_student=student, last_time=now)

    return render_template('attendance/mark_arrival.html')


@attendance_bp.route('/mark-departure', methods=['GET', 'POST'])
@login_required
def mark_departure():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        if not identifier:
            flash('Please enter a student ID or RFID tag.', 'warning')
            return render_template('attendance/mark_departure.html')

        student = (Student.query.filter_by(student_id=identifier, is_active=True).first() or
                   Student.query.filter_by(rfid_tag=identifier, is_active=True).first())

        if not student:
            flash(f'No active student found with ID or RFID: {identifier}', 'danger')
            return render_template('attendance/mark_departure.html')

        today = date.today()
        now = datetime.now()

        record = Attendance.query.filter_by(student_id=student.id, date=today).first()

        if not record or not record.arrival_time:
            flash(f'{student.full_name} has no arrival record for today. '
                  f'Please mark arrival first.', 'warning')
            return render_template('attendance/mark_departure.html')

        if record.departure_time:
            flash(f'{student.full_name} has already been marked as departed at '
                  f'{record.departure_time.strftime("%I:%M %p")}.', 'warning')
            return render_template('attendance/mark_departure.html')

        record.departure_time = now
        record.departure_marked_by = current_user.id
        db.session.commit()

        notify_guardians(student, 'departure', now)

        flash(f'{student.full_name} marked as departed at {now.strftime("%I:%M %p")}.', 'success')
        return render_template('attendance/mark_departure.html', last_student=student, last_time=now)

    return render_template('attendance/mark_departure.html')


@attendance_bp.route('/mark-absent', methods=['POST'])
@login_required
def mark_absent():
    student_id = request.form.get('student_id', type=int)
    selected_date_str = request.form.get('date', date.today().isoformat())

    try:
        selected_date = date.fromisoformat(selected_date_str)
    except ValueError:
        selected_date = date.today()

    student = Student.query.get_or_404(student_id)

    record = Attendance.query.filter_by(student_id=student.id, date=selected_date).first()
    if record:
        record.status = 'absent'
    else:
        record = Attendance(
            student_id=student.id,
            date=selected_date,
            status='absent',
            arrival_marked_by=current_user.id
        )
        db.session.add(record)

    db.session.commit()
    notify_guardians(student, 'absent', datetime.combine(selected_date, datetime.min.time()))
    flash(f'{student.full_name} marked as absent.', 'info')
    return redirect(url_for('attendance.index', date=selected_date_str))


@attendance_bp.route('/api/lookup')
@login_required
def api_lookup():
    """Quick lookup for RFID/ID scan — returns student info as JSON."""
    identifier = request.args.get('id', '').strip()
    if not identifier:
        return jsonify({'found': False})

    student = (Student.query.filter_by(student_id=identifier, is_active=True).first() or
               Student.query.filter_by(rfid_tag=identifier, is_active=True).first())

    if not student:
        return jsonify({'found': False})

    today = date.today()
    record = Attendance.query.filter_by(student_id=student.id, date=today).first()

    return jsonify({
        'found': True,
        'student_id': student.student_id,
        'full_name': student.full_name,
        'class_name': student.class_.name,
        'arrived': bool(record and record.arrival_time),
        'departed': bool(record and record.departure_time),
        'status': record.status if record else None,
        'arrival_time': record.arrival_time.strftime('%I:%M %p') if record and record.arrival_time else None
    })
