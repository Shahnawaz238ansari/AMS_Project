"""
login_window.py  —  AMS Project
Student & Teacher login windows with:
• Password visibility toggle (eye icon)
• Correct sys.path for both flat & nested layouts
• Proper theme propagation including title fg colour
"""
import tkinter as tk
from tkinter import messagebox
import sys
import os

# ── Path fix: add the directory that *contains* db/ and modules/ ──────────────
# Supports both layouts:
#   Flat  (all .py in one folder)  → add THIS folder
#   Nested (files inside modules/) → add PARENT folder
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
for _p in (_THIS_DIR, _PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db.connection import get_connection
from modules.theme import get_theme, toggle_theme

# ─── Password field with eye-toggle ──────────────────────────────────────────
class _PasswordEntry(tk.Frame):
    """Single-line password Entry with a 👁 / 🙈 visibility toggle."""

    def __init__(self, parent, var: tk.StringVar, t: dict, **kwargs):
        super().__init__(parent, bg=t["bg"], **kwargs)
        self._t       = t
        self._visible = False
        self._var     = var

        self._entry = tk.Entry(
            self, textvariable=var,
            font=("Segoe UI", 12),
            bg=t["entry_bg"], fg=t["fg"],
            insertbackground=t["fg"],
            relief="flat", bd=8, show="●"
        )
        self._entry.pack(side="left", fill="x", expand=True, ipady=6)

        self._eye = tk.Button(
            self, text="👁",
            font=("Segoe UI", 11),
            bg=t["entry_bg"], fg=t["sub_fg"],
            activebackground=t["entry_bg"],
            relief="flat", cursor="hand2", bd=0,
            command=self._toggle
        )
        self._eye.pack(side="right", padx=(0, 6))

    def _toggle(self):
        self._visible = not self._visible
        self._entry.config(show="" if self._visible else "●")
        self._eye.config(
            text="🙈" if self._visible else "👁",
            fg=self._t["accent"] if self._visible else self._t["sub_fg"]
        )

    def reconfigure(self, t: dict):
        self._t = t
        self.configure(bg=t["bg"])
        self._entry.configure(
            bg=t["entry_bg"], fg=t["fg"], insertbackground=t["fg"]
        )
        self._eye.configure(
            bg=t["entry_bg"], activebackground=t["entry_bg"],
            fg=t["accent"] if self._visible else t["sub_fg"]
        )


# ─── Internal theme helper ────────────────────────────────────────────────────
def _apply_theme(win, tog, title_lbl, title_fg_key, form,
        lbls, plain_entries, pwd_widget):
    """Re-apply the current theme to every widget in a login window."""
    t = get_theme()
    win.configure(bg=t["bg"])
    tog.configure(bg=t["toggle_bg"], fg=t["toggle_fg"], text=t["toggle_text"])
    title_lbl.configure(bg=t["bg"], fg=t[title_fg_key])   # ← fix: fg updated
    form.configure(bg=t["bg"])
    for lbl in lbls:
        lbl.configure(bg=t["bg"], fg=t["sub_fg"])
    for e in plain_entries:
        e.configure(bg=t["entry_bg"], fg=t["fg"], insertbackground=t["fg"])
    if pwd_widget:
        pwd_widget.reconfigure(t)


# ════════════════════════════════════════════════
#  STUDENT LOGIN
# ════════════════════════════════════════════════
class StudentLoginWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Student Login")
        self.win.geometry("560x460")
        self.win.resizable(False, False)
        self.win.grab_set()
        self._lbls         = []
        self._plain_entries= []
        self._pwd_widget   = None
        self._build()

    def _build(self):
        t = get_theme()
        self.win.configure(bg=t["bg"])

        # ── Topbar ───────────────────────────────
        topbar = tk.Frame(self.win, bg=t["bg"])
        topbar.pack(fill="x")
        self._tog = tk.Button(
            topbar, text=t["toggle_text"],
            font=("Segoe UI", 9, "bold"),
            bg=t["toggle_bg"], fg=t["toggle_fg"],
            relief="flat", cursor="hand2", bd=0,
            command=self._theme
        )
        self._tog.pack(anchor="ne", padx=12, pady=6, ipadx=10, ipady=4)

        # ── Title ────────────────────────────────
        self._title = tk.Label(
            self.win, text=" Student Login ",
            font=("Segoe UI", 16, "bold"),
            bg=t["bg"], fg=t["success"]
        )
        self._title.pack(pady=(0, 14))

        # ── Form ─────────────────────────────────
        self.form = tk.Frame(self.win, bg=t["bg"])
        self.form.pack(padx=46, fill="x")

        self.v_roll = tk.StringVar()
        self.v_pwd  = tk.StringVar()

        # Roll Number (plain entry)
        l = tk.Label(self.form, text="Roll Number",
            font=("Segoe UI", 10),
            bg=t["bg"], fg=t["sub_fg"], anchor="w")
        l.pack(fill="x", pady=(12, 2))
        self._lbls.append(l)

        e = tk.Entry(self.form, textvariable=self.v_roll,
            font=("Segoe UI", 12),
            bg=t["entry_bg"], fg=t["fg"],
            insertbackground=t["fg"],
            relief="flat", bd=8)
        e.pack(fill="x", ipady=6)
        self._plain_entries.append(e)

        # Password (eye-toggle widget)
        l2 = tk.Label(self.form, text="Password",
            font=("Segoe UI", 10),
            bg=t["bg"], fg=t["sub_fg"], anchor="w")
        l2.pack(fill="x", pady=(12, 2))
        self._lbls.append(l2)

        self._pwd_widget = _PasswordEntry(self.form, self.v_pwd, t)
        self._pwd_widget.pack(fill="x")

        # ── Login button ─────────────────────────
        self._login_btn = tk.Button(
            self.win, text="Login",
            font=("Segoe UI", 12, "bold"),
            bg=t["btn_login_s"], fg="white",
            activebackground=t["btn_login_sh"],
            relief="flat", cursor="hand2", bd=0,
            command=self._login
        )
        self._login_btn.pack(pady=24, ipadx=34, ipady=10)

        self.win.bind("<Return>", lambda e: self._login())

    def _theme(self):
        toggle_theme()
        t = get_theme()
        _apply_theme(self.win, self._tog, self._title, "success",
            self.form, self._lbls, self._plain_entries,
            self._pwd_widget)
        self._login_btn.configure(
            bg=t["btn_login_s"], activebackground=t["btn_login_sh"])

    def _login(self):
        roll = self.v_roll.get().strip()
        pwd  = self.v_pwd.get().strip()
        if not roll or not pwd:
            messagebox.showerror("Error", "Enter Roll Number and Password!",
                parent=self.win)
            return
        conn = cur = None
        try:
            conn = get_connection()
            if not conn:
                messagebox.showerror("DB Error", "Cannot connect to database.",
                    parent=self.win)
                return
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM students WHERE roll_no=%s AND password=%s",
                (roll, pwd))
            student = cur.fetchone()
            if student:
                self.win.destroy()
                from modules.student_dashboard import StudentDashboard
                StudentDashboard(student)
            else:
                messagebox.showerror("Login Failed",
                    "Wrong Roll Number or Password!", parent=self.win)
        except Exception as ex:
            messagebox.showerror("Error", str(ex), parent=self.win)
        finally:
            if cur:  cur.close()
            if conn: conn.close()

# ════════════════════════════════════════════════
#  TEACHER LOGIN
# ════════════════════════════════════════════════
class TeacherLoginWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Teacher Login")
        self.win.geometry("560x460")
        self.win.resizable(False, False)
        self.win.grab_set()
        self._lbls         = []
        self._plain_entries= []
        self._pwd_widget   = None
        self._build()

    def _build(self):
        t = get_theme()
        self.win.configure(bg=t["bg"])

        # ── Topbar ───────────────────────────────
        topbar = tk.Frame(self.win, bg=t["bg"])
        topbar.pack(fill="x")
        self._tog = tk.Button(
            topbar, text=t["toggle_text"],
            font=("Segoe UI", 9, "bold"),
            bg=t["toggle_bg"], fg=t["toggle_fg"],
            relief="flat", cursor="hand2", bd=0,
            command=self._theme
        )
        self._tog.pack(anchor="ne", padx=12, pady=6, ipadx=10, ipady=4)

        # ── Title ────────────────────────────────
        self._title = tk.Label(
            self.win, text=" Teacher Login ",
            font=("Segoe UI", 16, "bold"),
            bg=t["bg"], fg=t["warning"]
        )
        self._title.pack(pady=(0, 14))

        # ── Form ─────────────────────────────────
        self.form = tk.Frame(self.win, bg=t["bg"])
        self.form.pack(padx=46, fill="x")

        self.v_email = tk.StringVar()
        self.v_pwd   = tk.StringVar()

        # Email (plain entry)
        l = tk.Label(self.form, text="Email ID",
                font=("Segoe UI", 10),
                bg=t["bg"], fg=t["sub_fg"], anchor="w")
        l.pack(fill="x", pady=(12, 2))
        self._lbls.append(l)

        e = tk.Entry(self.form, textvariable=self.v_email,
            font=("Segoe UI", 12),
            bg=t["entry_bg"], fg=t["fg"],
            insertbackground=t["fg"],
            relief="flat", bd=8)
        e.pack(fill="x", ipady=6)
        self._plain_entries.append(e)

        # Password (eye-toggle widget)
        l2 = tk.Label(self.form, text="Password",
                font=("Segoe UI", 10),
                bg=t["bg"], fg=t["sub_fg"], anchor="w")
        l2.pack(fill="x", pady=(12, 2))
        self._lbls.append(l2)

        self._pwd_widget = _PasswordEntry(self.form, self.v_pwd, t)
        self._pwd_widget.pack(fill="x")

        # ── Login button ─────────────────────────
        self._login_btn = tk.Button(
            self.win, text="Login",
            font=("Segoe UI", 12, "bold"),
            bg=t["btn_login_t"], fg="white",
            activebackground=t["btn_login_th"],
            relief="flat", cursor="hand2", bd=0,
            command=self._login
        )
        self._login_btn.pack(pady=24, ipadx=34, ipady=10)

        self.win.bind("<Return>", lambda e: self._login())

    def _theme(self):
        toggle_theme()
        t = get_theme()
        _apply_theme(self.win, self._tog, self._title, "warning",
            self.form, self._lbls, self._plain_entries,
            self._pwd_widget)
        self._login_btn.configure(
            bg=t["btn_login_t"], activebackground=t["btn_login_th"])

    def _login(self):
        email = self.v_email.get().strip()
        pwd   = self.v_pwd.get().strip()
        if not email or not pwd:
            messagebox.showerror("Error", "Enter Email and Password!",
                parent=self.win)
            return
        conn = cur = None
        try:
            conn = get_connection()
            if not conn:
                messagebox.showerror("DB Error", "Cannot connect to database.",
                    parent=self.win)
                return
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT * FROM teachers WHERE email=%s AND password=%s",
                (email, pwd))
            teacher = cur.fetchone()
            if teacher:
                self.win.destroy()
                from modules.teacher_dashboard import TeacherDashboard
                TeacherDashboard(teacher)
            else:
                messagebox.showerror("Login Failed",
                    "Wrong Email or Password!", parent=self.win)
        except Exception as ex:
            messagebox.showerror("Error", str(ex), parent=self.win)
        finally:
            if cur:  cur.close()
            if conn: conn.close()