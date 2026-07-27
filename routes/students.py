from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Student, Guardian, Class

students_bp = Blueprint('students', __name__, url_prefix='/students')


@students_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    class_filter = request.args.get('class_id', '')
    page = request.args.get('page', 1, type=int)

    query = Student.query.filter_by(is_active=True)
    if search:
        query = query.filter(
            (Student.full_name.ilike(f'%{search}%')) |
            (Student.student_id.ilike(f'%{search}%'))
        )
    if class_filter:
        query = query.filter_by(class_id=class_filter)

    students = query.order_by(Student.full_name).paginate(page=page, per_page=20)
    classes = Class.query.order_by(Class.name).all()

    return render_template('students/index.html',
                           students=students, classes=classes,
                           search=search, class_filter=class_filter)


@students_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    classes = Class.query.order_by(Class.name).all()

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        full_name = request.form.get('full_name', '').strip()
        dob = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        class_id = request.form.get('class_id')
        rfid_tag = request.form.get('rfid_tag', '').strip() or None
        address = request.form.get('address', '').strip()

        # Guardian info
        g_name = request.form.get('g_name', '').strip()
        g_relationship = request.form.get('g_relationship', '').strip()
        g_phone = request.form.get('g_phone', '').strip()
        g_email = request.form.get('g_email', '').strip() or None

        if not all([student_id, full_name, gender, class_id, g_name, g_relationship, g_phone]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('students/register.html', classes=classes)

        if Student.query.filter_by(student_id=student_id).first():
            flash('A student with this ID already exists.', 'danger')
            return render_template('students/register.html', classes=classes)

        if rfid_tag and Student.query.filter_by(rfid_tag=rfid_tag).first():
            flash('This RFID tag is already assigned to another student.', 'danger')
            return render_template('students/register.html', classes=classes)

        from datetime import date as date_type
        dob_parsed = None
        if dob:
            try:
                dob_parsed = date_type.fromisoformat(dob)
            except ValueError:
                flash('Invalid date of birth format.', 'danger')
                return render_template('students/register.html', classes=classes)

        student = Student(
            student_id=student_id,
            full_name=full_name,
            date_of_birth=dob_parsed,
            gender=gender,
            class_id=int(class_id),
            rfid_tag=rfid_tag,
            address=address
        )
        db.session.add(student)
        db.session.flush()

        guardian = Guardian(
            student_id=student.id,
            full_name=g_name,
            relationship=g_relationship,
            phone=g_phone,
            email=g_email,
            is_primary=True
        )
        db.session.add(guardian)
        db.session.commit()

        flash(f'Student {full_name} registered successfully.', 'success')
        return redirect(url_for('students.detail', student_id=student.id))

    return render_template('students/register.html', classes=classes)


@students_bp.route('/<int:student_id>')
@login_required
def detail(student_id):
    student = Student.query.get_or_404(student_id)
    from datetime import date
    recent_attendance = student.attendance_records.order_by(
        db.text('date DESC')
    ).limit(30).all()
    return render_template('students/detail.html',
                           student=student,
                           recent_attendance=recent_attendance,
                           today=date.today())


@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(student_id):
    student = Student.query.get_or_404(student_id)
    classes = Class.query.order_by(Class.name).all()

    if request.method == 'POST':
        student.full_name = request.form.get('full_name', '').strip()
        student.gender = request.form.get('gender')
        student.class_id = int(request.form.get('class_id'))
        student.address = request.form.get('address', '').strip()
        rfid_tag = request.form.get('rfid_tag', '').strip() or None

        if rfid_tag and rfid_tag != student.rfid_tag:
            existing = Student.query.filter_by(rfid_tag=rfid_tag).first()
            if existing and existing.id != student.id:
                flash('This RFID tag is already in use.', 'danger')
                return render_template('students/edit.html', student=student, classes=classes)
        student.rfid_tag = rfid_tag

        dob = request.form.get('date_of_birth')
        if dob:
            from datetime import date as date_type
            try:
                student.date_of_birth = date_type.fromisoformat(dob)
            except ValueError:
                pass

        db.session.commit()
        flash('Student information updated.', 'success')
        return redirect(url_for('students.detail', student_id=student.id))

    return render_template('students/edit.html', student=student, classes=classes)


@students_bp.route('/<int:student_id>/add-guardian', methods=['POST'])
@login_required
def add_guardian(student_id):
    student = Student.query.get_or_404(student_id)
    g_name = request.form.get('g_name', '').strip()
    g_relationship = request.form.get('g_relationship', '').strip()
    g_phone = request.form.get('g_phone', '').strip()
    g_email = request.form.get('g_email', '').strip() or None

    if not all([g_name, g_relationship, g_phone]):
        flash('Guardian name, relationship, and phone are required.', 'danger')
    else:
        guardian = Guardian(
            student_id=student.id,
            full_name=g_name,
            relationship=g_relationship,
            phone=g_phone,
            email=g_email,
            is_primary=False
        )
        db.session.add(guardian)
        db.session.commit()
        flash('Guardian added successfully.', 'success')

    return redirect(url_for('students.detail', student_id=student.id))


@students_bp.route('/<int:student_id>/deactivate', methods=['POST'])
@login_required
def deactivate(student_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('students.index'))
    student = Student.query.get_or_404(student_id)
    student.is_active = False
    db.session.commit()
    flash(f'{student.full_name} has been deactivated.', 'warning')
    return redirect(url_for('students.index'))
