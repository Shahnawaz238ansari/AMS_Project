"""
face_recognition_module.py  —  AMS face_module/
Real-time face recognition attendance using LBPH.

Uses:
    trainer/face_model.yml    — trained LBPH model
    trainer/label_map.pkl     — {int_label: roll_no} mapping

The DB look-up converts roll_no → student name & id so we can call
the teacher_dashboard's save_attendance callback.
"""

import cv2
import os
import pickle
import sys

_HERE        = os.path.dirname(os.path.abspath(__file__))
_TRAINER_DIR = os.path.join(_HERE, "trainer")
_MODEL_PATH  = os.path.join(_TRAINER_DIR, "face_model.yml")
_LABEL_MAP   = os.path.join(_TRAINER_DIR, "label_map.pkl")
_CASCADE     = os.path.join(_HERE, "haarcascade_frontalface_default.xml")

# Add project root to path so we can import db.connection
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

CONFIDENCE_THRESHOLD = 70   # lower = stricter. Tune between 60-80.
CONFIRM_FRAMES       = 5    # consecutive frames required before marking


class FaceAttendanceSession:
    """
    Runs a face-recognition attendance session in a blocking loop.
    Designed to be run in a background thread from teacher_dashboard.

    Parameters
    ----------
    subject      : str   — active subject name
    teacher_id   : int   — teacher's DB id
    dataset_dir  : str   — path to face_module/dataset/ (not used at runtime,
        kept for API compatibility)
    trainer_dir  : str   — path to face_module/trainer/
    on_mark_cb   : callable(roll_no, name) — called on main thread via after()
    on_done_cb   : callable(total_marked)  — called when session ends
    """

    def __init__(self, subject, teacher_id,
                dataset_dir=None, trainer_dir=None,
                on_mark_cb=None, on_done_cb=None):
        self.subject     = subject
        self.teacher_id  = teacher_id
        self.on_mark_cb  = on_mark_cb  or (lambda r, n: None)
        self.on_done_cb  = on_done_cb  or (lambda t: None)

        t_dir = trainer_dir or _TRAINER_DIR
        model = os.path.join(t_dir, "face_model.yml")
        lmap  = os.path.join(t_dir, "label_map.pkl")

        if not os.path.exists(model):
            raise FileNotFoundError(
                f"Model file not found:\n{model}\n\n"
                "Run train_model.py first."
            )
        if not os.path.exists(lmap):
            raise FileNotFoundError(
                f"Label map not found:\n{lmap}\n\n"
                "Run train_model.py to regenerate it."
            )

        self._recognizer = cv2.face.LBPHFaceRecognizer_create()
        self._recognizer.read(model)

        with open(lmap, "rb") as f:
            self._label_map = pickle.load(f)   # {int → roll_no}

        if not os.path.exists(_CASCADE):
            raise FileNotFoundError(
                f"Haar cascade not found:\n{_CASCADE}"
            )
        self._cascade = cv2.CascadeClassifier(_CASCADE)
        if self._cascade.empty():
            raise RuntimeError("Failed to load Haar cascade.")

        # Track marked students and consecutive-frame counters
        self._marked   = set()          # roll_nos already marked this session
        self._counters = {}             # roll_no → consecutive detection count

    # ─────────────────────────────────────────────────────────────────────
    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,  720)

        if not cap.isOpened():
            print("[face_recognition] ERROR: Cannot open webcam.")
            self.on_done_cb(0)
            return

        print(f"[face_recognition] Session started. Subject: {self.subject}")
        print("[face_recognition] Press Q to end session.")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self._cascade.detectMultiScale(
                    gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

                for (x, y, w, h) in faces:
                    face_crop = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
                    label, confidence = self._recognizer.predict(face_crop)

                    roll_no = self._label_map.get(label, None)
                    name    = self._get_name(roll_no) if roll_no else "Unknown"

                    if roll_no and confidence < CONFIDENCE_THRESHOLD:
                        if roll_no in self._marked:
                            # Already marked — show green "done" box
                            clr   = (0, 200, 80)
                            disp  = f"{name} ✓ (marked)"
                        else:
                            # Require CONFIRM_FRAMES consecutive good detections
                            self._counters[roll_no] = \
                                self._counters.get(roll_no, 0) + 1
                            remaining = CONFIRM_FRAMES - self._counters[roll_no]

                            if self._counters[roll_no] >= CONFIRM_FRAMES:
                                # Mark attendance
                                self._marked.add(roll_no)
                                self._counters[roll_no] = 0
                                self.on_mark_cb(roll_no, name)
                                clr  = (0, 255, 150)
                                disp = f"{name} — MARKED!"
                            else:
                                clr  = (0, 165, 255)
                                disp = f"{name} ({remaining} more frames)"
                    else:
                        # Unknown / low confidence
                        clr  = (0, 60, 220)
                        disp = f"Unknown  (conf={confidence:.0f})"
                        # Reset counter for this face position
                        if roll_no:
                            self._counters[roll_no] = 0

                    cv2.rectangle(frame, (x, y), (x+w, y+h), clr, 2)
                    cv2.putText(frame, disp, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, clr, 2)

                # HUD overlay
                cv2.rectangle(frame, (0, 0), (680, 46), (15, 23, 42), -1)
                cv2.putText(frame,
                    f"Face Attendance | {self.subject[:35]}  "
                    f"Marked: {len(self._marked)}  |  Q = End",
                    (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (255, 255, 255), 2)

                cv2.imshow("Face Attendance — Press Q to end", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

        total = len(self._marked)
        print(f"[face_recognition] Session ended. Total marked: {total}")
        self.on_done_cb(total)

    #────────────────────────────────────────────────────────────
    def _get_name(self, roll_no: str) -> str:
        """Fetch student name from DB by roll_no. Returns roll_no on failure."""
        try:
            from db.connection import get_connection
            conn = get_connection()
            if not conn:
                return roll_no
            cur = conn.cursor()
            cur.execute("SELECT name FROM students WHERE roll_no=%s", (roll_no,))
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row[0] if row else roll_no
        except Exception as ex:
            print(f"[face_recognition] DB lookup error: {ex}")
            return roll_no