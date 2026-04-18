import qrcode
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
import mysql.connector
from datetime import date
import os

# ─── Database Connection ───────────────────────
def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="MD@785892",
        database="ams_db"
    )
    return conn

# ─── 1. Generating the QR Code ─────────────────
def generate_qr(student_roll_no, student_name):
    qr_data = f"STUDENT:{student_roll_no}:{student_name}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    os.makedirs("assets/qrcodes", exist_ok=True)
    file_path = f"assets/qrcodes/{student_roll_no}.png"
    img.save(file_path)
    print(f"QR Code saved: {file_path}")
    return file_path

# ─── 2. Attendance by scanning QR ───────────────
def scan_and_mark_attendance(teacher_id):
    print("Webcam tuning on... ready with Your QR code!")
    print("'q' for quit this webcam!")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Webcam not found!")
        return

    # Improve camera quality
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    marked_students = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        qr_codes = decode(frame, symbols=[ZBarSymbol.QRCODE])

        for qr in qr_codes:
            qr_data = qr.data.decode("utf-8")
            roll_no = None

            if qr_data.startswith("STUDENT:"):
                parts = qr_data.split(":")
                if len(parts) >= 2:
                    roll_no = parts[1].strip()

            elif qr_data.startswith("ROLL:"):
                roll_no = qr_data.replace("ROLL:", "").strip()

            if not roll_no:
                continue

            if roll_no in marked_students:
                label = f"{roll_no} - Already Marked"
                color = (0, 165, 255)
            else:
                success, student_name = save_attendance(roll_no, teacher_id)
                if success:
                    marked_students.append(roll_no)
                    label = f"{student_name} - Present!"
                    color = (0, 255, 0)
                else:
                    label = f"{roll_no} - Not Found"
                    color = (0, 0, 255)

            # Show box around QR code
            points = qr.polygon
            if points:
                pts = [(p.x, p.y) for p in points]
                for j in range(len(pts)):
                    cv2.line(frame, pts[j], pts[(j+1) % len(pts)], color, 3)

            cv2.putText(frame, label,
                (qr.rect.left, qr.rect.top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.putText(frame,
            f"Marked: {len(marked_students)} | Press Q to quit",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
            0.8, (255, 255, 255), 2)

        cv2.imshow("QR Attendance Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nAttendance complete! Total marked: {len(marked_students)}")
    return marked_students

# ─── 3. Save to the database ───────────────
def save_attendance(roll_no, teacher_id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name FROM students WHERE roll_no = %s",
            (roll_no,)
        )
        student = cursor.fetchone()

        if not student:
            print(f"Student not found: {roll_no}")
            return False, None

        student_id   = student[0]
        student_name = student[1]
        today        = date.today()

        # is today already marked?
        cursor.execute("""
            SELECT id FROM attendance
            WHERE student_id = %s AND date = %s
        """, (student_id, today))

        if cursor.fetchone():
            print(f"{student_name} already marked today")
            return False, student_name

        cursor.execute("""
            INSERT INTO attendance
            (student_id, teacher_id, date, status, method)
            VALUES (%s, %s, %s, 'Present', 'QR')
        """, (student_id, teacher_id, today))

        conn.commit()
        print(f" Marked: {student_name} — {today}")
        return True, student_name

    except Exception as e:
        print(f"Database error: {e}")
        return False, None
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

# ─── 4. View Report ──────────────────────────
def view_attendance_report(date_filter=None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if date_filter is None:
            date_filter = date.today()

        cursor.execute("""
            SELECT s.name, s.roll_no, a.status, a.method, a.date
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = %s
            ORDER BY s.roll_no
        """, (date_filter,))

        records = cursor.fetchall()

        print(f"\n{'='*55}")
        print(f"  Attendance Report — {date_filter}")
        print(f"{'='*55}")
        print(f"{'Name':<22} {'Roll No':<14} {'Status':<10} {'Method'}")
        print(f"{'-'*55}")

        if not records:
            print("  Aaj koi attendance nahi mili.")
        for row in records:
            print(f"{row[0]:<22} {row[1]:<14} {row[2]:<10} {row[3]}")

        print(f"{'='*55}")
        print(f"  Total Present: {len(records)}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

# ─── Main Menu ─────────────────────────────────
if __name__ == "__main__":
    print("\n===== QR ATTENDANCE MODULE =====")
    print("1. Generate QR Code")
    print("2. Attendance Scan (Webcam)")
    print("3. View Report")
    choice = input("Choose (1/2/3): ").strip()

    if choice == "1":
        roll = input("Roll No: ").strip()
        name = input("Student Name: ").strip()
        generate_qr(roll, name)

    elif choice == "2":
        teacher_id = int(input("Teacher ID: ").strip())
        scan_and_mark_attendance(teacher_id)

    elif choice == "3":
        view_attendance_report()