"""
collect_faces.py  —  AMS face_module/
Captures face images for a student and saves them into:
    face_module/dataset/<roll_no>/  (numbered .jpg files)

Each student gets their own sub-folder named by roll_no.
This guarantees that adding a new student never touches
the images of any previously registered student.
"""

import cv2
import os

# Path to the cascade XML — sits next to this file
_CASCADE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "haarcascade_frontalface_default.xml")
_DATASET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset")

TARGET_IMAGES = 120   # how many face samples to collect


def collect(roll_no: str, name: str, target: int = TARGET_IMAGES) -> int:
    """
    Open webcam, detect faces and save crops to dataset/<roll_no>/.
    Returns the number of images saved.
    Raises RuntimeError on webcam / cascade failure.
    """
    if not os.path.exists(_CASCADE):
        raise RuntimeError(
            f"Haar cascade file not found:\n{_CASCADE}\n\n"
            "Download from opencv/data/haarcascades on GitHub and place "
            "it in your face_module/ folder."
        )

    face_cascade = cv2.CascadeClassifier(_CASCADE)
    if face_cascade.empty():
        raise RuntimeError("Failed to load Haar cascade — file may be corrupt.")

    # ── Per-student folder ──────────────────────
    student_dir = os.path.join(_DATASET, roll_no)
    os.makedirs(student_dir, exist_ok=True)

    # Start numbering after existing images so we never overwrite
    existing = [f for f in os.listdir(student_dir) if f.endswith(".jpg")]
    start_idx = len(existing)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,  720)

    if not cap.isOpened():
        raise RuntimeError("Could not open webcam (index 0).")

    count = 0
    print(f"[collect_faces] Capturing {target} images for {name} ({roll_no})")
    print("[collect_faces] Look at the camera. Press Q to stop early.")

    while count < target:
        ret, frame = cap.read()
        if not ret:
            break

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

        for (x, y, w, h) in faces:
            count += 1
            crop_path = os.path.join(student_dir, f"{start_idx + count}.jpg")
            cv2.imwrite(crop_path, gray[y:y+h, x:x+w])
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 220, 100), 2)
            cv2.putText(frame, f"Captured {count}/{target}",
                        (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 220, 100), 2)

        # HUD
        cv2.rectangle(frame, (0, 0), (480, 46), (15, 23, 42), -1)
        cv2.putText(frame,
            f"Face Capture | {name} ({roll_no})  "
            f"  {count}/{target}  |  Q = stop",
            (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        cv2.imshow("Face Capture — Press Q to stop", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"[collect_faces] Done. Saved {count} images to {student_dir}")
    return count