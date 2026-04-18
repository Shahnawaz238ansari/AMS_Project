import tkinter as tk
from tkinter import messagebox
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.theme import get_theme, toggle_theme


class MainMenuWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Attendance Management System")
        self.root.geometry("600x520")
        self.root.resizable(True, True)

        self._all_section_lbls = []

        self._build()

    # ─────────────────────────────────────────────
    def _build(self):
        t = get_theme()
        self.root.configure(bg=t["bg"])

        # ── Top bar ──────────────────────────────
        topbar = tk.Frame(self.root, bg=t["bg"], pady=6)
        topbar.pack(fill="x", padx=15)

        self.toggle_btn = tk.Button(
            topbar, text=t["toggle_text"],
            font=("Segoe UI", 9, "bold"),
            bg=t["toggle_bg"], fg=t["toggle_fg"],
            relief="flat", cursor="hand2", bd=0,
            command=self._switch_theme
        )
        self.toggle_btn.pack(side="right", ipadx=10, ipady=4)

        # ── Header card ──────────────────────────
        self.hdr = tk.Frame(self.root, bg=t["header_bg"], pady=28)
        self.hdr.pack(fill="x")

        tk.Frame(self.hdr, bg=t["accent"], width=5).pack(
            side="left", fill="y", padx=(0, 15)
        )

        txt_col = tk.Frame(self.hdr, bg=t["header_bg"])
        txt_col.pack(side="left")

        self.title_lbl = tk.Label(
            txt_col, text="Attendance Management System",
            font=("Segoe UI", 18, "bold"),
            bg=t["header_bg"], fg=t["accent"]
        )
        self.title_lbl.pack(anchor="w")

        self.sub_lbl = tk.Label(
            txt_col, text="QR Code  •  Face Detection  •  Smart Reports",
            font=("Segoe UI", 10),
            bg=t["header_bg"], fg=t["sub_fg"]
        )
        self.sub_lbl.pack(anchor="w", pady=(2, 0))

        # ── Body ─────────────────────────────────
        self.body = tk.Frame(self.root, bg=t["bg"])
        self.body.pack(fill="both", expand=True, padx=40, pady=20)

        # ── Section: Registration ─────────────────
        self._section_label("📋  Registration", t)

        reg_row = tk.Frame(self.body, bg=t["bg"])
        reg_row.pack(fill="x", pady=(4, 12))

        self.btn_sreg = self._btn(
            reg_row, "👤  Student Registration",
            t["btn_reg"], t["btn_reg_h"],
            self.open_student_registration
        )
        self.btn_sreg.pack(side="left", expand=True, fill="x", padx=(0, 6), ipady=11)

        self.btn_treg = self._btn(
            reg_row, "🏫  Teacher Registration",
            t["btn_reg"], t["btn_reg_h"],
            self.open_teacher_registration
        )
        self.btn_treg.pack(side="left", expand=True, fill="x", padx=(6, 0), ipady=11)

        # ── Divider ──────────────────────────────
        tk.Frame(self.body, bg=t["divider"], height=1).pack(fill="x", pady=6)

        # ── Section: Login ────────────────────────
        self._section_label("🔑  Login", t)

        login_row = tk.Frame(self.body, bg=t["bg"])
        login_row.pack(fill="x", pady=(4, 12))

        self.btn_slogin = self._btn(
            login_row, "🎓  Student Login",
            t["btn_login_s"], t["btn_login_sh"],
            self.open_student_login
        )
        self.btn_slogin.pack(side="left", expand=True, fill="x",
        padx=(0, 6), ipady=11)

        self.btn_tlogin = self._btn(
            login_row, "👨‍🏫  Teacher Login",
            t["btn_login_t"], t["btn_login_th"],
            self.open_teacher_login
        )
        self.btn_tlogin.pack(side="left", expand=True, fill="x",
            padx=(6, 0), ipady=11)

        # ── Footer ───────────────────────────────
        self.footer = tk.Label(
            self.root,
            text="Attendance Management System  •  AMS Project",
            font=("Segoe UI", 8),
            bg=t["bg"], fg=t["sub_fg"]
        )
        self.footer.pack(side="bottom", pady=10)

    def _section_label(self, text, t):
        lbl = tk.Label(
            self.body, text=text,
            font=("Segoe UI", 10, "bold"),
            bg=t["bg"], fg=t["sub_fg"]
        )
        lbl.pack(anchor="w", pady=(6, 0))
        self._all_section_lbls.append(lbl)
        return lbl

    def _btn(self, parent, text, color, hover, cmd):
        b = tk.Button(
            parent, text=text,
            font=("Segoe UI", 11, "bold"),
            bg=color, fg="white",
            activebackground=hover, activeforeground="white",
            relief="flat", cursor="hand2", bd=0,
            command=cmd
        )
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    # ─────────────────────────────────────────────
    def _switch_theme(self):
        toggle_theme()
        t = get_theme()
        self.root.configure(bg=t["bg"])
        self.toggle_btn.configure(bg=t["toggle_bg"], fg=t["toggle_fg"],
                text=t["toggle_text"])
        self.hdr.configure(bg=t["header_bg"])
        self.title_lbl.configure(bg=t["header_bg"], fg=t["accent"])
        self.sub_lbl.configure(bg=t["header_bg"], fg=t["sub_fg"])
        self.body.configure(bg=t["bg"])
        self.footer.configure(bg=t["bg"], fg=t["sub_fg"])
        for lbl in self._all_section_lbls:
            lbl.configure(bg=t["bg"], fg=t["sub_fg"])

    # ─────────────────────────────────────────────
    def open_student_registration(self):
        from modules.registration_window import StudentRegistrationWindow
        StudentRegistrationWindow(self.root)

    def open_teacher_registration(self):
        from modules.registration_window import TeacherRegistrationWindow
        TeacherRegistrationWindow(self.root)

    def open_student_login(self):
        from modules.login_window import StudentLoginWindow
        StudentLoginWindow(self.root)

    def open_teacher_login(self):
        from modules.login_window import TeacherLoginWindow
        TeacherLoginWindow(self.root)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MainMenuWindow().run()