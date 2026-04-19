# Attendance Management System (AMS)

A desktop-based Attendance Management System built with Python, Tkinter, and MySQL — developed as a mini project for B.Tech (CSE), 4th Semester.

---

## Project Overview

The **Attendance Management System (AMS)** is a GUI-based desktop application that automates the process of recording, managing, and reporting student attendance. It eliminates manual paper-based tracking and provides an efficient, reliable, and easy-to-use platform for educational institutions.

This project was developed using **Python** as the core language, **Tkinter** for the frontend GUI, **MySQL** as the backend database, and **mysql-connector-python** for database connectivity.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.x |
| Frontend (GUI) | Tkinter (Python Standard Library) |
| Backend / Database | MySQL |
| Database Connector | mysql-connector-python |
| IDE | VS Code / PyCharm / IDLE |

---

## Python Libraries Used

| Library | Purpose |
|---|---|
| `tkinter` | Building the GUI — windows, buttons, forms, tables |
| `tkinter.ttk` | Themed widgets — Treeview (table), Combobox, etc. |
| `tkinter.messagebox` | Popup alerts and confirmation dialogs |
| `mysql.connector` | Connecting Python to MySQL database |
| `datetime` | Handling date and time for attendance records |
| `os` | File and path operations |

---

## Features

- Login System — Secure admin/teacher login with credential validation against MySQL database
- Student Management — Add, update, delete, and view student records through GUI forms
- Attendance Marking — Mark attendance (Present / Absent) date-wise and subject-wise
- Attendance Reports — View and generate attendance summary for each student
- Search and Filter — Search students by name, roll number, or class
- Database Integration — All data stored persistently in MySQL via mysql-connector-python
- User-Friendly GUI — Clean and intuitive interface built with Tkinter and ttk widgets

---

## Project Structure

```
AMS_Project/
│
├── main.py                     # Entry point — launches the application
├── login.py                    # Login window and authentication logic
├── dashboard.py                # Main dashboard after login
│
├── student/
│   ├── add_student.py          # Add new student form
│   ├── update_student.py       # Update student details
│   └── view_student.py         # View all students in Treeview table
│
├── attendance/
│   ├── mark_attendance.py      # Mark attendance UI
│   └── view_attendance.py      # View attendance records
│
├── report/
│   └── attendance_report.py    # Generate attendance summary/report
│
├── db/
│   └── db_connection.py        # MySQL connection handler using mysql-connector-python
│
├── database/
│   └── ams_db.sql              # SQL script to create database and tables
│
└── README.md
```

---

## Database Schema

### students Table
```sql
CREATE TABLE students (
    student_id   INT PRIMARY KEY AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    roll_no      VARCHAR(20) UNIQUE NOT NULL,
    class        VARCHAR(50),
    email        VARCHAR(100)
);
```

### attendance Table
```sql
CREATE TABLE attendance (
    id           INT PRIMARY KEY AUTO_INCREMENT,
    student_id   INT,
    date         DATE NOT NULL,
    subject      VARCHAR(100),
    status       ENUM('Present', 'Absent') NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
```

### users Table
```sql
CREATE TABLE users (
    user_id      INT PRIMARY KEY AUTO_INCREMENT,
    username     VARCHAR(50) UNIQUE NOT NULL,
    password     VARCHAR(100) NOT NULL,
    role         VARCHAR(20) DEFAULT 'teacher'
);
```

---

## Database Connection

The `db/db_connection.py` file handles all MySQL connectivity using `mysql-connector-python`:

```python
import mysql.connector

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="your_username",
        password="your_password",
        database="ams_db"
    )
    return conn
```

---

## Setup and Installation

### Prerequisites
- Python 3.x installed
- MySQL Server installed and running
- mysql-connector-python library

### Steps

**1. Clone or Download the Project**
```bash
git clone https://github.com/yourusername/AMS_Project.git
cd AMS_Project
```

**2. Install Required Library**
```bash
pip install mysql-connector-python
```

**3. Import Database**

Open MySQL Workbench or MySQL command line and run:
```bash
mysql -u root -p < database/ams_db.sql
```

**4. Configure Database Connection**

Edit `db/db_connection.py` and update your MySQL credentials:
```python
host="localhost",
user="your_username",
password="your_password",
database="ams_db"
```

**5. Run the Project**
```bash
python main.py
```

---

## How It Works

1. Admin or Teacher logs in using valid credentials stored in the `users` table in MySQL.
2. Students are registered with their name, roll number, and class using Tkinter forms.
3. Attendance is marked daily or subject-wise — each record is saved to the `attendance` table with date and status.
4. Reports are generated by querying the MySQL database and displaying attendance percentage per student in a Tkinter Treeview.
5. mysql-connector-python handles all communication between the Python application and the MySQL database.

---

## Concepts Used

- Python OOP — Classes, Objects, Encapsulation, Inheritance
- Tkinter GUI — Tk(), Frame, Label, Entry, Button, Treeview, Combobox, messagebox
- MySQL Database — DDL, DML, Joins, Aggregate Functions (COUNT, SUM)
- mysql-connector-python — connect(), cursor(), execute(), fetchall(), commit()
- Event-Driven Programming — Button commands and event bindings in Tkinter
- Modular Programming — Separate Python files for each module (login, student, attendance)

---

## Project Category

| Field | Details |
|---|---|
| Project Type | Mini Project (Desktop Application) |
| Domain | Education / Academic Management |
| Course | B.Tech CSE — 4th Semester |
| Language | Python 3.x |
| Subject | Programming / Software Engineering |

---

## Future Enhancements

- Web-based version using Flask or Django
- Android version using Kivy or BeeWare
- Email or SMS notification to students for low attendance
- Graphical attendance charts using Matplotlib
- Export attendance report to PDF or Excel using ReportLab or openpyxl
- Password encryption using hashlib (MD5/SHA256)

---

## Developed By

**MD Ansari**
B.Tech (CSE) — Lateral Entry, 4th Semester
Engineering College, Jharkhand, India

---

## License

This project is developed for academic purposes only.
