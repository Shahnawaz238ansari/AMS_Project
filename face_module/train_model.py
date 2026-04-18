"""
train_model.py  —  AMS face_module/
Trains an LBPH face recognizer using ALL student folders under dataset/.

Folder structure expected:
    face_module/
        dataset/
            <roll_no_1>/    ← images for student 1
                1.jpg
                2.jpg ...
            <roll_no_2>/    ← images for student 2
                1.jpg ...
        trainer/
            face_model.yml      ← saved LBPH model
            label_map.pkl       ← {int_label: roll_no} mapping

WHY label_map.pkl?
    LBPH works with integer labels. We assign each student folder a
    unique integer and store the mapping so face_recognition_module.py
    can convert predicted int → roll_no → student name from the DB.

IMPORTANT — this file must be re-run every time a new student's face
data is collected so the new student is included in the model.
"""

import cv2
import os
import pickle
import numpy as np

_HERE        = os.path.dirname(os.path.abspath(__file__))
_DATASET_DIR = os.path.join(_HERE, "dataset")
_TRAINER_DIR = os.path.join(_HERE, "trainer")
_MODEL_PATH  = os.path.join(_TRAINER_DIR, "face_model.yml")
_LABEL_MAP   = os.path.join(_TRAINER_DIR, "label_map.pkl")


def train() -> dict:
    """
    Train the LBPH model on every student sub-folder in dataset/.
    Returns the label_map {int → roll_no}.
    Raises RuntimeError if no images are found.
    """
    os.makedirs(_TRAINER_DIR, exist_ok=True)

    if not os.path.isdir(_DATASET_DIR):
        raise RuntimeError(f"Dataset directory not found:\n{_DATASET_DIR}")

    # ── Build label map from sub-folder names ──
    student_folders = sorted([
        d for d in os.listdir(_DATASET_DIR)
        if os.path.isdir(os.path.join(_DATASET_DIR, d))
    ])

    if not student_folders:
        raise RuntimeError(
            "No student folders found in dataset/.\n"
            "Register at least one student with face capture first."
        )

    # int label  →  roll_no string
    label_map = {idx: roll_no for idx, roll_no in enumerate(student_folders)}
    # roll_no string  →  int label  (for fast lookup while building arrays)
    roll_to_label = {v: k for k, v in label_map.items()}

    print(f"[train_model] Found {len(student_folders)} student(s):")
    for lbl, roll in label_map.items():
        print(f"  Label {lbl:3d} → {roll}")

    faces_list  = []
    labels_list = []
    skipped     = 0

    for roll_no in student_folders:
        label       = roll_to_label[roll_no]
        student_dir = os.path.join(_DATASET_DIR, roll_no)
        img_files   = [f for f in os.listdir(student_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))]

        if not img_files:
            print(f"  [WARN] {roll_no}: no images — skipping")
            continue

        for fname in img_files:
            img_path = os.path.join(student_dir, fname)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                skipped += 1
                continue
            # Resize to a fixed size for consistency
            img = cv2.resize(img, (200, 200))
            faces_list.append(img)
            labels_list.append(label)

        print(f"  {roll_no}: loaded {len(img_files)} image(s)")

    if not faces_list:
        raise RuntimeError(
            "No valid face images could be loaded from dataset/.\n"
            "Make sure images are valid .jpg/.jpeg/.png files."
        )

    print(f"[train_model] Total samples: {len(faces_list)}  "
        f"(skipped {skipped} unreadable files)")

    # ── Train LBPH model ───────────────────────
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces_list, np.array(labels_list, dtype=np.int32))
    recognizer.save(_MODEL_PATH)
    print(f"[train_model] Model saved → {_MODEL_PATH}")

    # ── Save label map ─────────────────────────
    with open(_LABEL_MAP, "wb") as f:
        pickle.dump(label_map, f)
    print(f"[train_model] Label map saved → {_LABEL_MAP}")
    print(f"[train_model] Training complete. {len(label_map)} student(s) in model.")

    return label_map


if __name__ == "__main__":
    result = train()
    print("\nLabel map:")
    for lbl, roll in result.items():
        print(f"  {lbl} → {roll}")