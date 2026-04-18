"""
registration_window.py  —  AMS Project
Fixes applied vs original:
1. CalendarPicker: is_sel comparison used self._month == self._month (always True)
→ fixed to compare current loop month/year against navigation state.
2. ScrollableFrame.bind_all("<MouseWheel>") fires across ALL windows.
    → replaced with per-canvas bind to avoid polluting other Toplevels.
3. registration_window face_dir computed root_dir = dirname(dirname(__file__))
    which in a flat layout points to /mnt (not /mnt/project).
    → Unified: face_module is always a sibling of __file__ in flat layout, or sibling of ROOT in nested layout. Both cases handled.
4. sys.path fix: consistent with login_window — insert both THIS_DIR and
PARENT_DIR so db/ and modules/ resolve in either layout.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import threading

# ── Path fix ──────────────────────────────────────────────────────────────────
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
for _p in (_THIS_DIR, _PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db.connection import get_connection
from modules.theme import get_theme, toggle_theme
import qrcode
from PIL import Image, ImageTk
import calendar
from datetime import date as _date

SUBJECTS = [
    "Operating System CSE-401",
    "Modelling and Optimization Techniques CSE-402",
    "Computer Networks CSE-404",
    "Design and Analysis of Algorithm CSE-403",
    "Advanced Programming Practice CSE-405",
    "Audit Course AUC-401",
]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def _resolve_face_module_dir() -> str:
    """
    Return the face_module/ path that works in both flat and nested layouts.
    Flat:   /project/face_recognition_module.py → /project/face_module/
    Nested: /project/modules/registration_window.py → /project/face_module/
    """
    candidates = [
        os.path.join(_THIS_DIR,   "face_module"),  # flat layout
        os.path.join(_PARENT_DIR, "face_module"),  # nested layout
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    return candidates[0]   # fallback — will raise a clear error at runtime


def _generate_qr(roll_no, name):
    os.makedirs("assets/qrcodes", exist_ok=True)
    path = f"assets/qrcodes/{roll_no}.png"
    if os.path.exists(path):
        return path
    qr = qrcode.QRCode(version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10, border=4)
    qr.add_data(f"STUDENT:{roll_no}:{name}")
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(path)
    return path


def _toggle_btn(win, cb, t=None):
    if t is None:
        t = get_theme()
    b = tk.Button(win, text=t["toggle_text"],
            font=("Segoe UI", 9, "bold"),
            bg=t["toggle_bg"], fg=t["toggle_fg"],
            relief="flat", cursor="hand2", bd=0,
            command=cb)
    b.pack(anchor="ne", padx=12, pady=6, ipadx=10, ipady=4)
    return b


def _lbl(parent, text, t):
    return tk.Label(parent, text=text, font=("Segoe UI", 10),
                    bg=t["bg"], fg=t["sub_fg"], anchor="w")


def _entry(parent, var, t, hide=False):
    e = tk.Entry(parent, textvariable=var,
            font=("Segoe UI", 11),
            bg=t["entry_bg"], fg=t["fg"],
            insertbackground=t["fg"],
            relief="flat", bd=8)
    if hide:
        e.config(show="●")
    return e

# ─── Calendar Popup ───────────────────────────────────────────────────────────
class CalendarPicker(tk.Toplevel):
    """A simple calendar popup that lets the user pick a date."""

    def __init__(self, parent, var: tk.StringVar, t: dict):
        super().__init__(parent)
        self.var = var
        self.t   = t
        self.title("Pick Date of Birth")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=t["bg"])

        try:
            parts = var.get().strip().split("-")
            if len(parts) == 3 and len(parts[0]) == 4:
                self._year  = int(parts[0])
                self._month = int(parts[1])
                self._day   = int(parts[2])
            else:
                raise ValueError
        except Exception:
            today = _date.today()
            self._year  = today.year - 20
            self._month = today.month
            self._day   = today.day

        # Track the currently navigated month/year separately from
        # _month/_year so the highlight works correctly
        self._nav_year  = self._year
        self._nav_month = self._month

        self._build()

    def _build(self):
        t = self.t

        nav = tk.Frame(self, bg=t["header_bg"], pady=6)
        nav.pack(fill="x")

        tk.Button(nav, text="◀", font=("Segoe UI", 11, "bold"),
            bg=t["header_bg"], fg=t["fg"], relief="flat", cursor="hand2",
            command=self._prev_month).pack(side="left", padx=8)

        self._nav_lbl = tk.Label(nav, text="",
                font=("Segoe UI", 11, "bold"),
                bg=t["header_bg"], fg=t["accent"])
        self._nav_lbl.pack(side="left", expand=True)

        tk.Button(nav, text="▶", font=("Segoe UI", 11, "bold"),
            bg=t["header_bg"], fg=t["fg"], relief="flat", cursor="hand2",
            command=self._next_month).pack(side="right", padx=8)

        yr_frame = tk.Frame(self, bg=t["bg"], pady=4)
        yr_frame.pack(fill="x")
        tk.Label(yr_frame, text="Year:", font=("Segoe UI", 9),
            bg=t["bg"], fg=t["sub_fg"]).pack(side="left", padx=10)
        self._yr_var = tk.StringVar(value=str(self._nav_year))
        yr_spin = tk.Spinbox(yr_frame, from_=1950, to=_date.today().year,
                textvariable=self._yr_var,
                font=("Segoe UI", 10), width=6,
                bg=t["entry_bg"], fg=t["fg"],
                buttonbackground=t["header_bg"],
                relief="flat",
                command=self._year_changed)
        yr_spin.pack(side="left")
        yr_spin.bind("<Return>", lambda e: self._year_changed())

        days_hdr = tk.Frame(self, bg=t["bg"])
        days_hdr.pack(fill="x", padx=8, pady=(4, 0))
        for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            tk.Label(days_hdr, text=d, width=4,
            font=("Segoe UI", 8, "bold"),
            bg=t["bg"], fg=t["sub_fg"]).pack(side="left")

        self._grid_frame = tk.Frame(self, bg=t["bg"])
        self._grid_frame.pack(padx=8, pady=4)

        btn_row = tk.Frame(self, bg=t["bg"], pady=6)
        btn_row.pack()
        tk.Button(btn_row, text=" Select ",
            font=("Segoe UI", 10, "bold"),
            bg=t["success"], fg="white", relief="flat", cursor="hand2",
            command=self._confirm).pack(side="left", ipadx=14, ipady=5, padx=6)
        tk.Button(btn_row, text="Cancel",
            font=("Segoe UI", 9),
            bg=t["divider"], fg=t["fg"], relief="flat", cursor="hand2",
            command=self.destroy).pack(side="left", ipadx=10, ipady=5)

        self._render_grid()

    def _render_grid(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()

        t   = self.t
        cal = calendar.monthcalendar(self._nav_year, self._nav_month)
        self._nav_lbl.config(
            text=f"{calendar.month_name[self._nav_month]}  {self._nav_year}")
        self._yr_var.set(str(self._nav_year))

        for week in cal:
            row = tk.Frame(self._grid_frame, bg=t["bg"])
            row.pack()
            for day in week:
                if day == 0:
                    tk.Label(row, text="", width=4, bg=t["bg"]).pack(side="left")
                else:
                    # FIX: was comparing self._month == self._month (always True)
                    is_sel = (day == self._day and
                    self._nav_month == self._month and
                        self._nav_year  == self._year)
                    bg = t["accent"] if is_sel else t["header_bg"]
                    fg = t["bg"]     if is_sel else t["fg"]
                    b = tk.Button(row, text=str(day), width=3,
                        font=("Segoe UI", 9),
                        bg=bg, fg=fg, relief="flat", cursor="hand2",
                        command=lambda d=day: self._select_day(d))
                    b.pack(side="left", padx=1, pady=1)

    def _select_day(self, day):
        self._day   = day
        self._month = self._nav_month
        self._year  = self._nav_year
        self._render_grid()

    def _prev_month(self):
        self._nav_month -= 1
        if self._nav_month < 1:
            self._nav_month = 12
            self._nav_year -= 1
        self._day = min(
            self._day,
            calendar.monthrange(self._nav_year, self._nav_month)[1])
        self._render_grid()

    def _next_month(self):
        self._nav_month += 1
        if self._nav_month > 12:
            self._nav_month = 1
            self._nav_year += 1
        self._day = min(
            self._day,
            calendar.monthrange(self._nav_year, self._nav_month)[1])
        self._render_grid()

    def _year_changed(self):
        try:
            self._nav_year = int(self._yr_var.get())
            self._day = min(
                self._day,
                calendar.monthrange(self._nav_year, self._nav_month)[1])
            self._render_grid()
        except ValueError:
            pass

    def _confirm(self):
        self.var.set(f"{self._year:04d}-{self._nav_month:02d}-{self._day:02d}")
        self.destroy()


# ─── Password Entry with Eye Toggle ──────────────────────────────────────────
class PasswordEntry(tk.Frame):
    """An Entry widget with an eye-toggle button to show/hide password."""

    def __init__(self, parent, var: tk.StringVar, t: dict, **kwargs):
        super().__init__(parent, bg=t["bg"])
        self._t       = t
        self._visible = False

        self._entry = tk.Entry(self, textvariable=var,
            font=("Segoe UI", 11),
            bg=t["entry_bg"], fg=t["fg"],
            insertbackground=t["fg"],
            relief="flat", bd=8, show="●")
        self._entry.pack(side="left", fill="x", expand=True, ipady=6)

        self._eye_btn = tk.Button(self, text="👁",
            font=("Segoe UI", 10),
            bg=t["entry_bg"], fg=t["sub_fg"],
            relief="flat", cursor="hand2", bd=0,
            activebackground=t["entry_bg"],
            command=self._toggle)
        self._eye_btn.pack(side="right", padx=(0, 4))

    def _toggle(self):
        self._visible = not self._visible
        self._entry.config(show="" if self._visible else "●")
        self._eye_btn.config(
            text="🙈" if self._visible else "👁",
            fg=self._t["accent"] if self._visible else self._t["sub_fg"]
        )

    def reconfigure(self, t: dict):
        self._t = t
        self.configure(bg=t["bg"])
        self._entry.configure(bg=t["entry_bg"], fg=t["fg"],
            insertbackground=t["fg"])
        self._eye_btn.configure(bg=t["entry_bg"],
                                activebackground=t["entry_bg"],
                                fg=t["accent"] if self._visible else t["sub_fg"])

    def pack(self, **kwargs):
        super().pack(**kwargs)


# ─── Reusable Scrollable Frame ────────────────────────────────────────────────
class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._sb = ttk.Scrollbar(self, orient="vertical",
                command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._sb.set)

        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self._canvas, bg=bg)
        self._win_id = self._canvas.create_window(
            (0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # FIX: bind per canvas, not bind_all, to avoid cross-window scroll leaks
        self._canvas.bind("<Enter>",  self._attach_scroll)
        self._canvas.bind("<Leave>",  self._detach_scroll)

    def _attach_scroll(self, _e):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _detach_scroll(self, _e):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_inner_configure(self, _event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        content_h = self.inner.winfo_reqheight()
        canvas_h  = self._canvas.winfo_height()
        if content_h > canvas_h:
            self._sb.pack(side="right", fill="y")
        else:
            self._sb.pack_forget()

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._win_id, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def reconfigure_bg(self, bg):
        self._canvas.configure(bg=bg)
        self.inner.configure(bg=bg)
        self.configure(bg=bg)


# ════════════════════════════════════════════════
#  STUDENT REGISTRATION
# ════════════════════════════════════════════════
class StudentRegistrationWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Student Registration")
        self.win.geometry("660x900")
        self.win.minsize(600, 680)
        self.win.resizable(True, True)
        self.win.grab_set()
        self._lbls          = []
        self._entries       = []
        self._pwd_entry     = None
        self._face_captured = False
        self._build()

    def _build(self):
        t = get_theme()
        self.win.configure(bg=t["bg"])

        topbar = tk.Frame(self.win, bg=t["bg"])
        topbar.pack(fill="x")
        self._tog = _toggle_btn(topbar, self._theme, t)

        self._head_lbl = tk.Label(self.win, text=" Student Registration  ",
                font=("Segoe UI", 16, "bold"),
                bg=t["bg"], fg=t["accent"])
        self._head_lbl.pack(pady=(0, 6))

        self._scroll = ScrollableFrame(self.win, bg=t["bg"])
        self._scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self.form = self._scroll.inner

        self.v_name  = tk.StringVar()
        self.v_roll  = tk.StringVar()
        self.v_email = tk.StringVar()
        self.v_pwd   = tk.StringVar()
        self.v_cls   = tk.StringVar()
        self.v_dob   = tk.StringVar()
        self.v_phone = tk.StringVar()
        self.v_blood = tk.StringVar(value="A+")

        self._inner_form = tk.Frame(self.form, bg=t["bg"])
        self._inner_form.pack(fill="x", padx=36)
        inner_form = self._inner_form

        plain_fields = [
            ("Full Name",                  self.v_name,  False),
            ("Roll Number",                self.v_roll,  False),
            ("Email ID",                   self.v_email, False),
            ("Class  (e.g. CSE 2nd Year)", self.v_cls,   False),
            ("Phone Number",               self.v_phone, False),
        ]
        for lbl_text, var, hide in plain_fields:
            l = _lbl(inner_form, lbl_text, t)
            l.pack(fill="x", pady=(8, 1))
            self._lbls.append(l)
            e = _entry(inner_form, var, t, hide)
            e.pack(fill="x", ipady=6)
            self._entries.append(e)

        pwd_lbl = _lbl(inner_form, "Password", t)
        pwd_lbl.pack(fill="x", pady=(8, 1))
        self._lbls.append(pwd_lbl)
        self._pwd_widget = PasswordEntry(inner_form, self.v_pwd, t)
        self._pwd_widget.pack(fill="x")

        dob_lbl = _lbl(inner_form, "Date of Birth", t)
        dob_lbl.pack(fill="x", pady=(8, 1))
        self._lbls.append(dob_lbl)

        dob_row = tk.Frame(inner_form, bg=t["bg"])
        dob_row.pack(fill="x")
        self._dob_entry = tk.Entry(dob_row, textvariable=self.v_dob,
                font=("Segoe UI", 11),
                bg=t["entry_bg"], fg=t["fg"],
                insertbackground=t["fg"],
                relief="flat", bd=8)
        self._dob_entry.pack(side="left", fill="x", expand=True, ipady=6)
        self._dob_hint = tk.Label(dob_row, text="YYYY-MM-DD",
                font=("Segoe UI", 8, "italic"),
                bg=t["bg"], fg=t["sub_fg"])
        self._dob_hint.pack(side="left", padx=(4, 2))
        self._cal_btn = tk.Button(dob_row, text="📅",
                font=("Segoe UI", 12),
                bg=t["btn_attend"], fg="white",
                relief="flat", cursor="hand2", bd=0,
                command=self._open_calendar)
        self._cal_btn.pack(side="right", ipadx=6, ipady=4)

        bl = _lbl(inner_form, "Blood Group", t)
        bl.pack(fill="x", pady=(8, 1))
        self._lbls.append(bl)

        self._blood_cb = ttk.Combobox(inner_form, textvariable=self.v_blood,
                values=BLOOD_GROUPS, state="readonly",
                font=("Segoe UI", 11))
        self._blood_cb.pack(fill="x", ipady=5)

        tk.Frame(inner_form, bg=t["divider"], height=1).pack(fill="x", pady=(18, 8))

        self._face_header = tk.Label(inner_form,
            text="  Face Recognition Data  (Optional but Recommended)  ",
            font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["accent"], anchor="w")
        self._face_header.pack(fill="x")
        self._lbls.append(self._face_header)

        self._face_hint_lbl = tk.Label(inner_form,
            text="Capture your face now so teachers can use AI attendance.\n"
            "Full Name & Roll Number must be filled before capturing.",
            font=("Segoe UI", 8, "italic"),
            bg=t["bg"], fg=t["sub_fg"], anchor="w", justify="left")
        self._face_hint_lbl.pack(fill="x", pady=(2, 6))
        self._lbls.append(self._face_hint_lbl)

        self._face_status_var = tk.StringVar(value="  Face data not captured yet  ")
        self._face_status_lbl = tk.Label(inner_form,
            textvariable=self._face_status_var,
            font=("Segoe UI", 9, "bold"),
            bg=t["bg"], fg=t["sub_fg"], anchor="w")
        self._face_status_lbl.pack(fill="x", pady=(0, 6))

        self._face_btn = tk.Button(
            inner_form, text="  Capture Face Data  (Webcam)",
            font=("Segoe UI", 11, "bold"),
            bg=t["btn_attend"], fg="white",
            activebackground=t["btn_attend_h"],
            relief="flat", cursor="hand2", bd=0,
            command=self._capture_face
        )
        self._face_btn.pack(fill="x", ipady=10, pady=(0, 3))

        self._retake_btn = tk.Button(
            inner_form, text=" Retake Face Data ",
            font=("Segoe UI", 9),
            bg=t["divider"], fg=t["fg"],
            activebackground=t["header_bg"],
            relief="flat", cursor="hand2", bd=0,
            command=self._retake_face
        )

        tk.Frame(inner_form, bg=t["divider"], height=1).pack(fill="x", pady=(14, 8))

        self._reg_btn = tk.Button(
            inner_form, text=" Register  &  Generate QR Code ",
            font=("Segoe UI", 12, "bold"),
            bg=t["success"], fg="white",
            activebackground=t["btn_login_sh"],
            relief="flat", cursor="hand2", bd=0,
            command=self._register
        )
        self._reg_btn.pack(pady=(0, 22), ipadx=14, ipady=12, fill="x")

    def _open_calendar(self):
        CalendarPicker(self.win, self.v_dob, get_theme())

    def _capture_face(self):
        roll = self.v_roll.get().strip()
        name = self.v_name.get().strip()
        if not roll or not name:
            messagebox.showerror("Missing Info",
                    "Please fill in Full Name and Roll Number first!",
                    parent=self.win)
            return

        if not messagebox.askyesno("Open Webcam",
            f"Webcam will open to capture ~120 face images for:\n\n"
            f"  Name    : {name}\n"
            f"  Roll No : {roll}\n\n"
            "Look at the camera and move your head slightly.\n"
            "Press  Q  to stop early.\n\nContinue?",
            parent=self.win):
            return

        self._face_btn.config(state="disabled", text=" Capturing…  Please wait")
        self._face_status_var.set(" Opening webcam…")
        self.win.update_idletasks()

        def _run():
            try:
                face_dir = _resolve_face_module_dir()
                if face_dir not in sys.path:
                    sys.path.insert(0, face_dir)
                if "collect_faces" in sys.modules:
                    del sys.modules["collect_faces"]
                from collect_faces import collect
                collect(roll, name)
                captured = True
            except ImportError as e:
                captured = False
                self.win.after(0, lambda err=e: messagebox.showerror(
                    "Module Error",
                    f"collect_faces.py could not be imported:\n{err}\n\n"
                    "Ensure face_module/collect_faces.py exists.",
                    parent=self.win))
            except Exception as e:
                captured = False
                self.win.after(0, lambda err=e: messagebox.showerror(
                    "Capture Error", str(err), parent=self.win))
            self.win.after(0, lambda ok=captured: self._after_capture(ok, roll, name))

        threading.Thread(target=_run, daemon=True).start()

    def _after_capture(self, success, roll, name):
        t = get_theme()
        if success:
            self._face_captured = True
            self._face_status_var.set(f" Face data captured  ({name} / {roll})")
            self._face_status_lbl.configure(fg=t["success"])
            self._face_btn.config(
                text=" Face Captured  (click Retake to redo)",
                bg=t["success"], state="normal")
            self._retake_btn.pack(fill="x", ipady=5, pady=(0, 2))
        else:
            self._face_status_var.set(" Capture failed — try again")
            self._face_status_lbl.configure(fg=t["danger"])
            self._face_btn.config(
                text=" Capture Face Data  (Webcam)",
                bg=t["btn_attend"], state="normal")

    def _retake_face(self):
        t = get_theme()
        self._face_captured = False
        self._face_status_var.set(" Face data not captured yet")
        self._face_status_lbl.configure(fg=t["sub_fg"])
        self._face_btn.config(
            text=" Capture Face Data  (Webcam)",
            bg=t["btn_attend"], state="normal")
        self._retake_btn.pack_forget()

    def _theme(self):
        toggle_theme()
        t = get_theme()
        self.win.configure(bg=t["bg"])
        self._tog.configure(bg=t["toggle_bg"], fg=t["toggle_fg"],
                            text=t["toggle_text"])
        self._head_lbl.configure(bg=t["bg"], fg=t["accent"])
        self._scroll.reconfigure_bg(t["bg"])
        self._inner_form.configure(bg=t["bg"])
        for w in self._inner_form.winfo_children():
            if isinstance(w, tk.Frame):
                try:
                    h = w.cget("height")
                    w.configure(bg=t["divider"] if h and int(h) == 1 else t["bg"])
                except Exception:
                    w.configure(bg=t["bg"])
        for l in self._lbls:
            try:
                l.configure(bg=t["bg"], fg=t["sub_fg"])
            except Exception:
                pass
        self._face_header.configure(fg=t["accent"])
        self._face_status_lbl.configure(bg=t["bg"])
        for e in self._entries:
            e.configure(bg=t["entry_bg"], fg=t["fg"], insertbackground=t["fg"])
        self._pwd_widget.reconfigure(t)
        self._dob_entry.configure(bg=t["entry_bg"], fg=t["fg"],
                insertbackground=t["fg"])
        self._dob_hint.configure(bg=t["bg"], fg=t["sub_fg"])
        self._cal_btn.configure(bg=t["btn_attend"])
        self._reg_btn.configure(bg=t["success"], activebackground=t["btn_login_sh"])
        if self._face_captured:
            self._face_btn.configure(bg=t["success"],
                activebackground=t["btn_login_sh"])
            self._face_status_lbl.configure(fg=t["success"])
        else:
            self._face_btn.configure(bg=t["btn_attend"],
                activebackground=t["btn_attend_h"])
        self._retake_btn.configure(bg=t["divider"], fg=t["fg"])

    def _register(self):
        name  = self.v_name.get().strip()
        roll  = self.v_roll.get().strip()
        email = self.v_email.get().strip()
        pwd   = self.v_pwd.get().strip()
        cls   = self.v_cls.get().strip()
        dob   = self.v_dob.get().strip()
        phone = self.v_phone.get().strip()
        blood = self.v_blood.get().strip()

        if not all([name, roll, email, pwd, cls, dob, phone, blood]):
            messagebox.showerror("Incomplete", "Fill all the fields!", parent=self.win)
            return

        if self._face_captured:
            if messagebox.askyesno("Train Face Model",
                "Face data was captured.\n\n"
                "Train the face recognition model now?\n"
                "(Recommended — takes a few seconds)",
                parent=self.win):
                self._train_model_bg()

        qr_path = _generate_qr(roll, name)
        conn = cur = None
        try:
            conn = get_connection()
            if not conn:
                messagebox.showerror("DB Error", "Cannot connect to database.",
                parent=self.win)
                return
            cur = conn.cursor()
            cur.execute("""INSERT INTO students
                (name,roll_no,email,password,class,dob,phone,blood_group,qr_code_path)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (name, roll, email, pwd, cls, dob, phone, blood, qr_path))
            conn.commit()
            self._show_qr(qr_path, name, roll)
        except Exception as ex:
            if "Duplicate" in str(ex):
                messagebox.showerror("Already Exists",
                "Roll No or Email is already registered!",
                parent=self.win)
            else:
                messagebox.showerror("DB Error", str(ex), parent=self.win)
        finally:
            if cur:  cur.close()
            if conn: conn.close()

    def _train_model_bg(self):
        self._face_status_var.set(" Training face recognition model…")
        self.win.update_idletasks()

        def _run():
            try:
                face_dir = _resolve_face_module_dir()
                if face_dir not in sys.path:
                    sys.path.insert(0, face_dir)
                if "train_model" in sys.modules:
                    del sys.modules["train_model"]
                from train_model import train
                train()
                self.win.after(0, lambda: self._face_status_var.set(
                    " Face model trained successfully!"))
            except Exception as e:
                self.win.after(0, lambda err=e: self._face_status_var.set(
                    f" Training failed: {err}"))

        threading.Thread(target=_run, daemon=True).start()

    def _show_qr(self, path, name, roll):
        t = get_theme()
        w = tk.Toplevel(self.win)
        w.title("Registration Successful")
        w.geometry("380x530")
        w.configure(bg=t["bg"])
        w.grab_set()
        tk.Label(w, text=" Registration Successful!",
            font=("Segoe UI", 13, "bold"),
            bg=t["bg"], fg=t["success"]).pack(pady=14)
        tk.Label(w, text=f"Name: {name}\nRoll No: {roll}",
            font=("Segoe UI", 10), bg=t["bg"], fg=t["fg"]).pack()
        face_note = (" Face data captured — AI attendance enabled!"
            if self._face_captured
            else " No face data captured — QR attendance only")
        tk.Label(w, text=face_note,
            font=("Segoe UI", 9, "italic"), bg=t["bg"],
            fg=t["success"] if self._face_captured else t["warning"]
            ).pack(pady=(6, 0))
        tk.Label(w,
            text="Take a screenshot and save it\n"
                "Teacher will scan - attendance will be marked",
                font=("Segoe UI", 9, "italic"),
                bg=t["bg"], fg=t["warning"]).pack(pady=6)
        img   = Image.open(path).resize((220, 220))
        photo = ImageTk.PhotoImage(img)
        lbl   = tk.Label(w, image=photo, bg=t["bg"])
        lbl.image = photo
        lbl.pack()
        tk.Button(w, text="Close", font=("Segoe UI", 10, "bold"),
            bg=t["danger"], fg="white", relief="flat",
            cursor="hand2", command=w.destroy
            ).pack(pady=14, ipadx=20, ipady=6)


# ════════════════════════════════════════════════
#  TEACHER REGISTRATION
# ════════════════════════════════════════════════
class TeacherRegistrationWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Teacher Registration")
        self.win.geometry("520x520")
        self.win.minsize(480, 460)
        self.win.resizable(True, True)
        self.win.grab_set()
        self._lbls    = []
        self._entries = []
        self._build()

    def _build(self):
        t = get_theme()
        self.win.configure(bg=t["bg"])

        topbar = tk.Frame(self.win, bg=t["bg"])
        topbar.pack(fill="x")
        self._tog = _toggle_btn(topbar, self._theme, t)

        self._head_lbl = tk.Label(self.win, text="\u200d Teacher Registration",
            font=("Segoe UI", 16, "bold"),
            bg=t["bg"], fg=t["warning"])
        self._head_lbl.pack(pady=(0, 8))

        self._scroll = ScrollableFrame(self.win, bg=t["bg"])
        self._scroll.pack(fill="both", expand=True, padx=4, pady=4)
        self.form = self._scroll.inner

        self._inner_form = tk.Frame(self.form, bg=t["bg"])
        self._inner_form.pack(fill="x", padx=36)
        inner_form = self._inner_form

        self.v_name    = tk.StringVar()
        self.v_email   = tk.StringVar()
        self.v_pwd     = tk.StringVar()
        self.v_subject = tk.StringVar(value=SUBJECTS[0])

        for lbl_text, var in [
            ("Full Name", self.v_name),
            ("Email ID",  self.v_email),
        ]:
            l = _lbl(inner_form, lbl_text, t)
            l.pack(fill="x", pady=(10, 1))
            self._lbls.append(l)
            e = _entry(inner_form, var, t)
            e.pack(fill="x", ipady=6)
            self._entries.append(e)

        pwd_lbl = _lbl(inner_form, "Password", t)
        pwd_lbl.pack(fill="x", pady=(10, 1))
        self._lbls.append(pwd_lbl)
        self._pwd_widget = PasswordEntry(inner_form, self.v_pwd, t)
        self._pwd_widget.pack(fill="x")

        sl = _lbl(inner_form, "Subject", t)
        sl.pack(fill="x", pady=(10, 1))
        self._lbls.append(sl)

        self._subj_cb = ttk.Combobox(inner_form, textvariable=self.v_subject,
                values=SUBJECTS, state="readonly",
                font=("Segoe UI", 11))
        self._subj_cb.pack(fill="x", ipady=5)

        self._reg_btn = tk.Button(
            inner_form, text=" Register ",
            font=("Segoe UI", 12, "bold"),
            bg=t["warning"], fg="white",
            activebackground=t["btn_login_th"],
            relief="flat", cursor="hand2", bd=0,
            command=self._register
        )
        self._reg_btn.pack(pady=26, ipadx=24, ipady=12, fill="x")

    def _theme(self):
        toggle_theme()
        t = get_theme()
        self.win.configure(bg=t["bg"])
        self._tog.configure(bg=t["toggle_bg"], fg=t["toggle_fg"],
                            text=t["toggle_text"])
        self._head_lbl.configure(bg=t["bg"], fg=t["warning"])
        self._scroll.reconfigure_bg(t["bg"])
        self._inner_form.configure(bg=t["bg"])
        for w in self._inner_form.winfo_children():
            if isinstance(w, tk.Frame):
                w.configure(bg=t["bg"])
        for l in self._lbls:
            l.configure(bg=t["bg"], fg=t["sub_fg"])
        for e in self._entries:
            e.configure(bg=t["entry_bg"], fg=t["fg"], insertbackground=t["fg"])
        self._pwd_widget.reconfigure(t)
        self._reg_btn.configure(bg=t["warning"],
                                activebackground=t["btn_login_th"])

    def _register(self):
        name    = self.v_name.get().strip()
        email   = self.v_email.get().strip()
        pwd     = self.v_pwd.get().strip()
        subject = self.v_subject.get().strip()
        if not all([name, email, pwd, subject]):
            messagebox.showerror("Incomplete", "Fill every field!", parent=self.win)
            return
        conn = cur = None
        try:
            conn = get_connection()
            if not conn:
                messagebox.showerror("DB Error", "Cannot connect to database.",
                        parent=self.win)
                return
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO teachers(name,email,password,subject) VALUES(%s,%s,%s,%s)",
                (name, email, pwd, subject))
            conn.commit()
            tid = cur.lastrowid
            messagebox.showinfo("Success",
                f" Registration successful!\n\n"
                f"Teacher ID: {tid}\n"
                f"Please note this ID — Students will see your name in class.",
                                parent=self.win)
            self.win.destroy()
        except Exception as ex:
            if "Duplicate" in str(ex):
                messagebox.showerror("Already Exists",
                    "This email is already registered!",
                    parent=self.win)
            else:
                messagebox.showerror("DB Error", str(ex), parent=self.win)
        finally:
            if cur:  cur.close()
            if conn: conn.close()