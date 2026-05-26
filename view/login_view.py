# view/auth_view.py
"""
LoginView — Clinic Management System authentication screen.
Style : Light / Professional

Layout:
  Full window split into two halves:
  LEFT  45% : Brand panel  (clinic identity, decorative medical cross)
  RIGHT 55% : Login card   (username, password, submit, version tag)

Controller interface expected:
    controller.on_login()
    controller.get_app_name() -> str
    controller.get_all_identity_settings() -> dict
        keys: app_name, app_subtitle, app_address, app_phone

View methods called by controller:
    get_credentials() -> (username, password)
    show_error(message: str)
"""

import customtkinter as ctk
import tkinter as tk
from datetime import date

# ── Palette ───────────────────────────────────────────────────────────────────
BG           = "#F7F8FA"
PANEL_BG     = "#FFFFFF"
BRAND_BG     = "#1E3A5F"          # deep navy  — brand side
BRAND_ACCENT = "#3B82F6"          # vivid blue — highlights on brand side
BRAND_LIGHT  = "#DBEAFE"
BORDER       = "#E2E6ED"
TEXT_PRIMARY   = "#1A202C"
TEXT_SECONDARY = "#64748B"
TEXT_LIGHT     = "#CBD5E1"
ACCENT       = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
DANGER       = "#DC2626"
SUCCESS      = "#16A34A"

FONT = "Helvetica"


# ─────────────────────────────────────────────────────────────────────────────
class LoginView(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller = controller

        # Fetch clinic identity
        try:
            identity = controller.get_all_identity_settings()
        except Exception:
            identity = {}
        self._clinic_name     = identity.get("app_name",     "CLINIC MANAGER")
        self._clinic_subtitle = identity.get("app_subtitle", "Medical Clinic — Algeria")
        self._clinic_address  = identity.get("app_address",  "")
        self._clinic_phone    = identity.get("app_phone",    "")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=45)
        self.grid_columnconfigure(1, weight=55)

        self._build_brand_panel()
        self._build_login_panel()

        # Bind Enter key
        parent.bind("<Return>", lambda e: self.controller.on_login())

    # ══════════════════════════════════════════════════════════════════════
    # LEFT — Brand / hero panel
    # ══════════════════════════════════════════════════════════════════════

    def _build_brand_panel(self):
        panel = ctk.CTkFrame(self, fg_color=BRAND_BG, corner_radius=0)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        # ── Medical cross decoration ──────────────────────────────────────
        cross_canvas = tk.Canvas(
            inner, width=120, height=120,
            bg=BRAND_BG, highlightthickness=0)
        cross_canvas.pack(pady=(0, 24))
        self._draw_cross(cross_canvas, 120, 120)

        # ── Clinic name ───────────────────────────────────────────────────
        ctk.CTkLabel(inner,
                     text=self._clinic_name.upper(),
                     font=ctk.CTkFont(FONT, 28, "bold"),
                     text_color="#FFFFFF"
                     ).pack()

        ctk.CTkLabel(inner,
                     text=self._clinic_subtitle,
                     font=ctk.CTkFont(FONT, 13),
                     text_color=TEXT_LIGHT
                     ).pack(pady=(4, 0))

        # Divider
        ctk.CTkFrame(inner, fg_color=BRAND_ACCENT,
                     height=2, width=60).pack(pady=20)

        # Address / phone
        if self._clinic_address:
            ctk.CTkLabel(inner,
                         text=f"📍  {self._clinic_address}",
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_LIGHT
                         ).pack(pady=2)
        if self._clinic_phone:
            ctk.CTkLabel(inner,
                         text=f"📞  {self._clinic_phone}",
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_LIGHT
                         ).pack(pady=2)

        # ── Feature pills ─────────────────────────────────────────────────
        pills_data = [
            ("👤", "Patients"),
            ("📅", "Appointments"),
            ("📋", "Prescriptions"),
            ("💰", "Billing"),
        ]
        pills = ctk.CTkFrame(inner, fg_color="transparent")
        pills.pack(pady=(24, 0))
        for i, (icon, label) in enumerate(pills_data):
            pill = ctk.CTkFrame(pills, fg_color="#243B55",
                                corner_radius=20)
            pill.grid(row=i // 2, column=i % 2,
                      padx=6, pady=4)
            ctk.CTkLabel(pill,
                         text=f"{icon}  {label}",
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_LIGHT
                         ).pack(padx=16, pady=6)

        # ── Year tag ─────────────────────────────────────────────────────
        ctk.CTkLabel(panel,
                     text=f"© {date.today().year}  Clinic Management System",
                     font=ctk.CTkFont(FONT, 10),
                     text_color="#475569"
                     ).place(relx=0.5, rely=0.97, anchor="s")

    @staticmethod
    def _draw_cross(canvas, w, h):
        """Draw a stylised medical cross with a glow ring."""
        cx, cy = w // 2, h // 2
        arm_w, arm_h = 20, 52

        # Outer glow ring
        r = 52
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                           outline=BRAND_ACCENT, width=2)
        # Inner ring fill
        canvas.create_oval(cx - r + 4, cy - r + 4,
                           cx + r - 4, cy + r - 4,
                           fill="#243B55", outline="")

        # Cross arms
        # Vertical
        canvas.create_rectangle(
            cx - arm_w // 2, cy - arm_h // 2,
            cx + arm_w // 2, cy + arm_h // 2,
            fill=BRAND_ACCENT, outline="")
        # Horizontal
        canvas.create_rectangle(
            cx - arm_h // 2, cy - arm_w // 2,
            cx + arm_h // 2, cy + arm_w // 2,
            fill=BRAND_ACCENT, outline="")
        # Highlight dot in centre
        canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5,
                           fill="#FFFFFF", outline="")

    # ══════════════════════════════════════════════════════════════════════
    # RIGHT — Login card
    # ══════════════════════════════════════════════════════════════════════

    def _build_login_panel(self):
        panel = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Centred card
        card = ctk.CTkFrame(panel, fg_color=PANEL_BG,
                            border_width=1, border_color=BORDER,
                            corner_radius=16,
                            width=380)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_columnconfigure(0, weight=1)

        # ── Card header ───────────────────────────────────────────────────
        ctk.CTkLabel(card,
                     text="🏥",
                     font=ctk.CTkFont(size=40)
                     ).grid(row=0, column=0, pady=(36, 4))

        ctk.CTkLabel(card,
                     text="Welcome back",
                     font=ctk.CTkFont(FONT, 22, "bold"),
                     text_color=TEXT_PRIMARY
                     ).grid(row=1, column=0, pady=(0, 4))

        ctk.CTkLabel(card,
                     text="Sign in to continue to your clinic dashboard",
                     font=ctk.CTkFont(FONT, 12),
                     text_color=TEXT_SECONDARY
                     ).grid(row=2, column=0, pady=(0, 24))

        # ── Form ──────────────────────────────────────────────────────────
        form = ctk.CTkFrame(card, fg_color="transparent")
        form.grid(row=3, column=0, sticky="ew", padx=36)
        form.grid_columnconfigure(0, weight=1)

        # Username
        ctk.CTkLabel(form, text="Username",
                     font=ctk.CTkFont(FONT, 12, "bold"),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")

        self._username_var = ctk.StringVar()
        self._user_entry = ctk.CTkEntry(
            form, textvariable=self._username_var,
            placeholder_text="Enter your username",
            font=ctk.CTkFont(FONT, 13),
            fg_color="#F8FAFC",
            border_width=1, border_color=BORDER,
            text_color=TEXT_PRIMARY,
            height=42, corner_radius=8)
        self._user_entry.grid(row=1, column=0, sticky="ew",
                               pady=(4, 14))

        # Password
        ctk.CTkLabel(form, text="Password",
                     font=ctk.CTkFont(FONT, 12, "bold"),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=2, column=0, sticky="w")

        self._password_var = ctk.StringVar()
        self._pass_entry = ctk.CTkEntry(
            form, textvariable=self._password_var,
            placeholder_text="Enter your password",
            show="•",
            font=ctk.CTkFont(FONT, 13),
            fg_color="#F8FAFC",
            border_width=1, border_color=BORDER,
            text_color=TEXT_PRIMARY,
            height=42, corner_radius=8)
        self._pass_entry.grid(row=3, column=0, sticky="ew",
                               pady=(4, 6))

        # Show/hide password toggle
        self._show_pass = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form, text="Show password",
            variable=self._show_pass,
            font=ctk.CTkFont(FONT, 11),
            text_color=TEXT_SECONDARY,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            checkmark_color="white",
            corner_radius=4,
            command=self._toggle_password
        ).grid(row=4, column=0, sticky="w", pady=(0, 16))

        # Error message label
        self._error_lbl = ctk.CTkLabel(
            form, text="",
            font=ctk.CTkFont(FONT, 12, "bold"),
            text_color=DANGER, anchor="w")
        self._error_lbl.grid(row=5, column=0, sticky="w",
                              pady=(0, 8))

        # Sign In button
        self._login_btn = ctk.CTkButton(
            form,
            text="Sign In  →",
            font=ctk.CTkFont(FONT, 14, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="white",
            height=46, corner_radius=10,
            command=self._on_login_click
        )
        self._login_btn.grid(row=6, column=0, sticky="ew",
                              pady=(0, 0))

        # ── Hint ──────────────────────────────────────────────────────────
        hint = ctk.CTkFrame(card, fg_color="#F8FAFC",
                            border_width=1, border_color=BORDER,
                            corner_radius=8)
        hint.grid(row=4, column=0, sticky="ew",
                  padx=36, pady=(16, 0))
        ctk.CTkLabel(hint,
                     text="Default credentials:  admin  /  admin123",
                     font=ctk.CTkFont(FONT, 11),
                     text_color=TEXT_SECONDARY
                     ).pack(padx=12, pady=8)

        # ── Version / footer ──────────────────────────────────────────────
        ctk.CTkLabel(card,
                     text="Clinic Manager  •  v1.0",
                     font=ctk.CTkFont(FONT, 10),
                     text_color="#CBD5E1"
                     ).grid(row=5, column=0, pady=(12, 24))

        # Focus username on open
        self.after(100, self._user_entry.focus)

    # ══════════════════════════════════════════════════════════════════════
    # INTERNAL HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _toggle_password(self):
        self._pass_entry.configure(
            show="" if self._show_pass.get() else "•")

    def _on_login_click(self):
        # Brief visual feedback
        self._login_btn.configure(text="Signing in…", state="disabled")
        self.after(300, self._restore_btn)
        self.controller.on_login()

    def _restore_btn(self):
        self._login_btn.configure(text="Sign In  →", state="normal")

    # ══════════════════════════════════════════════════════════════════════
    # CONTROLLER INTERFACE
    # ══════════════════════════════════════════════════════════════════════

    def get_credentials(self) -> tuple[str, str]:
        return (
            self._username_var.get().strip(),
            self._password_var.get(),
        )

    def show_error(self, message: str):
        self._error_lbl.configure(text=f"⚠  {message}")
        # Shake the card border colour red briefly
        self._pass_entry.configure(border_color=DANGER)
        self.after(1800, lambda: self._pass_entry.configure(
            border_color=BORDER))
        # Auto-clear error after 4 s
        self.after(4000, lambda: self._error_lbl.configure(text=""))