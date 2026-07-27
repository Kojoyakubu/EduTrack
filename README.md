# EDU TRACK
### Student Attendance & Movement Notification System
**Oyoko Methodist Senior High School, Koforidua — Eastern Region**

---

## Quick Start

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up MySQL
Create the database (the app auto-creates tables on first run):
```sql
CREATE DATABASE edutrack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Or run the full schema manually:
```bash
mysql -u root -p < database/schema.sql
```

### 3. Configure environment
```bash
copy .env.example .env
```
Edit `.env` with your database credentials and email settings.

### 4. Run the application
```bash
python app.py
```
Visit **http://localhost:5000**

---

## Default Login
| Email | Password |
|-------|----------|
| `admin@edutrack.com` | `Admin@1234` |

> **Change the password immediately after first login!**

---

## Features
| Module | Description |
|--------|-------------|
| **Dashboard** | Live stats, weekly chart, recent arrivals & notifications |
| **Mark Arrival** | RFID scan or manual ID entry — marks present/late automatically |
| **Mark Departure** | Records departure time, triggers parent notification |
| **Attendance Sheet** | Full daily sheet with filter by class/date/student |
| **Student Registry** | Register, view, edit students with RFID assignment |
| **Guardians** | Multiple guardians per student, primary guardian for notifications |
| **Attendance Reports** | Date-range summary with attendance percentage per student |
| **Email Notifications** | Automated HTML email to guardians on arrival, departure, absence |
| **Admin Panel** | User management, class management, system settings |
| **Notification Log** | Full audit trail of all sent notifications |

---

## Additional Documentation
- See `SYSTEM_CAPABILITIES.md` for a detailed module-by-module explanation of what the system can do.

---

## Email Notifications Setup (Gmail)
1. Enable **2-Factor Authentication** on your Gmail account
2. Go to **Google Account → Security → App Passwords**
3. Generate an app password for "Mail"
4. Set in `.env`:
   ```
   MAIL_USERNAME=your_school_email@gmail.com
   MAIL_PASSWORD=your_16_char_app_password
   ```

---

## Project Structure
```
Edu Track/
├── app.py                  # Application factory & entry point
├── config.py               # Configuration (reads .env)
├── extensions.py           # Flask extensions (db, login_manager)
├── models.py               # SQLAlchemy models
├── requirements.txt
├── .env.example            # Environment variable template
├── database/
│   └── schema.sql          # MySQL schema
├── routes/
│   ├── auth.py             # Login / logout
│   ├── dashboard.py        # Home dashboard
│   ├── students.py         # Student CRUD
│   ├── attendance.py       # Arrival / departure marking
│   ├── reports.py          # Attendance reports
│   └── admin.py            # Admin panel
├── utils/
│   └── notifications.py    # Email notification engine
├── templates/              # Jinja2 HTML templates
└── static/
    ├── css/style.css       # Custom styles
    └── js/main.js          # Frontend JavaScript
```

---

## Technologies
- **Backend**: Python 3.11+, Flask 3, Flask-Login, Flask-SQLAlchemy
- **Database**: MySQL (via PyMySQL)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript, Chart.js, Font Awesome
- **Notifications**: SMTP Email (configurable for Gmail / any SMTP server)
- **Security**: Werkzeug password hashing, CSRF protection via Flask-WTF, session management

---

*Designed and implemented for Oyoko Methodist Senior High School.*
