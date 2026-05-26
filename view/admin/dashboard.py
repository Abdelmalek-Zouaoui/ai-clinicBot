# view/admin/dashboard.py
"""
DashboardView — Clinic at-a-glance screen.
Style : Light / Professional  (white panels, blue accents, clean grid)

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  Top bar  :  greeting + date + quick-nav buttons        │
  ├──────────┬──────────┬──────────┬──────────┬────────────┤
  │  STAT    │  STAT    │  STAT    │  STAT    │            │  ← stat cards row
  ├──────────┴──────────┴──────────┴──────────┤  WAITING   │
  │                                           │  LIST      │  ← chart + waiting
  │         Monthly Revenue Chart             │            │
  │         (canvas — no external libs)       │            │
  └───────────────────────────────────────────┴────────────┘

Controller interface expected:
    controller.navigate(page_key: str)
    controller.refresh_dashboard_data()          # called by "Refresh" btn
    # Data pushed IN via:
    self.update_stat_cards(total, low, expiring, sales)
    self.update_waiting_list(appointments: list[dict])
    self.update_chart(data: dict)                # {day(int): revenue(float)}
"""

import customtkinter as ctk
import tkinter as tk
from datetime import date, datetime
import math
from view.sidebar import Sidebar

# ── Palette ───────────────────────────────────────────────────────────────────
BG             = "#F7F8FA"
PANEL_BG       = "#FFFFFF"
BORDER         = "#E2E6ED"
TEXT_PRIMARY   = "#1A202C"
TEXT_SECONDARY = "#64748B"
ACCENT         = "#2563EB"
ACCENT_LIGHT   = "#DBEAFE"
SUCCESS        = "#16A34A"
SUCCESS_LIGHT  = "#DCFCE7"
WARNING        = "#D97706"
WARNING_LIGHT  = "#FEF3C7"
DANGER         = "#DC2626"
DANGER_LIGHT   = "#FEE2E2"
PURPLE         = "#7C3AED"
PURPLE_LIGHT   = "#EDE9FE"
CHART_BAR      = "#3B82F6"
CHART_BAR_HOV  = "#2563EB"
CHART_GRID     = "#E2E8F0"
CHART_TEXT     = "#94A3B8"

FONT_FAMILY = "Helvetica"


# ─────────────────────────────────────────────────────────────────────────────
class DashboardView(ctk.CTkFrame):

    def __init__(self, parent, controller,
                 lang="en", role="admin", username="Admin"):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller = controller
        self.role       = role
        self.username   = username
        self.lang       = lang

        # State
        self._chart_data: dict = {}
        self._waiting:    list = []
        self._hover_bar:  int | None = None

        self._build()

    # ══════════════════════════════════════════════════════════════════════
    # BUILD
    # ══════════════════════════════════════════════════════════════════════

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)   # sidebar fixed
        self.grid_columnconfigure(1, weight=1)   # content expands

        # Sidebar
        self._sidebar = Sidebar(self, self.controller, active="dashboard")
        self._sidebar.grid(row=0, column=0, sticky="ns")

        # Content wrapper
        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(2, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_stat_cards()
        self._build_main_area()

    # ── Top bar ───────────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = ctk.CTkFrame(self._content, fg_color=PANEL_BG, height=68,
                           border_width=1, border_color=BORDER,
                           corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        # Greeting
        now   = datetime.now()
        hour  = now.hour
        greet = ("🌅 Good morning" if hour < 12
                 else "☀️ Good afternoon" if hour < 18
                 else "🌙 Good evening")
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w", padx=24, pady=12)

        ctk.CTkLabel(left,
                     text=f"{greet}, {self.username}",
                     font=ctk.CTkFont(FONT_FAMILY, 18, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(left,
                     text=now.strftime("%A, %d %B %Y"),
                     font=ctk.CTkFont(FONT_FAMILY, 12),
                     text_color=TEXT_SECONDARY).pack(anchor="w")

        # Refresh button only (nav is now in sidebar)
        ctk.CTkButton(
            bar, text="↻  Refresh", width=110, height=34,
            font=ctk.CTkFont(FONT_FAMILY, 12),
            fg_color=ACCENT, hover_color="#1D4ED8",
            text_color="white", corner_radius=8,
            command=self.controller.refresh_dashboard_data
        ).grid(row=0, column=2, padx=24, pady=17)

    # ── Stat cards ────────────────────────────────────────────────────────

    def _build_stat_cards(self):
        row = ctk.CTkFrame(self._content, fg_color=BG)
        row.grid(row=1, column=0, sticky="ew", padx=16, pady=(16, 0))
        for i in range(4):
            row.grid_columnconfigure(i, weight=1)

        cards_meta = [
            ("total",    "Total Patients",    "👤", ACCENT,   ACCENT_LIGHT),
            ("low",      "Waiting",           "⏳", WARNING,  WARNING_LIGHT),
            ("expiring", "Completed Today",   "✅", SUCCESS,  SUCCESS_LIGHT),
            ("sales",    "Today's Revenue",   "💰", PURPLE,   PURPLE_LIGHT),
        ]
        self._stat_labels: dict[str, ctk.CTkLabel] = {}

        for col, (key, title, icon, color, light) in enumerate(cards_meta):
            card = ctk.CTkFrame(row, fg_color=PANEL_BG,
                                border_width=1, border_color=BORDER,
                                corner_radius=12)
            card.grid(row=0, column=col, sticky="ew",
                      padx=(0 if col == 0 else 8, 0), pady=0)
            card.grid_columnconfigure(0, weight=1)

            # Coloured left stripe
            stripe = ctk.CTkFrame(card, fg_color=color,
                                  width=4, corner_radius=0)
            stripe.grid(row=0, column=0, rowspan=3,
                        sticky="ns", padx=(0, 12), pady=0)
            stripe.grid_propagate(False)

            # Icon bubble
            bubble = ctk.CTkFrame(card, fg_color=light,
                                  width=44, height=44, corner_radius=10)
            bubble.grid(row=0, column=1, padx=(0, 12),
                        pady=(18, 0), sticky="n")
            bubble.grid_propagate(False)
            ctk.CTkLabel(bubble, text=icon,
                         font=ctk.CTkFont(size=20)).place(
                relx=0.5, rely=0.5, anchor="center")

            # Value
            val_lbl = ctk.CTkLabel(card, text="—",
                                   font=ctk.CTkFont(FONT_FAMILY, 26, "bold"),
                                   text_color=color)
            val_lbl.grid(row=0, column=2, sticky="w",
                         padx=(0, 16), pady=(18, 0))
            self._stat_labels[key] = val_lbl

            # Title
            ctk.CTkLabel(card, text=title,
                         font=ctk.CTkFont(FONT_FAMILY, 11),
                         text_color=TEXT_SECONDARY).grid(
                row=1, column=2, sticky="w", padx=(0, 16), pady=(0, 16))

    # ── Main area  (chart left | waiting right) ───────────────────────────

    def _build_main_area(self):
        area = ctk.CTkFrame(self._content, fg_color=BG)
        area.grid(row=2, column=0, sticky="nsew",
                  padx=16, pady=16)
        area.grid_rowconfigure(0, weight=1)
        area.grid_columnconfigure(0, weight=62)
        area.grid_columnconfigure(1, weight=38)

        self._build_chart_panel(area)
        self._build_waiting_panel(area)

    # ── Revenue chart ─────────────────────────────────────────────────────

    def _build_chart_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=PANEL_BG,
                             border_width=1, border_color=BORDER,
                             corner_radius=12)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr,
                     text="📈  Monthly Revenue",
                     font=ctk.CTkFont(FONT_FAMILY, 14, "bold"),
                     text_color=TEXT_PRIMARY,
                     anchor="w").grid(row=0, column=0, sticky="w")

        month_name = date.today().strftime("%B %Y")
        ctk.CTkLabel(hdr, text=month_name,
                     font=ctk.CTkFont(FONT_FAMILY, 11),
                     text_color=TEXT_SECONDARY).grid(
            row=0, column=1, sticky="e")

        # Canvas for bar chart
        self._chart_canvas = tk.Canvas(
            panel, bg=PANEL_BG, highlightthickness=0)
        self._chart_canvas.grid(row=1, column=0, sticky="nsew",
                                padx=16, pady=(0, 16))
        self._chart_canvas.bind("<Configure>", self._on_chart_resize)
        self._chart_canvas.bind("<Motion>",    self._on_chart_hover)
        self._chart_canvas.bind("<Leave>",     self._on_chart_leave)

    def _draw_chart(self):
        c      = self._chart_canvas
        W      = c.winfo_width()
        H      = c.winfo_height()
        if W < 10 or H < 10:
            return

        c.delete("all")

        data   = self._chart_data          # {day: revenue}
        today  = date.today()
        import calendar
        n_days = calendar.monthrange(today.year, today.month)[1]
        days   = list(range(1, n_days + 1))

        PAD_L, PAD_R = 52, 16
        PAD_T, PAD_B = 16, 40
        chart_w = W - PAD_L - PAD_R
        chart_h = H - PAD_T - PAD_B

        max_val = max(data.values(), default=1) or 1
        # Round max up nicely
        magnitude = 10 ** math.floor(math.log10(max_val)) if max_val > 0 else 1
        max_val   = math.ceil(max_val / magnitude) * magnitude

        bar_w     = max(4, chart_w / n_days - 3)
        spacing   = chart_w / n_days

        # ── Grid lines & Y labels ────────────────────────────────────────
        n_grid = 4
        for i in range(n_grid + 1):
            y_val = max_val * i / n_grid
            y_px  = PAD_T + chart_h - (chart_h * i / n_grid)
            c.create_line(PAD_L, y_px, W - PAD_R, y_px,
                          fill=CHART_GRID, dash=(4, 4), width=1)
            label = (f"{int(y_val/1000)}k" if y_val >= 1000
                     else str(int(y_val)))
            c.create_text(PAD_L - 6, y_px,
                          text=label, anchor="e",
                          fill=CHART_TEXT,
                          font=(FONT_FAMILY, 9))

        # ── Bars ─────────────────────────────────────────────────────────
        self._bar_rects = {}   # day → (x0,y0,x1,y1)
        for day in days:
            rev   = data.get(day, 0)
            x_ctr = PAD_L + (day - 0.5) * spacing
            x0    = x_ctr - bar_w / 2
            x1    = x_ctr + bar_w / 2
            bar_h = (rev / max_val) * chart_h if max_val else 0
            y0    = PAD_T + chart_h - bar_h
            y1    = PAD_T + chart_h

            is_today  = (day == today.day)
            is_hover  = (day == self._hover_bar)
            fill = (CHART_BAR_HOV if is_hover
                    else ACCENT     if is_today
                    else CHART_BAR)

            if rev > 0:
                c.create_rectangle(x0, y0, x1, y1,
                                   fill=fill, outline="",
                                   tags=f"bar_{day}")
                # Top cap — small rounded effect
                cap_h = min(4, bar_h)
                c.create_rectangle(x0, y0, x1, y0 + cap_h,
                                   fill=fill, outline="")

            self._bar_rects[day] = (x0, PAD_T, x1, y1)

            # X-axis label every 5 days + today
            if day % 5 == 0 or is_today:
                c.create_text(x_ctr, PAD_T + chart_h + 14,
                              text=str(day), anchor="n",
                              fill=ACCENT if is_today else CHART_TEXT,
                              font=(FONT_FAMILY,
                                    9,
                                    "bold" if is_today else "normal"))

        # Axis lines
        c.create_line(PAD_L, PAD_T, PAD_L, PAD_T + chart_h,
                      fill=BORDER, width=1)
        c.create_line(PAD_L, PAD_T + chart_h,
                      W - PAD_R, PAD_T + chart_h,
                      fill=BORDER, width=1)

        # Tooltip (if hovered)
        if self._hover_bar and self._hover_bar in data:
            rev   = data[self._hover_bar]
            rects = self._bar_rects[self._hover_bar]
            tx    = (rects[0] + rects[2]) / 2
            ty    = rects[1] + 4
            tip   = f"Day {self._hover_bar}: {rev:,.0f} DA"
            # Bubble
            tw    = len(tip) * 6 + 12
            c.create_rectangle(tx - tw/2, ty, tx + tw/2, ty + 20,
                               fill=TEXT_PRIMARY, outline="")
            c.create_text(tx, ty + 10,
                          text=tip, fill="white",
                          font=(FONT_FAMILY, 9, "bold"))

    def _on_chart_resize(self, _event=None):
        self.after(20, self._draw_chart)

    def _on_chart_hover(self, event):
        for day, (x0, y0, x1, y1) in self._bar_rects.items():
            if x0 <= event.x <= x1:
                if self._hover_bar != day:
                    self._hover_bar = day
                    self._draw_chart()
                return
        if self._hover_bar is not None:
            self._hover_bar = None
            self._draw_chart()

    def _on_chart_leave(self, _event=None):
        if self._hover_bar is not None:
            self._hover_bar = None
            self._draw_chart()

    # ── Waiting list ──────────────────────────────────────────────────────

    def _build_waiting_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=PANEL_BG,
                             border_width=1, border_color=BORDER,
                             corner_radius=12)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr,
                     text="⏳  Waiting Room",
                     font=ctk.CTkFont(FONT_FAMILY, 14, "bold"),
                     text_color=TEXT_PRIMARY,
                     anchor="w").grid(row=0, column=0, sticky="w")

        self._waiting_count_lbl = ctk.CTkLabel(
            hdr, text="0 patients",
            font=ctk.CTkFont(FONT_FAMILY, 11),
            text_color=TEXT_SECONDARY)
        self._waiting_count_lbl.grid(row=0, column=1, sticky="e")

        # Divider
        div = ctk.CTkFrame(panel, fg_color=BORDER, height=1)
        div.grid(row=0, column=0, sticky="ew", padx=16, pady=(48, 0))

        # Scrollable list
        self._waiting_scroll = ctk.CTkScrollableFrame(
            panel, fg_color="transparent")
        self._waiting_scroll.grid(row=1, column=0, sticky="nsew",
                                  padx=0, pady=0)
        self._waiting_scroll.grid_columnconfigure(0, weight=1)

        # Go to appointments button
        ctk.CTkButton(
            panel, text="Open Appointments →",
            font=ctk.CTkFont(FONT_FAMILY, 12),
            fg_color=ACCENT_LIGHT, hover_color="#BFDBFE",
            text_color=ACCENT, corner_radius=8, height=34,
            command=lambda: self.controller.navigate("appointments")
        ).grid(row=2, column=0, sticky="ew",
               padx=16, pady=(8, 16))

    def _render_waiting_list(self):
        for w in self._waiting_scroll.winfo_children():
            w.destroy()

        patients = self._waiting
        n        = len(patients)
        self._waiting_count_lbl.configure(
            text=f"{n} patient{'s' if n != 1 else ''}")

        if not patients:
            empty = ctk.CTkFrame(self._waiting_scroll,
                                 fg_color="transparent")
            empty.grid(row=0, column=0, pady=40)
            ctk.CTkLabel(empty, text="🎉",
                         font=ctk.CTkFont(size=32)).pack()
            ctk.CTkLabel(empty, text="No patients waiting",
                         font=ctk.CTkFont(FONT_FAMILY, 13),
                         text_color=TEXT_SECONDARY).pack(pady=(4, 0))
            return

        for idx, appt in enumerate(patients):
            self._render_waiting_card(idx, appt)

    def _render_waiting_card(self, idx: int, appt: dict):
        card = ctk.CTkFrame(self._waiting_scroll,
                            fg_color="#F8FAFC",
                            border_width=1, border_color=BORDER,
                            corner_radius=10)
        card.grid(row=idx, column=0, sticky="ew",
                  padx=10, pady=4)
        card.grid_columnconfigure(1, weight=1)

        # Queue number circle
        num_bg = ctk.CTkFrame(card, fg_color=ACCENT_LIGHT,
                              width=36, height=36, corner_radius=18)
        num_bg.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10)
        num_bg.grid_propagate(False)
        ctk.CTkLabel(num_bg, text=str(idx + 1),
                     font=ctk.CTkFont(FONT_FAMILY, 13, "bold"),
                     text_color=ACCENT).place(relx=0.5, rely=0.5,
                                               anchor="center")

        # Name
        ctk.CTkLabel(card,
                     text=appt.get("patient_name", "—"),
                     font=ctk.CTkFont(FONT_FAMILY, 13, "bold"),
                     text_color=TEXT_PRIMARY,
                     anchor="w").grid(row=0, column=1,
                                       sticky="w", pady=(10, 0))

        # Visit type
        visit = appt.get("visit_type", "Consultation")
        complaint = appt.get("chief_complaint", "")
        sub = visit + (f"  —  {complaint}" if complaint else "")
        ctk.CTkLabel(card, text=sub,
                     font=ctk.CTkFont(FONT_FAMILY, 11),
                     text_color=TEXT_SECONDARY,
                     anchor="w").grid(row=1, column=1,
                                       sticky="w", pady=(0, 10))

        # Time
        raw = appt.get("appointment_date", "")
        time_str = raw[11:16] if len(raw) >= 16 else "—"
        ctk.CTkLabel(card, text=time_str,
                     font=ctk.CTkFont(FONT_FAMILY, 10),
                     text_color=TEXT_SECONDARY).grid(
            row=0, column=2, padx=(0, 12), pady=(10, 0))

        # "See" button
        ctk.CTkButton(
            card, text="→", width=28, height=28,
            font=ctk.CTkFont(FONT_FAMILY, 13, "bold"),
            fg_color=ACCENT, hover_color="#1D4ED8",
            text_color="white", corner_radius=6,
            command=lambda: self.controller.navigate("appointments")
        ).grid(row=1, column=2, padx=(0, 12), pady=(0, 10))

    # ══════════════════════════════════════════════════════════════════════
    # CONTROLLER INTERFACE  (called by main.py / controller)
    # ══════════════════════════════════════════════════════════════════════

    def update_stat_cards(self, total: str, low: str,
                          expiring: str, sales: str):
        """Push live data into the four stat cards."""
        self._stat_labels["total"].configure(text=total)
        self._stat_labels["low"].configure(text=low)
        self._stat_labels["expiring"].configure(text=expiring)
        self._stat_labels["sales"].configure(text=sales)

    def update_waiting_list(self, appointments: list[dict]):
        """Refresh the waiting-room panel."""
        self._waiting = appointments
        self._render_waiting_list()

    def update_chart(self, data: dict):
        """
        Accepts {day(int): revenue(float)} for the current month.
        Redraws the bar chart.
        """
        self._chart_data  = data or {}
        self._hover_bar   = None
        # Delay draw until canvas has been laid out
        self.after(50, self._draw_chart)

    def apply_lang(self, lang_code: str):
        """Language switch hook — extend if localisation is needed."""
        self.lang = lang_code