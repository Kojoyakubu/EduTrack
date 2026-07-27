-- EDU TRACK Database Schema
-- Oyoko Methodist Senior High School
-- Student Attendance and Movement Notification System

CREATE DATABASE IF NOT EXISTS edutrack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE edutrack;

-- Users (Staff / Admin)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role ENUM('admin', 'staff') NOT NULL DEFAULT 'staff',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- Classes
CREATE TABLE IF NOT EXISTS classes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(120)
);

-- Students
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    date_of_birth DATE,
    gender ENUM('Male', 'Female') NOT NULL,
    class_id INT NOT NULL,
    rfid_tag VARCHAR(50) UNIQUE,
    photo VARCHAR(256),
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES classes(id)
);

-- Guardians
CREATE TABLE IF NOT EXISTS guardians (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    relationship VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(120),
    is_primary BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- Attendance Records
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    arrival_time DATETIME,
    departure_time DATETIME,
    arrival_marked_by INT,
    departure_marked_by INT,
    status ENUM('present', 'late', 'absent', 'excused') DEFAULT 'present',
    notes TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (arrival_marked_by) REFERENCES users(id),
    FOREIGN KEY (departure_marked_by) REFERENCES users(id),
    UNIQUE KEY unique_student_date (student_id, date)
);

-- Notification Logs
CREATE TABLE IF NOT EXISTS notification_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    guardian_id INT,
    event_type ENUM('arrival', 'departure', 'absent', 'late') NOT NULL,
    channel ENUM('email', 'sms', 'both') NOT NULL DEFAULT 'email',
    recipient_contact VARCHAR(120) NOT NULL,
    message TEXT NOT NULL,
    status ENUM('sent', 'failed', 'pending') DEFAULT 'pending',
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (guardian_id) REFERENCES guardians(id)
);

-- System Settings
CREATE TABLE IF NOT EXISTS settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(80) NOT NULL UNIQUE,
    setting_value TEXT,
    description VARCHAR(256)
);

-- Default settings
INSERT INTO settings (setting_key, setting_value, description) VALUES
('school_arrival_start', '06:00', 'Time from which arrivals are recorded'),
('school_arrival_end', '07:30', 'Latest on-time arrival'),
('school_departure_time', '15:30', 'Expected departure time'),
('late_threshold_minutes', '30', 'Minutes after arrival_end to mark as late'),
('notifications_enabled', '1', 'Enable/disable all notifications'),
('notification_channel', 'email', 'Default notification channel: email, sms, both')
ON DUPLICATE KEY UPDATE setting_key=setting_key;

-- Default admin user (password: Admin@1234)
INSERT INTO users (full_name, email, password_hash, role) VALUES 
('System Administrator', 'admin@edutrack.com', 
 'pbkdf2:sha256:600000$edutrack$c7f85c0d8c3a2e4f6b9d1e3f5a7c9b2d4e6f8a0c2b4d6e8f0a2c4b6d8e0f2a4',
 'admin')
ON DUPLICATE KEY UPDATE email=email;

-- Sample classes
INSERT INTO classes (name, description) VALUES
('Form 1A', 'First Year - Section A'),
('Form 1B', 'First Year - Section B'),
('Form 2A', 'Second Year - Section A'),
('Form 2B', 'Second Year - Section B'),
('Form 3A', 'Third Year - Section A'),
('Form 3B', 'Third Year - Section B')
ON DUPLICATE KEY UPDATE name=name;
