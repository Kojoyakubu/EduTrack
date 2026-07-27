# EDU TRACK System Capabilities

## Purpose and Scope
EDU TRACK is a web-based student attendance and movement monitoring system for schools. It records student arrival and departure events, tracks attendance outcomes (present, late, absent), and sends guardian notifications through configurable channels.

Primary scope:
- Daily attendance operations for staff.
- Student profile and guardian management.
- School-level and student-level attendance reporting.
- Administrative control over users, classes, and system behavior.
- Notification logging and delivery status visibility.

## User Roles and Access
The system currently supports two user roles.

### 1) Administrator
Administrators can:
- Access all staff features.
- Create and manage system users.
- Activate/deactivate user accounts.
- Manage classes.
- Configure school timing and notification settings.
- View notification logs (email and SMS).

### 2) Staff
Staff can:
- Log in and access dashboard, students, attendance, and reports modules.
- Register and maintain student records.
- Mark arrival, departure, and absence.
- Trigger automated guardian notifications through attendance actions.
- Change their own password.

## Authentication and Session Management
The system provides:
- Email/password login.
- Optional remember-me session persistence.
- Logout endpoint.
- Route protection for authenticated pages.
- Role-based restriction for administrator-only pages.
- Password hashing (not plaintext storage).
- Last login timestamp update after successful sign-in.

## Core Functional Modules

### Dashboard Module
The dashboard provides a live operational overview of attendance and notifications.

What it shows:
- Total active students.
- Present count for today (present + late).
- Absent count for today.
- Late arrivals count for today.
- Departed count for today.
- Recent arrival records.
- Recent notification activity with status.
- Weekly attendance chart (present vs absent).

Operational value:
- Immediate visibility for school leadership and attendance staff.
- Faster identification of attendance risk trends.

### Student Registry Module
The student module is a full record-management workflow.

Capabilities:
- List students with pagination.
- Search by student name or student ID.
- Filter by class.
- Register a new student profile.
- Assign optional RFID tag per student.
- Capture demographics (DOB, gender, class, address).
- View student profile details.
- Edit student profile and RFID assignment.
- Deactivate student records (admin-only action).

Validation and safety behavior:
- Student ID must be unique.
- RFID tag must be unique when provided.
- Required fields are enforced during registration.
- Date of birth parsing is validated.
- Deactivation uses a soft approach (is_active flag), not hard delete.

### Guardian Management
Guardian data is linked to students and used for notifications.

Capabilities:
- Create an initial primary guardian during student registration.
- Add additional guardians to a student profile.
- Store guardian relationship, phone, and optional email.
- Select notification recipients from linked guardians.

Behavior details:
- Primary guardian preference is supported.
- If no primary guardian is marked, the first available guardian can still be used by helper logic.

### Attendance Operations Module
The attendance module handles daily movement and status records.

Capabilities:
- Daily attendance sheet with per-date viewing.
- Class filtering and student search in attendance view.
- Mark arrival by entering either student ID or RFID tag.
- Mark departure by entering either student ID or RFID tag.
- Mark student absent from attendance sheet.
- JSON lookup endpoint for scan/ID quick checks.

Business rules enforced:
- Arrival cannot be marked twice for the same student/date.
- Departure requires a same-day arrival record first.
- Departure cannot be marked twice for the same student/date.
- One attendance record per student per date.
- Late detection uses configurable cutoff plus threshold.

Status logic:
- Present: arrival recorded before late boundary.
- Late: arrival recorded after late boundary.
- Absent: explicitly marked by staff.
- Excused: defined in model and schema for supported status value storage.

### Reporting Module
The reporting module supports operational and analytical views.

Capabilities:
- Attendance summary for a selected date range.
- Optional class filter for focused reporting.
- Per-student totals across selected period:
  - Total recorded days.
  - Present days.
  - Absent days.
  - Late days.
- Student-specific detailed attendance history page.

Use cases:
- Parent meetings and student counseling evidence.
- Class-level attendance trend checks.
- Administrative monitoring for compliance and intervention.

### Notifications Module
The system supports guardian notifications for attendance events.

Supported events:
- Arrival.
- Departure.
- Late arrival.
- Absence.

Supported channels:
- Email.
- SMS (Twilio integration).
- Both channels simultaneously.

Message behavior:
- Event-specific templates are generated for email (HTML + plain text).
- Short SMS templates are generated per event.
- Notification channel is controlled by admin settings.
- Global notifications can be enabled or disabled in settings.

Delivery logging and tracking:
- Each send attempt is recorded in notification logs.
- Log tracks event type, channel, recipient, content, status, timestamp, and error details.
- SMS pending logs can be refreshed against Twilio delivery status.

Failure resilience:
- Email failures are captured and logged.
- SMS failures include Twilio error diagnostics when available.
- Pending SMS state is supported where delivery is queued, not final.

### Administration Module
The admin area centralizes system configuration and governance.

Capabilities:
- User management:
  - View all users.
  - Create users.
  - Toggle active/inactive status.
  - Prevent self-deactivation.
- Class management:
  - View classes.
  - Add classes.
  - Prevent duplicate class names.
- Settings management:
  - Arrival recording start time.
  - On-time arrival cutoff time.
  - Expected departure time.
  - Late threshold minutes.
  - Notifications enabled/disabled.
  - Notification channel (email, SMS, both).
- Notification audit:
  - Paginated log view.
  - Status visibility for sent/failed/pending records.

### Password Management
Users can change their own password.

Validation rules:
- Current password must match account.
- New password minimum length is enforced.
- New password and confirmation must match.

## Data Model Capabilities
The system persists structured entities for school operations.

Main entities:
- User.
- Class.
- Student.
- Guardian.
- Attendance.
- NotificationLog.
- Setting.

Key model-level capabilities:
- Unique constraints for identity fields.
- One attendance record per student per date via composite uniqueness.
- Relationship mapping for student-guardian, student-attendance, and notification associations.
- Configurable key-value settings retrieval and updates.

## Automation and Default Provisioning
On startup, the application can initialize baseline data.

Seeded defaults include:
- Default administrator account.
- Common class list.
- Default timing and notification settings.

Operational benefit:
- Faster first-time deployment with reduced manual setup.

## Configuration Capabilities
The system reads runtime configuration from environment variables.

Configurable areas:
- Flask secret and database connection.
- SMTP email server credentials.
- Twilio SMS credentials and sender info.
- School naming values used in notifications and UI text.

Flexibility outcome:
- The same codebase can be used in different institutions/environments by changing configuration.

## API/Integration Surface
Current built-in integration points:
- Attendance quick-lookup endpoint returning JSON for ID/RFID scans.
- SMTP integration for email sending.
- Twilio integration for SMS sending and delivery refresh.

## User Interface Behaviors
The frontend includes practical workflow enhancements.

UI behaviors:
- Live clock on arrival/departure pages.
- Auto-dismiss flash messages.
- Responsive sidebar behavior for smaller screens.
- User dropdown interactions.
- Keyboard-enter support for fast scan submission.
- Dashboard chart visualization for weekly attendance.

## Auditability and Traceability
The system supports traceability for attendance communication and user activity context.

What is traceable:
- Who marked arrival/departure (user linkage in attendance records).
- What notifications were attempted/sent/failed.
- Recipient and message content for each notification log entry.
- Last login timestamp for users.

## Operational Strengths
The current implementation is strongest in:
- Day-to-day attendance recording with low interaction friction.
- Guardian communication automation tied directly to attendance events.
- Admin control over timing thresholds and notification strategy.
- Practical reporting for school operations.

## Current Boundaries
The system currently does not appear to include these as built-in features:
- Multi-school tenancy in one instance.
- Full timetable/schedule management.
- Student promotion/graduation workflow automation.
- Native mobile app clients.
- Biometric integration beyond RFID/identifier flow.
- Advanced analytics or predictive attendance risk scoring.

These can be added incrementally without changing the core attendance foundation.

## Summary
EDU TRACK can operate as a complete attendance and student movement monitoring platform for a single school environment, with role-based access, event-driven notifications, operational reporting, and auditable logs. It is production-oriented for school-day workflows and has a clear path for future expansion into deeper analytics and broader school management features.
