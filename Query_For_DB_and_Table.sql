CREATE DATABASE ams_db;
USE ams_db;

-- Teachers table
CREATE TABLE IF NOT EXISTS teachers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
	email VARCHAR(100) NOT NULL,
    password VARCHAR(250) NOT NULL,
    subject VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll_no VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(250) NOT NULL,
    class VARCHAR(50),
    dob varchar(20) NOT NULL,
    phone varchar(15) NOT NULL,
    blood_group varchar(5) NOT NULL,
    face_encoding LONGBLOB,
    qr_code_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    teacher_id INT,
    subject varchar(100) NOT NULL,
    date DATE,
    status VARCHAR(10),
    method VARCHAR(20),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE current_timestamp
);

-- ── 3. Active Classes table (NAYA) ──────────────
CREATE TABLE active_classes (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id  INT          NOT NULL,
  subject     VARCHAR(100) NOT NULL,
  start_time  DATETIME     DEFAULT NOW(),
  active      TINYINT(1)   DEFAULT 1,
  UNIQUE KEY uniq_teacher (teacher_id),
  FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);
