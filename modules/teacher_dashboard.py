# ═══════════════════════════════════════════════════════════════════════════
#  teacher_dashboard.py  —  AMS Project
# ═══════════════════════════════════════════════════════════════════════════
import tkinter as tk
from tkinter import ttk, messagebox
import sys, os, threading, csv
from datetime import date, datetime

THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR  = os.path.dirname(THIS_DIR)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

FACE_MODULE_DIR = os.path.join(ROOT_DIR, "face_module")
EXPORT_DIR      = os.path.join(ROOT_DIR, "attendance_exports")

from db.connection import get_connection
from modules.theme import get_theme, toggle_theme
import cv2
from pyzbar.pyzbar import decode, ZBarSymbol

SUBJECTS = [
    "Operating System",
    "Design and Analysis of Algorithm",
    "Modelling and Optimization Techniques",
    "Advanced Programming Practice",
    "Computer Networks",
    "Audit Course",
]
SUBJ_PALETTE = [
    ("#0369a1", "#0284c7"),
    ("#059669", "#10b981"),
    ("#7c3aed", "#8b5cf6"),
    ("#b45309", "#d97706"),
    ("#be123c", "#e11d48"),
    ("#0f766e", "#0d9488"),
]
ROW_ODD  = "odd"
ROW_EVEN = "even"


def _normalise_date(raw: str) -> str:
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return str(date.today())


class TeacherDashboard:
    def __init__(self, teacher):
        self.teacher     = teacher
        self.active_subj = None

        self.win = tk.Tk()
        self.win.title(f"Teacher Dashboard  —  {teacher['name']}")
        self.win.geometry("1150x760")
        self.win.minsize(920, 640)
        self.win.resizable(True, True)
        self._build()
        self.win.mainloop()

    # ─────────────────────────────────────────────
    def _build(self):
        t = get_theme()
        self.win.configure(bg=t["bg"])

        # Topbar
        topbar = tk.Frame(self.win, bg=t["bg"])
        topbar.pack(fill="x", padx=15, pady=6)
        self._tog = tk.Button(topbar, text=t["toggle_text"],
            font=("Segoe UI", 9, "bold"),
            bg=t["toggle_bg"], fg=t["toggle_fg"],
            relief="flat", cursor="hand2", bd=0,
            command=self._theme)
        self._tog.pack(side="right", ipadx=10, ipady=4)

        # Header
        self.hdr = tk.Frame(self.win, bg=t["header_bg"], pady=14)
        self.hdr.pack(fill="x")
        tk.Frame(self.hdr, bg=t["warning"], width=5).pack(side="left", fill="y")
        hdr_txt = tk.Frame(self.hdr, bg=t["header_bg"])
        hdr_txt.pack(side="left", padx=15)
        self._wlbl = tk.Label(hdr_txt,
            text=f"\u200d  Welcome, {self.teacher['name']}",
            font=("Segoe UI", 16, "bold"),
            bg=t["header_bg"], fg=t["warning"])
        self._wlbl.pack(anchor="w")
        self._ilbl = tk.Label(hdr_txt,
            text=(f"Subject: {self.teacher['subject']}   |   "
                  f"ID: {self.teacher['id']}   |   "
                  f"Email: {self.teacher.get('email','—')}"),
            font=("Segoe UI", 9), bg=t["header_bg"], fg=t["sub_fg"])
        self._ilbl.pack(anchor="w")

        # Active class banner
        self.banner = tk.Frame(self.win, bg=t["success"], pady=8)
        self._blbl  = tk.Label(self.banner, text="",
            font=("Segoe UI", 10, "bold"), bg=t["success"], fg="white")
        self._blbl.pack(side="left", padx=16)
        tk.Button(self.banner, text="⏹  End Class",
            font=("Segoe UI", 9, "bold"),
            bg=t["danger"], fg="white", relief="flat", cursor="hand2",
            command=self._end_class
        ).pack(side="right", padx=14, ipadx=10, ipady=4)

        # Body
        self._body = tk.Frame(self.win, bg=t["bg"])
        self._body.pack(fill="both", expand=True, padx=16, pady=10)

        # LEFT panel (scrollable canvas)
        left_outer = tk.Frame(self._body, bg=t["bg"], width=395)
        left_outer.pack(side="left", fill="y", padx=(0, 12))
        left_outer.pack_propagate(False)

        self._lcanvas = tk.Canvas(left_outer, bg=t["bg"], highlightthickness=0)
        lsb = ttk.Scrollbar(left_outer, orient="vertical",
                    command=self._lcanvas.yview)
        self._lcanvas.configure(yscrollcommand=lsb.set)
        lsb.pack(side="right", fill="y")
        self._lcanvas.pack(side="left", fill="both", expand=True)
        self._left = tk.Frame(self._lcanvas, bg=t["bg"])
        self._lwin = self._lcanvas.create_window(
            (0, 0), window=self._left, anchor="nw")
        self._left.bind("<Configure>", lambda e: (
            self._lcanvas.configure(scrollregion=self._lcanvas.bbox("all")),
            self._lcanvas.itemconfig(self._lwin,
                        width=self._lcanvas.winfo_width())))
        self._lcanvas.bind("<Configure>", lambda e:
            self._lcanvas.itemconfig(self._lwin, width=e.width))
        self._left.bind_all("<MouseWheel>", lambda e:
            self._lcanvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._build_left_panel(t)

        # RIGHT panel
        self._right = tk.Frame(self._body, bg=t["bg"])
        self._right.pack(side="left", fill="both", expand=True)
        self._build_right_panel(t)

        self._load_report()
        self._load_stats()

    # ─────────────────────────────────────────────
    def _build_left_panel(self, t):
        left = self._left

        self._slbl = tk.Label(left, text="  Select Subject → Start Class",
            font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["sub_fg"])
        self._slbl.pack(anchor="w", pady=(4, 6))

        grid = tk.Frame(left, bg=t["bg"])
        grid.pack(fill="x")
        self._subj_grid = grid
        self._subj_btns = []
        for i, (subj, (col, hov)) in enumerate(zip(SUBJECTS, SUBJ_PALETTE)):
            r, c = divmod(i, 2)
            b = tk.Button(grid, text=subj,
                font=("Segoe UI", 8, "bold"),
                bg=col, fg="white", activebackground=hov,
                relief="flat", cursor="hand2",
                wraplength=165, justify="left",
                width=20, height=3, anchor="w",
                command=lambda s=subj: self._start_class(s))
            b.grid(row=r, column=c, padx=3, pady=3, sticky="ew")
            b.bind("<Enter>", lambda e, b=b, h=hov: b.config(bg=h))
            b.bind("<Leave>", lambda e, b=b, c=col: b.config(bg=c))
            self._subj_btns.append(b)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        tk.Frame(left, bg=t["divider"], height=1).pack(fill="x", pady=10)

        self._act_lbl = tk.Label(left, text="  Actions",
            font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["sub_fg"])
        self._act_lbl.pack(anchor="w", pady=(0, 6))

        # Store action config so we can update colours on theme toggle
        self._action_cfg = [
            ("  QR Attendance  (Webcam)",  "btn_reg",     "btn_reg_h",    self._qr_scan),
            ("  Face Attendance  (AI)",     "btn_attend",  "btn_attend_h", self._face_scan),
            ("  View / Refresh Report",     "btn_login_t", "btn_login_th", self._refresh),
            ("  Export CSV",                "success",     "btn_login_sh", self._export_csv),
        ]
        self._act_btns = []
        for txt, col_key, hov_key, cmd in self._action_cfg:
            col = t[col_key]; hov = t[hov_key]
            b = tk.Button(left, text=txt,
                font=("Segoe UI", 10, "bold"),
                bg=col, fg="white", activebackground=hov,
                relief="flat", cursor="hand2", bd=0,
                command=cmd)
            b.pack(fill="x", pady=3, ipady=9)
            # Store theme key references on the widget for easy update
            b._col_key = col_key
            b._hov_key = hov_key
            b.bind("<Enter>", lambda e, b=b: b.config(bg=get_theme()[b._hov_key]))
            b.bind("<Leave>", lambda e, b=b: b.config(bg=get_theme()[b._col_key]))
            self._act_btns.append(b)

        tk.Frame(left, bg=t["divider"], height=1).pack(fill="x", pady=10)

        self._stats_lbl = tk.Label(left, text="  Today's Stats  ",
            font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["sub_fg"])
        self._stats_lbl.pack(anchor="w", pady=(0, 6))

        sf = tk.Frame(left, bg=t["bg"])
        sf.pack(fill="x")
        self._stats_frame = sf
        self.v_today = tk.StringVar(value="0")
        self.v_total = tk.StringVar(value="0")
        self._stat_cards = []
        for title, var, col_key in [
            ("Today Present",  self.v_today, "success"),
            ("Total Students", self.v_total, "btn_reg"),
        ]:
            col = t[col_key]
            card = tk.Frame(sf, bg=col, padx=16, pady=12)
            card.pack(side="left", expand=True, fill="both", padx=3)
            card._col_key = col_key
            tk.Label(card, textvariable=var,
                font=("Segoe UI", 22, "bold"), bg=col, fg="white").pack()
            tk.Label(card, text=title, font=("Segoe UI", 8),
                bg=col, fg="#ccffcc").pack()
            self._stat_cards.append(card)

        tk.Frame(left, bg=t["divider"], height=1).pack(fill="x", pady=10)
        self._active_info_frame = tk.Frame(left, bg=t["header_bg"],
                            padx=10, pady=10)
        self._active_info_lbl = tk.Label(self._active_info_frame,
            text="No active class",
            font=("Segoe UI", 9, "italic"),
            bg=t["header_bg"], fg=t["sub_fg"],
            wraplength=350, justify="left")
        self._active_info_lbl.pack(anchor="w")
        self._active_info_frame.pack(fill="x", pady=(0, 8))

    # ══════════════════════════════════════════════
    def _build_right_panel(self, t):
        right = self._right

        ff = tk.Frame(right, bg=t["bg"])
        ff.pack(fill="x", pady=(0, 6))
        self._ff = ff

        self._dflbl = tk.Label(ff, text="Filter by Date:",
            font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["sub_fg"])
        self._dflbl.pack(side="left", padx=(0, 4))

        self.v_date = tk.StringVar(value=str(date.today()))
        self._date_e = tk.Entry(ff, textvariable=self.v_date,
            font=("Segoe UI", 10), width=13,
            bg=t["entry_bg"], fg=t["fg"],
            insertbackground=t["fg"], relief="flat", bd=6)
        self._date_e.pack(side="left", padx=4, ipady=4)

        self._search_btn = tk.Button(ff, text="🔍 Search",
            font=("Segoe UI", 9, "bold"),
            bg=t["btn_reg"], fg="white", relief="flat", cursor="hand2",
            command=self._load_report)
        self._search_btn.pack(side="left", padx=4, ipadx=8, ipady=4)

        self._today_btn = tk.Button(ff, text="Today",
            font=("Segoe UI", 9),
            bg=t["divider"], fg=t["fg"],
            relief="flat", cursor="hand2",
            command=lambda: (self.v_date.set(str(date.today())),
                    self._load_report()))
        self._today_btn.pack(side="left", ipadx=6, ipady=4)

        self.v_subj_filter = tk.StringVar(value="All Subjects")
        self._subj_cb = ttk.Combobox(ff, textvariable=self.v_subj_filter,
            values=["All Subjects"] + SUBJECTS,
            state="readonly", width=24,
            font=("Segoe UI", 9))
        self._subj_cb.pack(side="left", padx=8, ipady=3)
        self._subj_cb.bind("<<ComboboxSelected>>", lambda e: self._load_report())

        self._row_count_var = tk.StringVar(value="0 records")
        self._row_count_lbl = tk.Label(ff, textvariable=self._row_count_var,
            font=("Segoe UI", 8, "italic"),
            bg=t["bg"], fg=t["sub_fg"])
        self._row_count_lbl.pack(side="right", padx=8)

        self._report_lbl = tk.Label(right, text=" Attendance Report ",
            font=("Segoe UI", 10, "bold"), bg=t["bg"], fg=t["sub_fg"])
        self._report_lbl.pack(anchor="w", pady=(2, 4))

        tree_frame = tk.Frame(right, bg=t["bg"])
        tree_frame.pack(fill="both", expand=True)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("Roll No", "Name", "Subject", "Status", "Method", "Date", "Time")
        self.tree = ttk.Treeview(tree_frame, columns=cols,
                    show="headings", selectmode="extended")
        self._style_tree(t)

        col_cfg = [
            ("Roll No",  115, 80,  "center"),
            ("Name",     195, 120, "w"),
            ("Subject",  265, 140, "w"),
            ("Status",    80,  60, "center"),
            ("Method",    80,  60, "center"),
            ("Date",     110,  80, "center"),
            ("Time",      75,  55, "center"),
        ]
        for col, w, mw, anch in col_cfg:
            self.tree.heading(col, text=col,
                command=lambda c=col: self._sort_tree(c, False))
            self.tree.column(col, anchor=anch, width=w, minwidth=mw,
                stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure(ROW_ODD,   background=t["tree_bg"])
        self.tree.tag_configure(ROW_EVEN,  background=t["tree_field"])
        self.tree.tag_configure("present", foreground=t["success"])
        self.tree.tag_configure("absent",  foreground=t["danger"])
        self.tree.tag_configure("face_row",foreground=t["accent"])

        self._ctx = tk.Menu(self.win, tearoff=0)
        self._ctx.add_command(label="📋  Copy Row", command=self._copy_row)
        self.tree.bind("<Button-3>", self._show_ctx)
        self.tree.bind("<MouseWheel>", lambda e:
            self.tree.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._status_bar = tk.Label(right, text="Ready",
            font=("Segoe UI", 8),
            bg=t["header_bg"], fg=t["sub_fg"],
            anchor="w", padx=8, pady=3)
        self._status_bar.pack(fill="x", side="bottom")

    # ─────────────────────────────────────────────
    def _sort_tree(self, col, reverse):
        data = [(self.tree.set(ch, col), ch)
                for ch in self.tree.get_children("")]
        data.sort(reverse=reverse)
        for idx, (_, ch) in enumerate(data):
            self.tree.move(ch, "", idx)
            tag = ROW_ODD if idx % 2 == 0 else ROW_EVEN
            existing = [x for x in self.tree.item(ch, "tags")
                        if x not in (ROW_ODD, ROW_EVEN)]
            self.tree.item(ch, tags=[tag] + existing)
        self.tree.heading(col,
            command=lambda: self._sort_tree(col, not reverse))

    def _show_ctx(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self._ctx.tk_popup(event.x_root, event.y_root)

    def _copy_row(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.win.clipboard_clear()
        self.win.clipboard_append("\t".join(str(v) for v in vals))
        self._status_bar.config(text="Row copied to clipboard.")

    # ─────────────────────────────────────────────
    def _export_csv(self):
        """
        Export a single consolidated CSV for the selected date (and optional
        subject filter).  All attendance methods (QR + Face) are merged into
        one file with an 'Attendance Method' column so teachers never have to
        manage separate sheets per capture method.
        """
        d    = _normalise_date(self.v_date.get())
        subj = self.v_subj_filter.get()

        # ── Pull ALL records for this date/subject directly from the DB ──────
        conn = cur = None
        db_rows = []
        try:
            conn = get_connection()
            cur  = conn.cursor()
            if subj == "All Subjects":
                cur.execute("""
                    SELECT s.roll_no, s.name,
                        COALESCE(a.subject, '—'),
                        a.status,
                        a.method,
                        a.date,
                        COALESCE(TIME_FORMAT(a.created_at, '%H:%i'), '—')
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.date = %s
                    ORDER BY COALESCE(a.subject,''), s.roll_no
                """, (d,))
            else:
                cur.execute("""
                    SELECT s.roll_no, s.name,
                        COALESCE(a.subject, '—'),
                        a.status,
                        a.method,
                        a.date,
                        COALESCE(TIME_FORMAT(a.created_at, '%H:%i'), '—')
                    FROM attendance a
                    JOIN students s ON a.student_id = s.id
                    WHERE a.date = %s AND a.subject = %s
                    ORDER BY s.roll_no
                """, (d, subj))
            db_rows = cur.fetchall()
        except Exception:
            # Fallback: created_at column may not exist — omit Time column
            try:
                if subj == "All Subjects":
                    cur.execute("""
                        SELECT s.roll_no, s.name,
                            COALESCE(a.subject, '—'),
                            a.status, a.method, a.date, '—'
                        FROM attendance a
                        JOIN students s ON a.student_id = s.id
                        WHERE a.date = %s
                        ORDER BY COALESCE(a.subject,''), s.roll_no
                    """, (d,))
                else:
                    cur.execute("""
                        SELECT s.roll_no, s.name,
                            COALESCE(a.subject, '—'),
                            a.status, a.method, a.date, '—'
                        FROM attendance a
                        JOIN students s ON a.student_id = s.id
                        WHERE a.date = %s AND a.subject = %s
                        ORDER BY s.roll_no
                    """, (d, subj))
                db_rows = cur.fetchall()
            except Exception as ex:
                messagebox.showerror("Export Error",
                    f"Could not fetch data from database:\n{ex}",
                    parent=self.win)
                return
        finally:
            if cur:  cur.close()
            if conn: conn.close()

        if not db_rows:
            messagebox.showinfo("Export",
                f"No records found for {d}" +
                (f"  [{subj}]" if subj != "All Subjects" else "") +
                "\nNothing to export.",
                parent=self.win)
            return

        # ── Deduplicate: one row per (roll_no, subject) ──────────────────────
        # If a student was marked by both QR and Face (edge case), keep both
        # rows but merge the method labels so the teacher sees the full picture.
        seen   = {}   # key: (roll_no, subject) → row index in merged list
        merged = []
        for roll_no, name, subject, status, method, att_date, time_ in db_rows:
            key = (roll_no, subject)
            if key in seen:
                # Already have a row — append the extra method to the cell
                idx = seen[key]
                existing_method = merged[idx][4]
                if method not in existing_method:
                    merged[idx] = list(merged[idx])
                    merged[idx][4] = f"{existing_method} + {method}"
                    merged[idx] = tuple(merged[idx])
            else:
                seen[key] = len(merged)
                merged.append((roll_no, name, subject, status, method, att_date, time_))

        # ── Build filename: subject_date.csv (safe filename chars only) ──────
        subj_slug = (subj if subj != "All Subjects" else "All_Subjects")
        subj_slug = "".join(c if c.isalnum() or c in "-_ " else "_"
                            for c in subj_slug).strip().replace(" ", "_")
        os.makedirs(EXPORT_DIR, exist_ok=True)
        fname = os.path.join(EXPORT_DIR, f"{subj_slug}_{d}.csv")

        # ── Write CSV with renamed 'Attendance Method' column ────────────────
        HEADER = ("Roll No", "Name", "Subject", "Status",
                "Attendance Method", "Date", "Time")
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(HEADER)
            w.writerows(merged)

        messagebox.showinfo("Export Successful",
            f"  CSV saved  ({len(merged)} record{'s' if len(merged)!=1 else ''}):\n\n"
            f"{fname}",
            parent=self.win)
        self._status_bar.config(text=f"Exported {len(merged)} rows → {fname}")

    # ─────────────────────────────────────────────
    # THEME — fixed: action buttons, stat cards, filter bar all update
    # ─────────────────────────────────────────────
    def _style_tree(self, t):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("Treeview",
                    background=t["tree_bg"], foreground=t["fg"],
                    rowheight=30, fieldbackground=t["tree_field"],
                    font=("Segoe UI", 9))
        s.configure("Treeview.Heading",
                    background=t["btn_reg"], foreground="white",
                    font=("Segoe UI", 9, "bold"), relief="flat")
        s.map("Treeview.Heading",
            background=[("active", t["btn_reg_h"])])
        s.map("Treeview",
            background=[("selected", t["accent"])])

    def _theme(self):
        toggle_theme()
        t = get_theme()

        # Window + top level frames
        self.win.configure(bg=t["bg"])
        self._tog.configure(bg=t["toggle_bg"], fg=t["toggle_fg"],
                            text=t["toggle_text"])
        self.hdr.configure(bg=t["header_bg"])
        self._wlbl.configure(bg=t["header_bg"], fg=t["warning"])
        self._ilbl.configure(bg=t["header_bg"], fg=t["sub_fg"])
        self._body.configure(bg=t["bg"])
        self._lcanvas.configure(bg=t["bg"])
        self._left.configure(bg=t["bg"])
        self._right.configure(bg=t["bg"])

        # Left panel labels
        self._slbl.configure(bg=t["bg"], fg=t["sub_fg"])
        self._act_lbl.configure(bg=t["bg"], fg=t["sub_fg"])
        self._stats_lbl.configure(bg=t["bg"], fg=t["sub_fg"])
        self._subj_grid.configure(bg=t["bg"])
        self._active_info_frame.configure(bg=t["header_bg"])
        self._active_info_lbl.configure(bg=t["header_bg"], fg=t["sub_fg"])

        # ── FIX: update action buttons with correct theme colours ──────────
        for b in self._act_btns:
            col = t[b._col_key]
            hov = t[b._hov_key]
            b.configure(bg=col, fg="white", activebackground=hov)

        # ── FIX: update stat cards ─────────────────────────────────────────
        self._stats_frame.configure(bg=t["bg"])
        for card in self._stat_cards:
            col = t[card._col_key]
            card.configure(bg=col)
            for child in card.winfo_children():
                child.configure(bg=col)

        # Right panel filter bar
        self._ff.configure(bg=t["bg"])
        self._dflbl.configure(bg=t["bg"], fg=t["sub_fg"])
        self._date_e.configure(bg=t["entry_bg"], fg=t["fg"],
                    insertbackground=t["fg"])
        self._search_btn.configure(bg=t["btn_reg"], fg="white",
                        activebackground=t["btn_reg_h"])
        self._today_btn.configure(bg=t["divider"], fg=t["fg"])
        self._row_count_lbl.configure(bg=t["bg"], fg=t["sub_fg"])
        self._report_lbl.configure(bg=t["bg"], fg=t["sub_fg"])
        self._status_bar.configure(bg=t["header_bg"], fg=t["sub_fg"])

        # Tree
        self._style_tree(t)
        self.tree.tag_configure(ROW_ODD,   background=t["tree_bg"])
        self.tree.tag_configure(ROW_EVEN,  background=t["tree_field"])
        self.tree.tag_configure("present", foreground=t["success"])
        self.tree.tag_configure("absent",  foreground=t["danger"])
        self.tree.tag_configure("face_row",foreground=t["accent"])

        # Banner
        self.banner.configure(bg=t["success"])
        self._blbl.configure(bg=t["success"])

    # ─────────────────────────────────────────────
    # CLASS MANAGEMENT
    # ─────────────────────────────────────────────
    def _start_class(self, subject):
        if self.active_subj:
            messagebox.showwarning("Class Active",
                f"'{self.active_subj}' already chalu hai.\n"
                "Pehle 'End Class' karo.", parent=self.win)
            return
        conn = cur = None
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                INSERT INTO active_classes(teacher_id,subject,start_time,active)
                VALUES(%s,%s,NOW(),1)
                ON DUPLICATE KEY UPDATE subject=%s, start_time=NOW(), active=1
            """, (self.teacher["id"], subject, subject))
            conn.commit()
        except Exception as ex:
            print("start_class:", ex)
        finally:
            if cur: cur.close()
            if conn: conn.close()

        self.active_subj = subject
        now_str = date.today().strftime("%d %b %Y")
        self._blbl.config(
            text=f"🟢  Active: {subject}   |   {self.teacher['name']}   |   {now_str}")
        self.banner.pack(fill="x", after=self.hdr)
        self._active_info_lbl.config(
            text=f"🟢 Active Class\n{subject}\nStarted: {now_str}\n\n"
                 "Press 'End Class' to stop.",
            fg=get_theme()["success"])
        messagebox.showinfo("Class Started",
            f"'{subject}' class is live now!\n\n"
            "Students can see it in the dashboard.\n"
            "Mark Attendance with QR Code or Facial Expression",
            parent=self.win)

    def _end_class(self):
        if not self.active_subj:
            return
        conn = cur = None
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute(
                "UPDATE active_classes SET active=0 "
                "WHERE teacher_id=%s AND subject=%s",
                (self.teacher["id"], self.active_subj))
            conn.commit()
        except Exception as ex:
            print("end_class:", ex)
        finally:
            if cur: cur.close()
            if conn: conn.close()
        self.banner.pack_forget()
        self._active_info_lbl.config(text="No active class",
                        fg=get_theme()["sub_fg"])
        messagebox.showinfo("Class Ended",
            f"'{self.active_subj}' The class was closed.", parent=self.win)
        self.active_subj = None
        self._load_report(); self._load_stats()

    # ─────────────────────────────────────────────
    # QR ATTENDANCE — runs in main thread (OpenCV window), dashboard hides
    # ─────────────────────────────────────────────
    def _qr_scan(self):
        if not self.active_subj:
            messagebox.showwarning("No Active Class",
                "First select the subject and start the class!",
                parent=self.win)
            return

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        if not cap.isOpened():
            messagebox.showerror("Webcam Error",
                "Webcam not found!\nPlease connect a webcam and try again.",
                parent=self.win)
            return

        self.win.withdraw()
        marked = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                for qr in decode(frame, symbols=[ZBarSymbol.QRCODE]):
                    data = qr.data.decode("utf-8")
                    roll_no = None
                    if data.startswith("STUDENT:"):
                        parts = data.split(":")
                        if len(parts) >= 2:
                            roll_no = parts[1].strip()
                    elif data.startswith("ROLL:"):
                        roll_no = data.replace("ROLL:", "").strip()
                    if not roll_no:
                        continue
                    if roll_no in marked:
                        label, clr = f"{roll_no}  Already Marked", (0, 165, 255)
                    else:
                        ok, name = self._save_attendance(roll_no, "QR")
                        if ok:
                            marked.append(roll_no)
                            label, clr = f"{name}  Present ✓", (0, 220, 100)
                        else:
                            label, clr = f"{roll_no}  Not Found/Duplicate", (0, 60, 220)
                    pts = [(p.x, p.y) for p in qr.polygon]
                    for j in range(len(pts)):
                        cv2.line(frame, pts[j], pts[(j+1) % len(pts)], clr, 3)
                    cv2.putText(frame, label,
                        (qr.rect.left, max(qr.rect.top - 12, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, clr, 2)

                # HUD
                cv2.rectangle(frame, (0, 0), (580, 50), (15, 23, 42), -1)
                cv2.putText(frame,
                    f"QR Attendance | Subject: {self.active_subj[:30]}  "
                    f"Marked: {len(marked)}  |  Press Q to Stop",
                    (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                cv2.imshow("QR Attendance — Press Q to stop", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

        self.win.deiconify()
        self.win.after(400, self._load_report)
        self.win.after(400, self._load_stats)
        messagebox.showinfo("QR Scan Complete",
            f"QR Attendance done!\n\n"
            f"Subject : {self.active_subj}\n"
            f"Total Marked : {len(marked)}",
            parent=self.win)

    # ─────────────────────────────────────────────
    # FACE ATTENDANCE — runs in background thread
    # ─────────────────────────────────────────────
    def _face_scan(self):
        if not self.active_subj:
            messagebox.showwarning("No Active Class",
                "First select the subject and start the class!\n"
                " Then run face attendance.",
                parent=self.win)
            return

        try:
            if FACE_MODULE_DIR not in sys.path:
                sys.path.insert(0, FACE_MODULE_DIR)
            if "face_recognition_module" in sys.modules:
                del sys.modules["face_recognition_module"]
            from face_recognition_module import FaceAttendanceSession
        except ImportError as e:
            messagebox.showerror("Module Not Found",
                f"Face recognition model not loaded:\n{e}\n\n"
                "✅ Checklist:\n"
                "1. File name must be  face_recognition_module.py\n"
                "2. File must be inside the  face_module/  folder\n"
                "3. face_module/ must contain __init__.py\n"
                "4. Run:  pip install opencv-contrib-python numpy",
                parent=self.win)
            return
        except Exception as e:
            messagebox.showerror("Import Error",
                f"Unexpected error loading face module:\n{e}",
                parent=self.win)
            return

        # Check model exists before starting
        model_path = os.path.join(FACE_MODULE_DIR, "trainer", "face_model.yml")
        if not os.path.exists(model_path):
            messagebox.showerror("Model Not Found",
                "Face recognition model not found!\n\n"
                "Get students to capture face data first\n"
                "(Registration → Capture Face Data button),\n"
                "Then run train_model.py.",
                parent=self.win)
            return

        self._status_bar.config(text="  Face Attendance starting….....")
        self.win.update_idletasks()

        def _run():
            session = FaceAttendanceSession(
                subject     = self.active_subj,
                teacher_id  = self.teacher["id"],
                dataset_dir = os.path.join(FACE_MODULE_DIR, "dataset"),
                trainer_dir = os.path.join(FACE_MODULE_DIR, "trainer"),
                on_mark_cb  = self._on_face_marked,
                on_done_cb  = self._on_face_done,
            )
            session.run()

        threading.Thread(target=_run, daemon=True).start()

    def _on_face_marked(self, roll_no, name):
        self.win.after(0, lambda: self._face_mark_ui(roll_no, name))

    def _face_mark_ui(self, roll_no, name):
        ok, sname = self._save_attendance(roll_no, "Face")
        msg = (f"✅ Face marked: {sname}" if ok
               else f"ℹ️ {name} already marked or not found")
        self._status_bar.config(text=msg)

    def _on_face_done(self, total_marked):
        self.win.after(0, lambda: self._face_done_ui(total_marked))

    def _face_done_ui(self, total_marked):
        self._load_report()
        self._load_stats()
        messagebox.showinfo("Face Attendance Done",
            f"Face Attendance complete!\n\n"
            f"Subject : {self.active_subj}\n"
            f"Total Marked : {total_marked}",
            parent=self.win)
        self._status_bar.config(text="Face Attendance session ended.")

    # ─────────────────────────────────────────────
    def _save_attendance(self, roll_no, method="QR"):
        conn = cur = None
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute(
                "SELECT id, name FROM students WHERE roll_no=%s", (roll_no,))
            row = cur.fetchone()
            if not row:
                return False, None
            sid, sname = row
            today = date.today()
            cur.execute("""
                SELECT id FROM attendance
                WHERE student_id=%s AND date=%s AND subject=%s
            """, (sid, today, self.active_subj))
            if cur.fetchone():
                return False, sname
            cur.execute("""
                INSERT INTO attendance
                (student_id, teacher_id, subject, date, status, method)
                VALUES(%s,%s,%s,%s,'Present',%s)
            """, (sid, self.teacher["id"], self.active_subj, today, method))
            conn.commit()
            return True, sname
        except Exception as ex:
            print("save_attendance:", ex)
            return False, None
        finally:
            if cur: cur.close()
            if conn: conn.close()

    # ─────────────────────────────────────────────
    def _refresh(self):
        self._status_bar.config(text=" Refreshing… ")
        self.win.update_idletasks()
        self._load_report()
        self._load_stats()
        self._status_bar.config(text="  Refreshed. ")

    # ─────────────────────────────────────────────
    def _load_report(self):
        for ch in self.tree.get_children():
            self.tree.delete(ch)

        d    = _normalise_date(self.v_date.get())
        subj = self.v_subj_filter.get()
        conn = cur = None
        try:
            conn = get_connection(); cur = conn.cursor()
            try:
                if subj == "All Subjects":
                    cur.execute("""
                        SELECT s.roll_no, s.name, a.subject,
                            a.status, a.method, a.date,
                            COALESCE(TIME_FORMAT(a.created_at,'%H:%i'), '—')
                        FROM attendance a
                        JOIN students s ON a.student_id = s.id
                        WHERE a.date = %s
                        ORDER BY s.roll_no
                    """, (d,))
                else:
                    cur.execute("""
                        SELECT s.roll_no, s.name, a.subject,
                            a.status, a.method, a.date,
                            COALESCE(TIME_FORMAT(a.created_at,'%H:%i'), '—')
                        FROM attendance a
                        JOIN students s ON a.student_id = s.id
                        WHERE a.date = %s AND a.subject = %s
                        ORDER BY s.roll_no
                    """, (d, subj))
            except Exception:
                if subj == "All Subjects":
                    cur.execute("""
                        SELECT s.roll_no, s.name, a.subject,
                            a.status, a.method, a.date, '—'
                        FROM attendance a
                        JOIN students s ON a.student_id = s.id
                        WHERE a.date = %s
                        ORDER BY s.roll_no
                    """, (d,))
                else:
                    cur.execute("""
                        SELECT s.roll_no, s.name, a.subject,
                            a.status, a.method, a.date, '—'
                        FROM attendance a
                        JOIN students s ON a.student_id = s.id
                        WHERE a.date = %s AND a.subject = %s
                        ORDER BY s.roll_no
                    """, (d, subj))

            rows = cur.fetchall()
            for idx, row in enumerate(rows):
                tag_row  = ROW_ODD if idx % 2 == 0 else ROW_EVEN
                tag_stat = "present" if row[3] == "Present" else "absent"
                tag_meth = "face_row" if row[4] == "Face" else ""
                tags = [tag_row, tag_stat]
                if tag_meth:
                    tags.append(tag_meth)
                self.tree.insert("", "end", values=row, tags=tags)

            count = len(rows)
            if not count:
                self.tree.insert("", "end",
                    values=("—", "no record", "—", "—", "—", d, "—"),
                    tags=(ROW_ODD,))
            self._row_count_var.set(
                f"{count} record{'s' if count != 1 else ''}")
            self._status_bar.config(
                text=f"Loaded {count} row(s) for {d}" +
                    (f"  [{subj}]" if subj != "All Subjects" else ""))

        except Exception as ex:
            print("load_report:", ex)
            self._status_bar.config(text=f" DB Error: {ex}")
            messagebox.showerror("Report Error",
                f"Could not load report:\n{ex}", parent=self.win)
        finally:
            if cur: cur.close()
            if conn: conn.close()

    def _load_stats(self):
        conn = cur = None
        try:
            conn = get_connection(); cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM attendance "
                "WHERE date=%s AND status='Present'", (date.today(),))
            self.v_today.set(str(cur.fetchone()[0]))
            cur.execute("SELECT COUNT(*) FROM students")
            self.v_total.set(str(cur.fetchone()[0]))
        except Exception as ex:
            print("load_stats:", ex)
        finally:
            if cur: cur.close()
            if conn: conn.close()


if __name__ == "__main__":
    TeacherDashboard({"id": 1, "name": "Test Teacher",
                    "subject": "Computer Networks", "email": "t@t.com"})