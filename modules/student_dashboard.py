"""
student_dashboard.py  —  AMS Project
Fix: sys.path was adding dirname(dirname(__file__)) = /mnt in a flat layout.
Now inserts both THIS_DIR and PARENT_DIR so imports resolve correctly in both flat and nested project structures.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# ── Path fix ──────────────────────────────────────────────────────────────────
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_THIS_DIR)
for _p in (_THIS_DIR, _PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db.connection import get_connection
from modules.theme import get_theme, toggle_theme
from datetime import date
from PIL import Image, ImageTk


class StudentDashboard:
    def __init__(self, student):
        self.student = student
        self.win = tk.Tk()
        self.win.title(f"Student Dashboard  —  {student['name']}")
        self.win.geometry("900x700")
        self.win.minsize(800, 600)
        self.win.resizable(True, True)
        self._build()
        self.win.mainloop()

    def _build(self):
        t = get_theme()
        self.win.configure(bg=t["bg"])

        # ── Topbar ───────────────────────────────
        topbar = tk.Frame(self.win, bg=t["bg"])
        topbar.pack(fill="x", padx=15, pady=6)
        self._tog = tk.Button(topbar, text=t["toggle_text"],
                font=("Segoe UI", 9, "bold"),
                bg=t["toggle_bg"], fg=t["toggle_fg"],
                relief="flat", cursor="hand2", bd=0,
                command=self._theme)
        self._tog.pack(side="right", ipadx=10, ipady=4)

        # ── Header ───────────────────────────────
        self.hdr = tk.Frame(self.win, bg=t["header_bg"], pady=14)
        self.hdr.pack(fill="x")
        tk.Frame(self.hdr, bg=t["success"], width=5).pack(side="left", fill="y")
        hc = tk.Frame(self.hdr, bg=t["header_bg"])
        hc.pack(side="left", padx=15)
        self._wlbl = tk.Label(hc, text=f" Welcome, {self.student['name']}",
                font=("Segoe UI", 15, "bold"),
                bg=t["header_bg"], fg=t["success"])
        self._wlbl.pack(anchor="w")
        self._ilbl = tk.Label(
            hc,
            text=(f"Roll: {self.student['roll_no']}   |   "
            f"Class: {self.student.get('class', '—')}   |   "
            f"{self.student.get('email', '—')}"),
            font=("Segoe UI", 9), bg=t["header_bg"], fg=t["sub_fg"])
        self._ilbl.pack(anchor="w")

        # ── Stats cards ──────────────────────────
        sf = tk.Frame(self.win, bg=t["bg"], pady=10)
        sf.pack(fill="x", padx=20)
        self.v_total   = tk.StringVar(value="0")
        self.v_present = tk.StringVar(value="0")
        self.v_pct     = tk.StringVar(value="0%")
        for title, var, col in [
            ("Total Classes", self.v_total,   t["btn_reg"]),
            ("Present",       self.v_present, t["success"]),
            ("Attendance %",  self.v_pct,     t["btn_login_t"]),
        ]:
            card = tk.Frame(sf, bg=col, padx=22, pady=12)
            card.pack(side="left", expand=True, fill="both", padx=8)
            tk.Label(card, textvariable=var, font=("Segoe UI", 24, "bold"),
                bg=col, fg="white").pack()
            tk.Label(card, text=title, font=("Segoe UI", 9),
                bg=col, fg="#cceeff").pack()

        # ── Active Classes ────────────────────────
        self._ac_outer = tk.Frame(self.win, bg=t["bg"])
        self._ac_outer.pack(fill="x", padx=20, pady=(6, 2))
        self._ac_hdr = tk.Label(
            self._ac_outer,
            text="🟢  Active Classes  —  Show your QR to Webcam in the Teacher's laptop for Attendance",
            font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["success"])
        self._ac_hdr.pack(anchor="w", pady=(4, 4))

        self._ac_canvas_frame = tk.Frame(self._ac_outer, bg=t["bg"])
        self._ac_canvas_frame.pack(fill="x")
        self._ac_canvas = tk.Canvas(self._ac_canvas_frame, bg=t["bg"],
                        height=110, highlightthickness=0)
        ac_hsb = ttk.Scrollbar(self._ac_canvas_frame, orient="horizontal",
                command=self._ac_canvas.xview)
        self._ac_canvas.configure(xscrollcommand=ac_hsb.set)
        self._ac_cards = tk.Frame(self._ac_canvas, bg=t["bg"])
        self._ac_cards_win = self._ac_canvas.create_window(
            (0, 0), window=self._ac_cards, anchor="nw")
        self._ac_cards.bind("<Configure>", lambda e: self._ac_canvas.configure(
            scrollregion=self._ac_canvas.bbox("all")))
        self._ac_canvas.pack(fill="x")
        ac_hsb.pack(fill="x")

        # ── Notebook tabs ─────────────────────────
        self._nb_outer = tk.Frame(self.win, bg=t["bg"])
        self._nb_outer.pack(fill="both", expand=True, padx=20, pady=8)
        self.nb = ttk.Notebook(self._nb_outer)
        self.nb.pack(fill="both", expand=True)

        sty = ttk.Style()
        sty.theme_use("default")
        sty.configure("TNotebook", background=t["bg"], borderwidth=0)
        sty.configure("TNotebook.Tab", background=t["header_bg"],
            foreground=t["fg"], padding=[14, 7],
            font=("Segoe UI", 9, "bold"))
        sty.map("TNotebook.Tab",
                background=[("selected", t["accent"])],
                foreground=[("selected", "white")])

        self.tab_att = tk.Frame(self.nb, bg=t["header_bg"])
        self.nb.add(self.tab_att, text="  My Attendance  ")
        self._build_att_tab(self.tab_att)

        self.tab_qr = tk.Frame(self.nb, bg=t["header_bg"])
        self.nb.add(self.tab_qr, text="  My QR Code  ")
        self._build_qr_tab(self.tab_qr)

        self.tab_me = tk.Frame(self.nb, bg=t["header_bg"])
        self.nb.add(self.tab_me, text="  My Profile  ")
        self._build_profile_tab(self.tab_me)

        self._load_stats()
        self._load_attendance()
        self._load_active_classes()

    # ─────────────────────────────────────────────
    def _load_active_classes(self):
        for w in self._ac_cards.winfo_children():
            w.destroy()
        t = get_theme()
        conn = cur = None
        try:
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT ac.id, ac.subject, ac.start_time, tc.name AS teacher_name
                FROM active_classes ac
                JOIN teachers tc ON ac.teacher_id = tc.id
                WHERE ac.active = 1
            """)
            classes = cur.fetchall()
        except Exception as ex:
            print("active_classes:", ex)
            classes = []
        finally:
            if cur:  cur.close()
            if conn: conn.close()

        if not classes:
            tk.Label(self._ac_cards,
                text="  There are no classes active right now.",
                font=("Segoe UI", 9, "italic"),
                bg=t["bg"], fg=t["sub_fg"]).pack(anchor="w", pady=4)
            return
        for cls in classes:
            self._ac_card(cls, t)

    def _ac_card(self, cls, t):
        card = tk.Frame(self._ac_cards, bg=t["success"], pady=8, padx=12)
        card.pack(side="left", padx=6, pady=2)
        tk.Label(card, text=f" {cls['subject']}",
            font=("Segoe UI", 9, "bold"),
            bg=t["success"], fg="white", wraplength=160).pack(anchor="w")
        tk.Label(card, text=f" {cls['teacher_name']}",
            font=("Segoe UI", 8),
            bg=t["success"], fg="#d1fae5").pack(anchor="w")
        tk.Button(card, text="📱  Show My QR",
            font=("Segoe UI", 8, "bold"),
            bg=t["btn_reg"], fg="white",
            activebackground=t["btn_reg_h"],
            relief="flat", cursor="hand2",
            command=lambda c=cls: self._show_qr_popup(c)
            ).pack(pady=(6, 0), ipadx=6, ipady=3)

    def _show_qr_popup(self, cls):
        conn = cur = None
        already = False
        try:
            conn = get_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("""SELECT id FROM attendance
                    WHERE student_id=%s AND date=%s AND subject=%s""",
                            (self.student["id"], date.today(), cls["subject"]))
                already = cur.fetchone() is not None
        except Exception as ex:
            print(ex)
        finally:
            if cur:  cur.close()
            if conn: conn.close()

        t = get_theme()
        w = tk.Toplevel(self.win)
        w.title("Show QR Code to Teacher")
        w.geometry("380x530")
        w.configure(bg=t["bg"])
        w.grab_set()

        if already:
            tk.Label(w, text="  Already Marked   !",
                font=("Segoe UI", 13, "bold"),
                bg=t["bg"], fg=t["success"]).pack(pady=20)
            tk.Label(w, text=f"Subject: {cls['subject']}\nAttendance has been marked today.",
                font=("Segoe UI", 10), bg=t["bg"], fg=t["fg"]).pack()
            tk.Button(w, text="Close", font=("Segoe UI", 10, "bold"),
                bg=t["btn_reg"], fg="white", relief="flat",
                cursor="hand2", command=w.destroy
                ).pack(pady=20, ipadx=20, ipady=6)
            return

        tk.Label(w, text=f" {cls['subject']}",
            font=("Segoe UI", 12, "bold"),
            bg=t["bg"], fg=t["accent"], wraplength=340).pack(pady=(14, 2))
        tk.Label(w, text=f"Teacher: {cls['teacher_name']}",
            font=("Segoe UI", 9), bg=t["bg"], fg=t["sub_fg"]).pack()
        tk.Label(w,
            text="  Show this code to your teacher. \n"
            "Teacher will scan through webcam - attendance will be marked",
            font=("Segoe UI", 9, "italic"), bg=t["bg"], fg=t["warning"]).pack(pady=8)

        qr_path = self.student.get("qr_code_path", "")
        if qr_path and os.path.exists(qr_path):
            img   = Image.open(qr_path).resize((260, 260))
            photo = ImageTk.PhotoImage(img)
            lbl   = tk.Label(w, image=photo, bg=t["bg"])
            lbl.image = photo
            lbl.pack(pady=6)
            tk.Label(w,
                text=f"Roll No: {self.student['roll_no']}   Name: {self.student['name']}",
                font=("Segoe UI", 9, "bold"),
                bg=t["bg"], fg=t["fg"]).pack()
        else:
            tk.Label(w, text="  QR Code not found!\nPlease register again.",
                font=("Segoe UI", 11), bg=t["bg"], fg=t["danger"]).pack(pady=40)

        tk.Button(w, text="Close",
                font=("Segoe UI", 10, "bold"),
                bg=t["danger"], fg="white", relief="flat",
                cursor="hand2",
                command=lambda: (w.destroy(),
                        self._load_stats(),
                        self._load_attendance())
            ).pack(pady=14, ipadx=20, ipady=6)

    # ─────────────────────────────────────────────
    def _build_att_tab(self, parent):
        t = get_theme()
        ff = tk.Frame(parent, bg=t["header_bg"], pady=8)
        ff.pack(fill="x", padx=8)
        tk.Label(ff, text="Month:", font=("Segoe UI", 9),
            bg=t["header_bg"], fg=t["sub_fg"]).pack(side="left", padx=6)
        self.v_month = tk.StringVar(value=str(date.today().month))
        ttk.Combobox(ff, textvariable=self.v_month,
            values=[str(i) for i in range(1, 13)],
            width=4, state="readonly").pack(side="left", padx=4)
        tk.Button(ff, text="Filter", font=("Segoe UI", 9, "bold"),
            bg=t["btn_reg"], fg="white", relief="flat", cursor="hand2",
            command=self._load_attendance
            ).pack(side="left", padx=8, ipadx=10, ipady=3)
        tk.Button(ff, text="  Refresh Classes  ", font=("Segoe UI", 9, "bold"),
            bg=t["success"], fg="white", relief="flat", cursor="hand2",
            command=self._load_active_classes
            ).pack(side="right", padx=10, ipadx=8, ipady=3)

        cols = ("Date", "Subject", "Status", "Method", "Teacher")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        sty = ttk.Style()
        sty.configure("Treeview", background=t["tree_bg"], foreground=t["fg"],
                    rowheight=26, fieldbackground=t["tree_field"],
                    font=("Segoe UI", 9))
        sty.configure("Treeview.Heading", background=t["btn_reg"],
                    foreground="white", font=("Segoe UI", 9, "bold"))
        sty.map("Treeview", background=[("selected", t["accent"])])
        for col, w in zip(cols, [110, 230, 75, 80, 160]):
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=w)
        sb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=5)
        sb.pack(side="right", fill="y", pady=5)

    def _build_qr_tab(self, parent):
        t = get_theme()
        tk.Label(parent,
        text=" This is your personal QR code. \n"
            "The teacher will scan this QR using the webcam - then the attendance will be marked\n"
            "Student cannot mark his/her own attendance",
            font=("Segoe UI", 10, "italic"),
            bg=t["header_bg"], fg=t["warning"]).pack(pady=14)
        qr_path = self.student.get("qr_code_path", "")
        if qr_path and os.path.exists(qr_path):
            img   = Image.open(qr_path).resize((270, 270))
            photo = ImageTk.PhotoImage(img)
            lbl   = tk.Label(parent, image=photo, bg=t["header_bg"])
            lbl.image = photo
            lbl.pack(pady=8)
            tk.Label(parent, text=f"Roll No: {self.student['roll_no']}",
                font=("Segoe UI", 11, "bold"),
                bg=t["header_bg"], fg=t["fg"]).pack()
        else:
            tk.Label(parent,
                text=" QR code not found! Please register again. ",
            font=("Segoe UI", 12), bg=t["header_bg"],
            fg=t["danger"]).pack(pady=40)

    def _build_profile_tab(self, parent):
        t = get_theme()
        tk.Label(parent, text=" My Profile ",
                font=("Segoe UI", 13, "bold"),
                bg=t["header_bg"], fg=t["accent"]).pack(pady=14)
        frame = tk.Frame(parent, bg=t["header_bg"])
        frame.pack(padx=40, fill="x")
        for lbl, val in [
            ("Full Name",     self.student.get("name",        "—")),
            ("Roll Number",   self.student.get("roll_no",     "—")),
            ("Class",         self.student.get("class",       "—")),
            ("Email",         self.student.get("email",       "—")),
            ("Date of Birth", self.student.get("dob",         "—")),
            ("Phone Number",  self.student.get("phone",       "—")),
            ("Blood Group",   self.student.get("blood_group", "—")),
        ]:
            row = tk.Frame(frame, bg=t["header_bg"])
            row.pack(fill="x", pady=5)
            tk.Label(row, text=f"{lbl}:", width=16,
                font=("Segoe UI", 10, "bold"),
                bg=t["header_bg"], fg=t["sub_fg"], anchor="w").pack(side="left")
            tk.Label(row, text=str(val),
                font=("Segoe UI", 10),
                bg=t["header_bg"], fg=t["fg"], anchor="w").pack(side="left", padx=6)

    # ─────────────────────────────────────────────
    def _load_stats(self):
        conn = cur = None
        try:
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM attendance WHERE student_id=%s AND status='Present'",
                (self.student["id"],))
            present = cur.fetchone()[0]
            cur.execute(
                """SELECT COUNT(DISTINCT CONCAT(date,'|',COALESCE(subject,'')))
                    FROM attendance WHERE student_id=%s""",
                (self.student["id"],))
            total = cur.fetchone()[0]
            pct = round((present / total) * 100, 1) if total else 0
            self.v_total.set(str(total))
            self.v_present.set(str(present))
            self.v_pct.set(f"{pct}%")
        except Exception as ex:
            print("stats:", ex)
        finally:
            if cur:  cur.close()
            if conn: conn.close()

    def _load_attendance(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = cur = None
        try:
            conn = get_connection()
            if not conn:
                return
            cur = conn.cursor()
            cur.execute("""
                SELECT a.date, COALESCE(a.subject,'—'), a.status, a.method, t.name
                FROM attendance a JOIN teachers t ON a.teacher_id = t.id
                WHERE a.student_id=%s AND MONTH(a.date)=%s
                ORDER BY a.date DESC
            """, (self.student["id"], self.v_month.get()))
            rows = cur.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
            if not rows:
                self.tree.insert("", "end",
                    values=("—", "No record this month", "—", "—", "—"))
        except Exception as ex:
            print("load_att:", ex)
        finally:
            if cur:  cur.close()
            if conn: conn.close()

    # ─────────────────────────────────────────────
    def _theme(self):
        toggle_theme()
        t = get_theme()
        self.win.configure(bg=t["bg"])
        self._tog.configure(bg=t["toggle_bg"], fg=t["toggle_fg"],
                            text=t["toggle_text"])
        self.hdr.configure(bg=t["header_bg"])
        self._wlbl.configure(bg=t["header_bg"], fg=t["success"])
        self._ilbl.configure(bg=t["header_bg"], fg=t["sub_fg"])
        self._ac_outer.configure(bg=t["bg"])
        self._ac_hdr.configure(bg=t["bg"], fg=t["success"])
        self._ac_canvas_frame.configure(bg=t["bg"])
        self._ac_canvas.configure(bg=t["bg"])
        self._ac_cards.configure(bg=t["bg"])
        self._nb_outer.configure(bg=t["bg"])
        sty = ttk.Style()
        sty.configure("Treeview",
                background=t["tree_bg"], foreground=t["fg"],
                fieldbackground=t["tree_field"])


if __name__ == "__main__":
    StudentDashboard({
        "id": 1, "name": "Md Shahnawaz Ansari",
        "roll_no": "CSE24011445013", "class": "CSE-4th Sem.",
        "email": "mdansari@gmail.com", "dob": "2003-03-15",
        "phone": "7858921784", "blood_group": "A+",
        "qr_code_path": "assets/qrcodes/CSE24011445013.png"
    })