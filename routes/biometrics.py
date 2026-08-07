from flask import Blueprint, current_app, request, jsonify, session
from flask_login import login_required
from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes, options_to_json_dict, parse_registration_credential_json, parse_authentication_credential_json
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, AuthenticatorSelectionCriteria, UserVerificationRequirement, AuthenticatorAttachment
from extensions import db
from models import Student, BiometricCredential
import secrets

biometric_bp = Blueprint('biometric', __name__, url_prefix='/biometric')


@biometric_bp.route('/register-options/<int:student_id>', methods=['GET'])
@login_required
def register_options(student_id):
    student = Student.query.get_or_404(student_id)
    challenge = secrets.token_bytes(32)
    session['webauthn_registration_student_id'] = student.id
    session['webauthn_registration_challenge'] = bytes_to_base64url(challenge)

    # Extract RP ID from the request hostname (without port)
    rp_id = request.host.split(':')[0]

    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=current_app.config.get('WEBAUTHN_RP_NAME', 'EDU TRACK'),
        user_id=student.id.to_bytes((student.id.bit_length() + 7) // 8 or 1, 'big'),
        user_name=student.student_id,
        user_display_name=student.full_name,
        challenge=challenge,
        timeout=60000,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
            authenticator_attachment=AuthenticatorAttachment.PLATFORM
        ),
    )
    return jsonify(options_to_json_dict(options))


@biometric_bp.route('/register', methods=['POST'])
@login_required
def register():
    payload = request.get_json(silent=True) or {}
    credential = payload.get('credential')
    if not credential:
        return jsonify({'ok': False, 'message': 'Missing WebAuthn registration response.'}), 400

    student_id = session.get('webauthn_registration_student_id')
    expected_challenge = session.get('webauthn_registration_challenge')
    if not student_id or not expected_challenge:
        return jsonify({'ok': False, 'message': 'Challenge not found. Start registration again.'}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'ok': False, 'message': 'Student not found.'}), 404

    # Extract RP ID from the request hostname (without port)
    rp_id = request.host.split(':')[0]
    
    # Build expected origin from request
    expected_origin = f"{'https' if request.is_secure else 'http'}://{request.host}"

    verified = verify_registration_response(
        credential=parse_registration_credential_json(credential),
        expected_challenge=base64url_to_bytes(expected_challenge),
        expected_rp_id=rp_id,
        expected_origin=[expected_origin],
        require_user_verification=True,
    )

    existing = BiometricCredential.query.filter_by(student_id=student.id).first()
    if existing:
        existing.credential_id = bytes_to_base64url(verified.credential_id)
        existing.public_key = verified.credential_public_key.hex()
        existing.sign_count = verified.sign_count
    else:
        record = BiometricCredential(
            student_id=student.id,
            credential_id=bytes_to_base64url(verified.credential_id),
            public_key=verified.credential_public_key.hex(),
            sign_count=verified.sign_count,
        )
        db.session.add(record)

    db.session.commit()
    session.pop('webauthn_registration_student_id', None)
    session.pop('webauthn_registration_challenge', None)
    return jsonify({'ok': True, 'message': 'Fingerprint credential enrolled successfully.'})


@biometric_bp.route('/auth-options', methods=['GET'])
@login_required
def auth_options():
    credentials = BiometricCredential.query.all()
    if not credentials:
        return jsonify({'ok': False, 'message': 'No biometric credentials are enrolled yet.'}), 404

    challenge = secrets.token_bytes(32)
    session['webauthn_auth_challenge'] = bytes_to_base64url(challenge)

    # Extract RP ID from the request hostname (without port)
    rp_id = request.host.split(':')[0]

    options = generate_authentication_options(
        rp_id=rp_id,
        challenge=challenge,
        timeout=60000,
        allow_credentials=[
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(record.credential_id),
                transports=['internal']
            ) for record in credentials
        ],
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    return jsonify(options_to_json_dict(options))


@biometric_bp.route('/verify', methods=['POST'])
@login_required
def verify():
    payload = request.get_json(silent=True) or {}
    credential = payload.get('credential')
    if not credential:
        return jsonify({'ok': False, 'message': 'Missing WebAuthn assertion response.'}), 400

    expected_challenge = session.get('webauthn_auth_challenge')
    if not expected_challenge:
        return jsonify({'ok': False, 'message': 'Authentication challenge expired. Try again.'}), 400

    records = BiometricCredential.query.all()
    if not records:
        return jsonify({'ok': False, 'message': 'No biometric credential is registered for this student.'}), 404

    credential_payload = parse_authentication_credential_json(credential)
    
    # Extract RP ID and origin from the request
    rp_id = request.host.split(':')[0]
    expected_origin = f"{'https' if request.is_secure else 'http'}://{request.host}"
    
    verification_context = {
        'expected_challenge': base64url_to_bytes(expected_challenge),
        'expected_rp_id': rp_id,
        'expected_origin': [expected_origin],
        'require_user_verification': True,
    }

    verified_record = None
    for credential_record in records:
        try:
            verified = verify_authentication_response(
                credential=credential_payload,
                expected_challenge=verification_context['expected_challenge'],
                expected_rp_id=verification_context['expected_rp_id'],
                expected_origin=verification_context['expected_origin'],
                credential_public_key=bytes.fromhex(credential_record.public_key),
                credential_current_sign_count=credential_record.sign_count,
                require_user_verification=verification_context['require_user_verification'],
            )
            verified_record = credential_record
            credential_record.sign_count = int(verified.new_sign_count)
            db.session.commit()
            break
        except Exception:
            continue

    if not verified_record:
        return jsonify({'ok': False, 'message': 'Fingerprint authentication failed or did not match an enrolled credential.'}), 401

    session.pop('webauthn_auth_challenge', None)

    student = Student.query.get(verified_record.student_id)
    return jsonify({
        'ok': True,
        'student_id': student.student_id,
        'full_name': student.full_name,
        'class_name': student.class_.name,
    })
