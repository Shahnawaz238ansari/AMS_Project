# Attendance Management System (AMS)

A desktop application for tracking student attendance using **QR codes** and **facial recognition**, built with Python + Tkinter and backed by MySQL.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

AMS is a mini-project for CSE departments that lets teachers manage class attendance without manual roll calls. Students register once, receive a unique QR code, and can optionally enrol their face. Teachers start a class session, then scan students via webcam — either by reading their QR code or by recognising their face with an LBPH model.

---

## Features

| Feature | Detail |
|---|---|
| Student & Teacher registration | Name, roll number, email, DOB, blood group, subject |
| QR-code attendance | Teacher's webcam scans student-held QR codes |
| Face-recognition attendance | LBPH model trained on per-student datasets |
| Dark / Light theme | Toggleable across all windows |
| Attendance report | Filterable by date and subject; exportable to CSV |
| Active class broadcast | Students see which classes are live in their dashboard |
| Password visibility toggle | Eye-icon on every password field across the app |

---

## Project Structure

```
AMS/                              ← project root (run everything from here)
├── main.py                       ← entry point
├── login_window.py               ← student & teacher login (eye-toggle added)
├── registration_window.py        ← student & teacher registration
├── student_dashboard.py          ← student view (QR display, attendance history)
├── teacher_dashboard.py          ← teacher view (class control, reports, CSV export)
├── theme.py                      ← dark / light palette (DARK / LIGHT dicts)
├── connection.py                 ← MySQL connection factory  ← edit password here
├── qr-attendence.py              ← standalone QR CLI tool (optional)
├── collect_faces.py              ← webcam face-capture script
├── face_recognition_module.py    ← LBPH inference session
├── train_model.py                ← trains the LBPH model on dataset/
├── __init__.py                   ← marks root as a Python package
│
├── face_module/                  ← face pipeline assets
│   ├── __init__.py
│   ├── dataset/                  ← per-student image folders  (auto-created)
│   │   └── <roll_no>/
│   │       ├── 1.jpg
│   │       └── ...
│   ├── trainer/                  ← saved LBPH model          (auto-created)
│   │   ├── face_model.yml
│   │   └── label_map.pkl
│   └── haarcascade_frontalface_default.xml
│
└── assets/
    └── qrcodes/                  ← student QR images         (auto-created)
        └── <roll_no>.png
```

> **Important:** Always launch the app from the project root so all relative paths resolve correctly.

---

## Prerequisites

| Requirement | Version | Download |
|---|---|---|
| Python | 3.9 or later | https://www.python.org/downloads/ |
| MySQL Server (Community) | 8.0+ | https://dev.mysql.com/downloads/mysql/ |
| MySQL Workbench (optional GUI) | any | https://dev.mysql.com/downloads/workbench/ |
| Webcam | — | Required for QR scanning and face capture |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AMS.git
cd AMS
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

A minimal `requirements.txt`:

```
mysql-connector-python
opencv-contrib-python      # contrib build required for cv2.face.LBPHFaceRecognizer
Pillow
qrcode[pil]
pyzbar
numpy
```

> **Windows note:** `pyzbar` requires the ZBar DLL. Download it from https://sourceforge.net/projects/zbar/ and place the DLLs in your system PATH, or use `pip install pyzbar --find-links https://github.com/NaturalHistoryMuseum/pyzbar`.

> **Critical:** Use `opencv-contrib-python`, **not** `opencv-python`. The base package does not ship the `cv2.face` module needed for LBPH face recognition.

### 3. Download the Haar cascade

Download `haarcascade_frontalface_default.xml` from the [OpenCV GitHub repository](https://github.com/opencv/opencv/tree/master/data/haarcascades) and place it inside `face_module/`.

---

## Database Setup

### Option A — MySQL Workbench

1. Open MySQL Workbench and connect with your root user.
2. Open `db/migration.sql` (File → Open SQL Script).
3. Click the lightning-bolt **Execute** button.

### Option B — Command line

```bash
mysql -u root -p < db/migration.sql
```

The script creates the `ams_db` database and all required tables (`students`, `teachers`, `attendance`, `active_classes`).

---

## Configuration

### Database password

Open `connection.py` and replace the placeholder with your MySQL password:

```python
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_MYSQL_PASSWORD_HERE",   # ← change this
    database="ams_db"
)
```

> **Security:** Never commit a real password to version control. Add `connection.py` to `.gitignore` or use environment variables (see [Security Notes](#security-notes)).

---

## Running the Application

```bash
# Always run from the project root
cd AMS
python main.py
```

The main menu opens with four options: Student Registration, Teacher Registration, Student Login, Teacher Login.

---

## How It Works

### Attendance flow

```
Teacher logs in
    → Selects subject → clicks "Start Class"
    → Active class appears on Student Dashboard

Student logs in
    → Sees active class card → clicks "Show My QR"
    → Holds QR code toward teacher's webcam

Teacher clicks "📷 QR Attendance"
    → Webcam opens → scans QR → marks student Present
    → Dashboard auto-refreshes after session
```

### Face recognition flow

```
Student registration
    → Clicks "Capture Face Data (Webcam)"
    → ~120 grayscale crops saved to face_module/dataset/<roll_no>/

After registration (or manually):
    → Run train_model.py  (or trigger via registration dialog)
    → face_module/trainer/face_model.yml + label_map.pkl created

Teacher session
    → Clicks "🤖 Face Attendance (AI)"
    → Webcam opens; LBPH model predicts identity
    → 5 consecutive confident frames required before marking Present
```

### Security architecture

Attendance writes happen exclusively in the teacher's authenticated session. Students only display their QR code — they have no write access to the attendance table.

---

## Security Notes

| Issue | Current State | Recommended Improvement |
|---|---|---|
| Hardcoded DB password | In `connection.py` | Use env var: `os.environ.get("AMS_DB_PASSWORD")` |
| Plain-text passwords | Stored as-is in `students`/`teachers` | Hash with `bcrypt` before storing |
| No input sanitisation | Parameterised queries used (safe from SQL injection) | Keep as-is |
| QR data not signed | Any QR with `STUDENT:<roll>` format is accepted | Add HMAC signature to QR payload |

---

## Troubleshooting

| Error | Likely Cause | Fix |
|---|---|---|
| `DB Connection Error` | MySQL not running or wrong password | Start MySQL service; check `connection.py` |
| `No module named 'cv2'` | Wrong OpenCV package installed | `pip install opencv-contrib-python` (not `opencv-python`) |
| `No module named 'cv2.face'` | Base OpenCV installed instead of contrib | `pip uninstall opencv-python && pip install opencv-contrib-python` |
| `No module named 'pyzbar'` | Library not installed | `pip install pyzbar` + install ZBar DLL on Windows |
| `No module named 'PIL'` | Pillow missing | `pip install Pillow` |
| Webcam not opening | Wrong camera index | Try `cv2.VideoCapture(1)` instead of `0` |
| `Model file not found` | Face model not trained | Run `python train_model.py` from project root |
| Haar cascade missing | XML not placed in `face_module/` | Download from OpenCV repo (see Installation step 3) |
| Scroll wheel fires in wrong window | Old `bind_all` bug | Update to fixed `registration_window.py` from this release |

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Commit your changes with a descriptive message.
4. Push and open a Pull Request against `main`.

Please do not commit `connection.py` with a real password. Add it to `.gitignore`:

```
# .gitignore
connection.py
face_module/dataset/
face_module/trainer/
assets/qrcodes/
attendance_exports/
__pycache__/
*.pyc
```

---

## Subjects Available

```
Operating System              CSE-401
Design and Analysis of Algorithm CSE-403
Modelling and Optimization Techniques CSE-402
Advanced Programming Practice CSE-405
Computer Networks             CSE-404
Audit Course                  AUC-401
```

---

## License

This project was created as a CSE mini-project. See `LICENSE` for details.

---

*CSE Department · AMS Mini Project · Built with Python, Tkinter, MySQL, OpenCV*