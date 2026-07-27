import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import current_app
from extensions import db
from models import NotificationLog, Student, Guardian

try:
  from twilio.rest import Client as TwilioClient
  from twilio.base.exceptions import TwilioRestException
except Exception:
  TwilioClient = None
  TwilioRestException = Exception


def _build_arrival_message(student: Student, arrival_time: datetime, html=False) -> str:
    time_str = arrival_time.strftime('%I:%M %p')
    date_str = arrival_time.strftime('%A, %d %B %Y')
    school = current_app.config.get('SCHOOL_NAME', 'School')

    if html:
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; 
                    border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
          <div style="background: #1a6b3a; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">EDU TRACK</h2>
            <p style="color: #c8e6c9; margin: 4px 0 0;">Student Arrival Notification</p>
          </div>
          <div style="padding: 24px;">
            <p style="font-size: 16px;">Dear Parent/Guardian,</p>
            <p>This is to notify you that your ward, <strong>{student.full_name}</strong>,
               has <strong style="color: #1a6b3a;">arrived safely at {school}</strong>.</p>
            <table style="width:100%; border-collapse: collapse; margin: 16px 0;">
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Student</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.full_name}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Student ID</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.student_id}</td>
              </tr>
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Class</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.class_.name}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Arrival Time</td>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>{time_str}</strong></td>
              </tr>
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Date</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{date_str}</td>
              </tr>
            </table>
            <p style="color: #666; font-size: 13px;">This is an automated notification from 
               {school}. Please do not reply to this email.</p>
          </div>
        </div>
        """
    return (f"EDU TRACK - ARRIVAL ALERT\n"
            f"Dear Parent/Guardian,\n"
            f"{student.full_name} (ID: {student.student_id}, Class: {student.class_.name}) "
            f"has arrived at {school} at {time_str} on {date_str}.\n"
            f"This is an automated message from {school}.")


def _build_departure_message(student: Student, departure_time: datetime, html=False) -> str:
    time_str = departure_time.strftime('%I:%M %p')
    date_str = departure_time.strftime('%A, %d %B %Y')
    school = current_app.config.get('SCHOOL_NAME', 'School')

    if html:
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; 
                    border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
          <div style="background: #1a3a6b; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">EDU TRACK</h2>
            <p style="color: #bbdefb; margin: 4px 0 0;">Student Departure Notification</p>
          </div>
          <div style="padding: 24px;">
            <p style="font-size: 16px;">Dear Parent/Guardian,</p>
            <p>This is to notify you that your ward, <strong>{student.full_name}</strong>,
               has <strong style="color: #1a3a6b;">left {school}</strong> and is on their way home.</p>
            <table style="width:100%; border-collapse: collapse; margin: 16px 0;">
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Student</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.full_name}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Student ID</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.student_id}</td>
              </tr>
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Class</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.class_.name}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Departure Time</td>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>{time_str}</strong></td>
              </tr>
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Date</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{date_str}</td>
              </tr>
            </table>
            <p style="color: #666; font-size: 13px;">This is an automated notification from 
               {school}. Please do not reply to this email.</p>
          </div>
        </div>
        """
    return (f"EDU TRACK - DEPARTURE ALERT\n"
            f"Dear Parent/Guardian,\n"
            f"{student.full_name} (ID: {student.student_id}, Class: {student.class_.name}) "
            f"has left {school} at {time_str} on {date_str}.\n"
            f"Please ensure they arrive home safely.\n"
            f"This is an automated message from {school}.")


def _build_absent_message(student: Student, date: datetime, html=False) -> str:
    date_str = date.strftime('%A, %d %B %Y')
    school = current_app.config.get('SCHOOL_NAME', 'School')

    if html:
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; 
                    border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
          <div style="background: #c0392b; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">EDU TRACK</h2>
            <p style="color: #ffd5d5; margin: 4px 0 0;">Absence Notification</p>
          </div>
          <div style="padding: 24px;">
            <p style="font-size: 16px;">Dear Parent/Guardian,</p>
            <p>This is to inform you that your ward, <strong>{student.full_name}</strong>,
               was <strong style="color: #c0392b;">absent from {school}</strong> today.</p>
            <table style="width:100%; border-collapse: collapse; margin: 16px 0;">
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Student</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.full_name}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Student ID</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.student_id}</td>
              </tr>
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Date</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{date_str}</td>
              </tr>
            </table>
            <p>If this absence was not authorized, please contact the school immediately.</p>
            <p style="color: #666; font-size: 13px;">This is an automated notification from 
               {school}. Please do not reply to this email.</p>
          </div>
        </div>
        """
    return (f"EDU TRACK - ABSENCE ALERT\n"
            f"Dear Parent/Guardian,\n"
            f"{student.full_name} (ID: {student.student_id}) was absent from {school} on {date_str}.\n"
            f"If this was not expected, please contact the school.\n"
            f"This is an automated message from {school}.")


def _build_late_message(student: Student, late_time: datetime, html=False) -> str:
    time_str = late_time.strftime('%I:%M %p')
    date_str = late_time.strftime('%A, %d %B %Y')
    school = current_app.config.get('SCHOOL_NAME', 'School')

    if html:
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;
                    border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
          <div style="background: #d68910; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">EDU TRACK</h2>
            <p style="color: #fff4d6; margin: 4px 0 0;">Late Arrival Notification</p>
          </div>
          <div style="padding: 24px;">
            <p style="font-size: 16px;">Dear Parent/Guardian,</p>
            <p>This is to inform you that your ward, <strong>{student.full_name}</strong>,
               checked in <strong style="color: #d68910;">late at {school}</strong>.</p>
            <table style="width:100%; border-collapse: collapse; margin: 16px 0;">
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Student</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.full_name}</td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Student ID</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{student.student_id}</td>
              </tr>
              <tr style="background: #f5f5f5;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Arrival Time</td>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>{time_str}</strong></td>
              </tr>
              <tr>
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Date</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{date_str}</td>
              </tr>
            </table>
            <p style="color: #666; font-size: 13px;">This is an automated notification from
               {school}. Please do not reply to this email.</p>
          </div>
        </div>
        """
    return (f"EDU TRACK - LATE ARRIVAL ALERT\n"
            f"Dear Parent/Guardian,\n"
            f"{student.full_name} (ID: {student.student_id}) checked in late at {school} "
            f"at {time_str} on {date_str}.\n"
            f"This is an automated message from {school}.")


def _build_sms_message(student: Student, event_type: str, event_time: datetime) -> str:
    school = current_app.config.get('SCHOOL_SHORT', 'EDU TRACK')
    time_str = event_time.strftime('%I:%M %p')
    date_str = event_time.strftime('%d %b %Y')

    if event_type == 'arrival':
        return (f"{school}: {student.full_name} ({student.student_id}) arrived at school "
                f"at {time_str} on {date_str}.")
    if event_type == 'departure':
        return (f"{school}: {student.full_name} ({student.student_id}) left school "
                f"at {time_str} on {date_str}.")
    if event_type == 'late':
        return (f"{school}: Late alert - {student.full_name} ({student.student_id}) "
                f"checked in at {time_str} on {date_str}.")
    return (f"{school}: Absence alert - {student.full_name} ({student.student_id}) "
            f"was marked absent on {date_str}.")


def _normalize_phone(phone: str) -> str:
    phone = (phone or '').strip().replace(' ', '')
    phone = phone.replace('-', '')

    if phone.startswith('00'):
        phone = '+' + phone[2:]
    elif phone.startswith('0') and len(phone) == 10:
        # Default local Ghana number format to +233.
        phone = '+233' + phone[1:]
    elif phone.startswith('233') and len(phone) == 12:
        phone = '+' + phone

    return phone


def _clean_config(value: str | None) -> str | None:
    if isinstance(value, str):
        value = value.strip()
    return value or None


def _twilio_error_hint(error_code: int | None) -> str:
  if error_code == 21704:
    return 'Messaging Service has no sender. Attach a Twilio phone number to the Messaging Service or use TWILIO_FROM_NUMBER.'
  if error_code == 21608:
    return 'Trial account can only send to verified recipient numbers.'
  return ''


def send_email_notification(recipient_email: str, subject: str, html_body: str,
                            plain_body: str) -> tuple[bool, str]:
    """Send an email and return (success, error_message)."""
    try:
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_port = current_app.config.get('MAIL_PORT', 587)
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER')

        if not mail_username or not mail_password:
            return False, 'Email credentials not configured.'

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"EDU TRACK <{mail_sender}>"
        msg['To'] = recipient_email

        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(mail_server, mail_port) as server:
            server.ehlo()
            server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_sender, recipient_email, msg.as_string())

        return True, ''
    except Exception as e:
        return False, str(e)


def send_sms_notification(recipient_phone: str, message: str) -> tuple[str, str]:
    """Send an SMS with Twilio and return (log_status, details)."""
    try:
        if TwilioClient is None:
            return 'failed', 'Twilio package not installed.'

        account_sid = _clean_config(current_app.config.get('TWILIO_ACCOUNT_SID'))
        auth_token = _clean_config(current_app.config.get('TWILIO_AUTH_TOKEN'))
        from_number = _clean_config(current_app.config.get('TWILIO_FROM_NUMBER'))
        messaging_service_sid = _clean_config(current_app.config.get('TWILIO_MESSAGING_SERVICE_SID'))

        if not account_sid or not auth_token:
            return 'failed', 'Twilio credentials not configured.'

        to_number = _normalize_phone(recipient_phone)
        if not to_number.startswith('+'):
            return 'failed', 'Phone number must include country code (e.g. +233...).'

        if not from_number and not messaging_service_sid:
            return 'failed', 'Twilio sender not configured (from number or messaging service SID).'

        client = TwilioClient(account_sid, auth_token)
        base_payload = {
            'to': to_number,
            'body': message,
        }
        payload = dict(base_payload)
        if messaging_service_sid:
          payload['messaging_service_sid'] = messaging_service_sid
        else:
          payload['from_'] = from_number

        try:
          twilio_message = client.messages.create(**payload)
        except TwilioRestException as e:
          # If Messaging Service has no sender (21704), retry with explicit From number if available.
          if messaging_service_sid and from_number and getattr(e, 'code', None) == 21704:
            twilio_message = client.messages.create(**{**base_payload, 'from_': from_number})
          else:
            code = getattr(e, 'code', None)
            hint = _twilio_error_hint(code)
            detail = f'Twilio error_code: {code}, error: {e.msg if hasattr(e, "msg") else str(e)}'
            if hint:
              detail = f'{detail}. Hint: {hint}'
            return 'failed', detail

        twilio_status = (twilio_message.status or 'queued').lower()
        twilio_sid = twilio_message.sid
        twilio_error_code = twilio_message.error_code
        twilio_error_message = twilio_message.error_message

        if twilio_error_code:
          hint = _twilio_error_hint(twilio_error_code)
          return 'failed', (
            f'Twilio status: {twilio_status}, error_code: {twilio_error_code}, '
            f'error: {twilio_error_message or "unknown"} (SID: {twilio_sid})'
            + (f'. Hint: {hint}' if hint else '')
          )

        if twilio_status in ('failed', 'undelivered', 'canceled'):
          return 'failed', f'Twilio status: {twilio_status} (SID: {twilio_sid})'

        if twilio_status in ('sent', 'delivered'):
          return 'sent', f'Twilio status: {twilio_status} (SID: {twilio_sid})'

        # Twilio creation success means accepted/queued, not final handset delivery.
        return 'pending', f'Twilio status: {twilio_status} (SID: {twilio_sid})'
    except Exception as e:
        return 'failed', str(e)


def _extract_sid(details: str | None) -> str | None:
    if not details:
        return None
    match = re.search(r'SID:\s*(SM[a-zA-Z0-9]+)', details)
    return match.group(1) if match else None


def refresh_pending_sms_logs(limit: int = 100) -> int:
    """Refresh pending SMS delivery status from Twilio. Returns number of updated logs."""
    if TwilioClient is None:
        return 0

    account_sid = _clean_config(current_app.config.get('TWILIO_ACCOUNT_SID'))
    auth_token = _clean_config(current_app.config.get('TWILIO_AUTH_TOKEN'))
    if not account_sid or not auth_token:
        return 0

    pending_logs = (NotificationLog.query
                    .filter_by(channel='sms', status='pending')
                    .order_by(NotificationLog.sent_at.desc())
                    .limit(limit)
                    .all())
    if not pending_logs:
        return 0

    client = TwilioClient(account_sid, auth_token)
    updates = 0

    for log in pending_logs:
        sid = _extract_sid(log.error_message)
        if not sid:
            continue

        try:
            twilio_message = client.messages(sid).fetch()
            twilio_status = (twilio_message.status or 'queued').lower()
            twilio_error_code = twilio_message.error_code
            twilio_error_message = twilio_message.error_message

            if twilio_status in ('delivered', 'sent'):
                log.status = 'sent'
                log.error_message = f'Twilio status: {twilio_status} (SID: {sid})'
                updates += 1
            elif twilio_status in ('failed', 'undelivered', 'canceled') or twilio_error_code:
                log.status = 'failed'
                hint = _twilio_error_hint(twilio_error_code)
                log.error_message = (
                    f'Twilio status: {twilio_status}, error_code: {twilio_error_code or "n/a"}, '
                    f'error: {twilio_error_message or "unknown"} (SID: {sid})'
                    + (f'. Hint: {hint}' if hint else '')
                )
                updates += 1
            else:
                log.error_message = f'Twilio status: {twilio_status} (SID: {sid})'
        except Exception as e:
            # Keep pending if Twilio status cannot be fetched right now.
            log.error_message = f'{log.error_message or ""} | refresh_error: {e}'.strip(' |')

    if updates:
        db.session.commit()

    return updates


def notify_guardians(student: Student, event_type: str,
           event_time: datetime = None) -> list[NotificationLog]:
  """
  Notify all guardians of a student about an attendance event.
  event_type: 'arrival' | 'departure' | 'absent' | 'late'
  Returns a list of NotificationLog entries.
  """
  from models import Setting

  notifications_enabled = Setting.get('notifications_enabled', '1')
  if notifications_enabled != '1':
    return []

  if event_time is None:
    event_time = datetime.utcnow()

  notification_channel = (Setting.get('notification_channel', 'email') or 'email').lower()
  if notification_channel not in ('email', 'sms', 'both'):
    notification_channel = 'email'

  logs = []
  guardians = student.guardians.all()

  if event_type == 'arrival':
    subject = f"[EDU TRACK] {student.full_name} has arrived at school"
    html_body = _build_arrival_message(student, event_time, html=True)
    plain_body = _build_arrival_message(student, event_time, html=False)
  elif event_type == 'departure':
    subject = f"[EDU TRACK] {student.full_name} has left school"
    html_body = _build_departure_message(student, event_time, html=True)
    plain_body = _build_departure_message(student, event_time, html=False)
  elif event_type == 'late':
    subject = f"[EDU TRACK] Late Arrival Alert - {student.full_name}"
    html_body = _build_late_message(student, event_time, html=True)
    plain_body = _build_late_message(student, event_time, html=False)
  elif event_type == 'absent':
    subject = f"[EDU TRACK] Absence Alert - {student.full_name}"
    html_body = _build_absent_message(student, event_time, html=True)
    plain_body = _build_absent_message(student, event_time, html=False)
  else:
    return logs

  sms_body = _build_sms_message(student, event_type, event_time)

  for guardian in guardians:
    if notification_channel in ('email', 'both') and guardian.email:
      success, error = send_email_notification(guardian.email, subject, html_body, plain_body)
      email_log = NotificationLog(
        student_id=student.id,
        guardian_id=guardian.id,
        event_type=event_type,
        channel='email',
        recipient_contact=guardian.email,
        message=plain_body,
        status='sent' if success else 'failed',
        sent_at=datetime.utcnow(),
        error_message=error if not success else None
      )
      db.session.add(email_log)
      logs.append(email_log)

    if notification_channel in ('sms', 'both') and guardian.phone:
      normalized_phone = _normalize_phone(guardian.phone)
      sms_status, sms_details = send_sms_notification(normalized_phone, sms_body)
      sms_log = NotificationLog(
        student_id=student.id,
        guardian_id=guardian.id,
        event_type=event_type,
        channel='sms',
        recipient_contact=normalized_phone,
        message=sms_body,
        status=sms_status,
        sent_at=datetime.utcnow(),
        error_message=sms_details
      )
      db.session.add(sms_log)
      logs.append(sms_log)

  db.session.commit()
  return logs
