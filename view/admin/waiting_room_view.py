# view/admin/waiting_room_view.py
"""
WaitingRoomView — Live waiting room display
Shows all patients currently waiting (status = 'Waiting').
Auto-refreshes every 30 seconds.
"""

import customtkinter as ctk
from datetime import datetime
from view.sidebar import Sidebar, Toast

BG           = "#F7F8FA"
PANEL_BG     = "#FFFFFF"
PANEL_ALT    = "#F1F5F9"
BORDER       = "#E2E6ED"
TEXT_PRIMARY   = "#1A202C"
TEXT_SECONDARY = "#64748B"
ACCENT         = "#2563EB"
ACCENT_LIGHT   = "#DBEAFE"
ACCENT_HOVER   = "#1D4ED8"
SUCCESS        = "#16A34A"
SUCCESS_LIGHT  = "#DCFCE7"
WARNING        = "#D97706"
WARNING_LIGHT  = "#FEF3C7"
DANGER         = "#DC2626"
DANGER_LIGHT   = "#FEE2E2"
TEAL           = "#0D9488"
TEAL_LIGHT     = "#CCFBF1"
TEAL_DARK      = "#0F766E"

FONT = "Helvetica"


class WaitingRoomView(ctk.CTkFrame):

    REFRESH_MS = 30_000   # auto-refresh every 30 s

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller    = controller
        self._refresh_job  = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(self, controller, active="waiting_room")
        self._sidebar.grid(row=0, column=0, sticky="ns")

        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_body()
        self._load()
        self._schedule_refresh()

    def _load(self):
        try:
            rows = self.controller.db.fetch_all(
                """SELECT a.appointment_id, p.full_name,
                          a.appointment_date, a.visit_type,
                          a.chief_complaint, a.patient_id
                   FROM appointments a
                   JOIN patients p ON a.patient_id = p.patient_id
                   WHERE DATE(a.appointment_date) = DATE('now')
                     AND a.status = 'Waiting'
                   ORDER BY a.appointment_date ASC"""
            ) or []
        except Exception:
            rows = []
        keys = ["appointment_id","patient_name","appointment_date",
                "visit_type","chief_complaint","patient_id"]
        waiting = [dict(zip(keys,r)) for r in rows]
        self._render(waiting)

    def _schedule_refresh(self):
        self._refresh_job = self.after(self.REFRESH_MS, self._auto_refresh)

    def _auto_refresh(self):
        self._load()
        self._schedule_refresh()

    def destroy(self):
        if self._refresh_job:
            try: self.after_cancel(self._refresh_job)
            except Exception: pass
        super().destroy()

    # ── Top bar ───────────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = ctk.CTkFrame(self._content, fg_color=TEAL, height=64,
                           corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="🟢  Waiting Room",
                     font=ctk.CTkFont(FONT,22,"bold"),
                     text_color="#FFFFFF"
                     ).grid(row=0, column=0, padx=24, sticky="w")

        self._clock_lbl = ctk.CTkLabel(bar,
                                        text="",
                                        font=ctk.CTkFont(FONT,13),
                                        text_color="#A7F3D0")
        self._clock_lbl.grid(row=0, column=1, padx=8, sticky="w")
        self._tick_clock()

        acts = ctk.CTkFrame(bar, fg_color="transparent")
        acts.grid(row=0, column=2, padx=24, pady=14)

        ctk.CTkButton(acts, text="📅  Appointments", width=150, height=36,
                      font=ctk.CTkFont(FONT,12,"bold"),
                      fg_color=TEAL_DARK, hover_color="#134E4A",
                      corner_radius=8,
                      command=lambda: self.controller.navigate("appointments")
                      ).pack(side="left", padx=(0,6))

        ctk.CTkButton(acts, text="↻  Refresh", width=100, height=36,
                      font=ctk.CTkFont(FONT,12),
                      fg_color=TEAL_DARK, hover_color="#134E4A",
                      corner_radius=8, command=self._load
                      ).pack(side="left")

    def _tick_clock(self):
        now = datetime.now().strftime("%H:%M:%S  —  %A, %d %B %Y")
        self._clock_lbl.configure(text=now)
        self.after(1000, self._tick_clock)

    # ── Body ──────────────────────────────────────────────────────────────

    def _build_body(self):
        self._body = ctk.CTkFrame(self._content, fg_color=BG)
        self._body.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self._body.grid_rowconfigure(1, weight=1)
        self._body.grid_columnconfigure(0, weight=1)

        # Stats bar
        self._stats_bar = ctk.CTkFrame(self._body, fg_color=PANEL_BG,
                                        height=60, border_width=1,
                                        border_color=BORDER, corner_radius=0)
        self._stats_bar.grid(row=0, column=0, sticky="ew")
        self._stats_bar.grid_propagate(False)
        self._stats_bar.grid_columnconfigure(0, weight=1)
        self._stats_bar.grid_columnconfigure(1, weight=1)
        self._stats_bar.grid_columnconfigure(2, weight=1)

        self._stat_waiting = self._make_stat(self._stats_bar, 0, "Waiting", "0", TEAL)
        self._stat_progress = self._make_stat(self._stats_bar, 1, "In Progress", "0", ACCENT)
        self._stat_done = self._make_stat(self._stats_bar, 2, "Completed Today", "0", SUCCESS)

        # Scrollable cards
        self._cards_scroll = ctk.CTkScrollableFrame(
            self._body, fg_color=BG)
        self._cards_scroll.grid(row=1, column=0, sticky="nsew",
                                 padx=24, pady=16)
        self._cards_scroll.grid_columnconfigure(0, weight=1)
        self._cards_scroll.grid_columnconfigure(1, weight=1)
        self._cards_scroll.grid_columnconfigure(2, weight=1)

    def _make_stat(self, parent, col, label, value, color):
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.grid(row=0, column=col, sticky="nsew",
                padx=1, pady=1)
        fr.grid_columnconfigure(0, weight=1)
        val_lbl = ctk.CTkLabel(fr, text=value,
                                font=ctk.CTkFont(FONT,22,"bold"),
                                text_color=color)
        val_lbl.pack(pady=(8,0))
        ctk.CTkLabel(fr, text=label,
                     font=ctk.CTkFont(FONT,10),
                     text_color=TEXT_SECONDARY).pack(pady=(0,6))
        return val_lbl

    def _render(self, waiting: list):
        for w in self._cards_scroll.winfo_children():
            w.destroy()

        # Update stats
        try:
            stats = self.controller.db.fetch_all(
                """SELECT status, COUNT(*) FROM appointments
                   WHERE DATE(appointment_date) = DATE('now')
                   GROUP BY status"""
            ) or []
            s = {r[0]:r[1] for r in stats}
            self._stat_waiting.configure(text=str(s.get("Waiting",0)))
            self._stat_progress.configure(text=str(s.get("In Progress",0)))
            self._stat_done.configure(text=str(s.get("Completed",0)))
        except Exception:
            pass

        if not waiting:
            self._render_empty()
            return

        # Render cards in a 3-column grid
        for pos, appt in enumerate(waiting):
            row_pos = pos // 3
            col_pos = pos % 3
            self._render_patient_card(appt, pos+1, row_pos, col_pos)

    def _render_empty(self):
        empty = ctk.CTkFrame(self._cards_scroll, fg_color="transparent")
        empty.grid(row=0, column=0, columnspan=3, pady=80)
        ctk.CTkLabel(empty, text="🎉",
                     font=ctk.CTkFont(size=60)).pack()
        ctk.CTkLabel(empty, text="No patients waiting right now",
                     font=ctk.CTkFont(FONT,18,"bold"),
                     text_color=TEXT_PRIMARY).pack(pady=(12,4))
        ctk.CTkLabel(empty,
                     text="When a patient arrives and is marked 🟢 Arrived\nin the Appointments page, they will appear here.",
                     font=ctk.CTkFont(FONT,13),
                     text_color=TEXT_SECONDARY,
                     justify="center").pack()

    def _render_patient_card(self, appt: dict, position: int,
                              grid_row: int, grid_col: int):
        card = ctk.CTkFrame(self._cards_scroll,
                            fg_color=PANEL_BG,
                            border_width=2, border_color=TEAL,
                            corner_radius=16)
        card.grid(row=grid_row, column=grid_col,
                  sticky="nsew", padx=8, pady=8)
        card.grid_columnconfigure(0, weight=1)

        # Position number + teal header
        top_bar = ctk.CTkFrame(card, fg_color=TEAL,
                                corner_radius=0, height=52)
        top_bar.grid(row=0, column=0, sticky="ew")
        top_bar.grid_propagate(False)
        top_bar.grid_columnconfigure(1, weight=1)

        # Queue number circle
        num_circle = ctk.CTkFrame(top_bar, fg_color="#FFFFFF",
                                   width=36, height=36, corner_radius=18)
        num_circle.grid(row=0, column=0, padx=12, pady=8)
        num_circle.grid_propagate(False)
        ctk.CTkLabel(num_circle, text=str(position),
                     font=ctk.CTkFont(FONT,16,"bold"),
                     text_color=TEAL
                     ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(top_bar, text="WAITING",
                     font=ctk.CTkFont(FONT,11,"bold"),
                     text_color=TEAL_LIGHT, anchor="w"
                     ).grid(row=0, column=1, sticky="w", padx=(0,12))

        # Wait time
        dt = appt.get("appointment_date","")
        wait_str = self._calc_wait_time(dt)
        ctk.CTkLabel(top_bar, text=wait_str,
                     font=ctk.CTkFont(FONT,10),
                     text_color=TEAL_LIGHT, anchor="e"
                     ).grid(row=0, column=2, sticky="e", padx=12)

        # Patient info
        ctk.CTkLabel(card,
                     text=appt.get("patient_name","—"),
                     font=ctk.CTkFont(FONT,17,"bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=1, column=0, sticky="w",
                            padx=16, pady=(14,2))

        appt_time = dt[11:16] if len(dt) >= 16 else "—"
        ctk.CTkLabel(card,
                     text=f"🕐 Appt: {appt_time}  ·  {appt.get('visit_type','—')}",
                     font=ctk.CTkFont(FONT,12),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=2, column=0, sticky="w",
                            padx=16, pady=(0,4))

        if appt.get("chief_complaint"):
            ctk.CTkLabel(card,
                         text=f"💬 {appt['chief_complaint'][:40]}",
                         font=ctk.CTkFont(FONT,11),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=3, column=0, sticky="w",
                                padx=16, pady=(0,8))

        # Action buttons
        btn_fr = ctk.CTkFrame(card, fg_color="transparent")
        btn_fr.grid(row=4, column=0, sticky="ew",
                    padx=12, pady=(4,14))
        btn_fr.grid_columnconfigure(0, weight=1)
        btn_fr.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_fr, text="▶  Start Visit",
                      font=ctk.CTkFont(FONT,12,"bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      height=38, corner_radius=8,
                      command=lambda a=appt: self._start_visit(a)
                      ).grid(row=0, column=0, sticky="ew", padx=(0,4))

        ctk.CTkButton(btn_fr, text="👻 No Show",
                      font=ctk.CTkFont(FONT,12),
                      fg_color=PANEL_ALT, hover_color=WARNING_LIGHT,
                      text_color=WARNING,
                      height=38, corner_radius=8,
                      command=lambda a=appt: self._no_show(a)
                      ).grid(row=0, column=1, sticky="ew", padx=(4,0))

    @staticmethod
    def _calc_wait_time(dt_str: str) -> str:
        """Show how long the patient has been waiting."""
        try:
            appt_dt = datetime.strptime(dt_str[:16], "%Y-%m-%d %H:%M")
            diff    = datetime.now() - appt_dt
            mins    = int(diff.total_seconds() / 60)
            if mins < 0:
                return "Upcoming"
            if mins < 60:
                return f"⏱ {mins} min"
            h = mins // 60
            m = mins % 60
            return f"⏱ {h}h {m}m"
        except Exception:
            return ""

    def _start_visit(self, appt: dict):
        try:
            self.controller.on_update_appointment_status(
                appt["appointment_id"], "In Progress", "", "")
        except Exception:
            pass
        Toast.show(self._content,
                   f"▶ Starting visit for {appt.get('patient_name','')}",
                   kind="info")
        self._load()

    def _no_show(self, appt: dict):
        try:
            self.controller.on_update_appointment_status(
                appt["appointment_id"], "No Show", "", "")
        except Exception:
            pass
        self._load()