"""
view/admin/user_mgmt.py
-----------------------
Employee Account Management Page — Smart Pharmacy Management System.

Layout (split-screen):
  Left  (2/3) : Scrollable employee table with role badge, status, delete button
  Right (1/3) : "Create Account" form panel (username, full name, password,
                confirm password, role selector, phone, notes)

Pure UI layer — zero SQL, zero business logic.
All actions fire controller callbacks.
"""

import customtkinter as ctk
from tkinter import messagebox

# ─────────────────────────── Colour Tokens ────────────────────────────
BG_DARK      = "#242424"
BG_SIDEBAR   = "#1a1a2e"
BG_CARD      = "#2d2d2d"
BG_INPUT     = "#1e1e2e"
BG_ROW_ODD   = "#2a2a2a"
BG_ROW_EVEN  = "#323232"
BG_ROW_HOVER = "#3a3a3a"
BG_HEADER    = "#1a1a2e"
ACCENT_BLUE  = "#1f538d"
ACCENT_TEAL  = "#2fa572"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED   = "#ef4444"
ACCENT_PURPLE= "#7c3aed"
TEXT_LIGHT   = "#e2e8f0"
TEXT_MUTED   = "#94a3b8"
TEXT_HEADER  = "#7dd3fc"
BORDER_CLR   = "#374151"
BORDER_FOCUS = "#1f538d"

ROLE_COLORS = {
    "admin":      ACCENT_PURPLE,
    "pharmacist": ACCENT_BLUE,
    "cashier":    ACCENT_TEAL,
    "employee":   ACCENT_AMBER,
}
ROLE_ICONS = {
    "admin":      "👑",
    "pharmacist": "💊",
    "cashier":    "🧾",
    "employee":   "👤",
}

ROLES = ["pharmacist", "cashier", "employee"]   # selectable — admin is not creatable here


class UserMgmtView(ctk.CTkFrame):
    """
    Employee account management page.

    Public API
    ----------
    render(users: list[dict])        — Populate the employee table.
                                       Each dict must have keys:
                                       user_id, username, full_name, role, phone
    show_form_message(msg, success)  — Show feedback banner on the right panel.
    clear_form()                     — Reset all form fields to blank.
    get_form_data() -> dict          — Read current form values.

    Controller callbacks expected
    -----------------------------
    controller.navigate(key)
    controller.on_create_employee(data: dict)
    controller.on_delete_employee(user_id: int, username: str)
    """

    def __init__(self, parent, controller=None):
        super().__init__(parent, fg_color=BG_DARK, corner_radius=0)
        self.controller = controller

        self.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()

    # ══════════════════════════ HEADER ════════════════════════════════

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=BG_SIDEBAR, height=64, corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        # Back button
        ctk.CTkButton(
            hdr, text="←  Back", width=90, height=36, corner_radius=8,
            fg_color="transparent", hover_color=ACCENT_BLUE,
            text_color=TEXT_MUTED, font=ctk.CTkFont("Helvetica", 13),
            command=lambda: self.controller and self.controller.navigate("dashboard")
        ).grid(row=0, column=0, padx=(16, 0), pady=14)

        # Title
        title_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        title_frame.grid(row=0, column=1, padx=20, pady=8, sticky="w")

        ctk.CTkLabel(
            title_frame, text="👥  Employee Accounts",
            font=ctk.CTkFont("Helvetica", 20, "bold"), text_color=TEXT_LIGHT
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            title_frame, text="Manage staff logins · Create · Delete",
            font=ctk.CTkFont("Helvetica", 11), text_color=TEXT_MUTED
        ).grid(row=1, column=0, sticky="w")

    # ══════════════════════════ BODY ══════════════════════════════════

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=3)   # table takes 2/3
        body.grid_columnconfigure(1, weight=0)   # divider
        body.grid_columnconfigure(2, weight=2)   # form takes 1/3

        self._build_table_panel(body)

        # Vertical divider
        ctk.CTkFrame(body, width=1, fg_color=BORDER_CLR).grid(
            row=0, column=1, sticky="ns", padx=10)

        self._build_form_panel(body)

    # ──────────────────────── LEFT: Employee Table ────────────────────

    def _build_table_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=16,
                             border_width=1, border_color=BORDER_CLR)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Panel title bar
        title_bar = ctk.CTkFrame(panel, fg_color="transparent")
        title_bar.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="ew")
        title_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            title_bar, text="🧑‍💼  Staff Roster",
            font=ctk.CTkFont("Helvetica", 15, "bold"), text_color=TEXT_LIGHT
        ).grid(row=0, column=0, sticky="w")

        self._count_badge = ctk.CTkLabel(
            title_bar, text="0 employees",
            font=ctk.CTkFont("Helvetica", 11), text_color=TEXT_MUTED
        )
        self._count_badge.grid(row=0, column=2, sticky="e")

        # Column headers
        cols = [
            ("#",          4,  TEXT_MUTED),
            ("Username",  20,  TEXT_HEADER),
            ("Full Name", 24,  TEXT_HEADER),
            ("Role",      14,  TEXT_HEADER),
            ("Phone",     16,  TEXT_MUTED),
            ("Actions",   12,  TEXT_MUTED),
        ]
        header_row = ctk.CTkFrame(panel, fg_color=BG_HEADER, corner_radius=8)
        header_row.grid(row=1, column=0, padx=10, pady=(0, 4), sticky="ew")
        for i, (lbl, w, clr) in enumerate(cols):
            header_row.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                header_row, text=lbl,
                font=ctk.CTkFont("Helvetica", 11, "bold"),
                text_color=clr
            ).grid(row=0, column=i, padx=8, pady=8, sticky="w")

        # Scrollable rows area
        self._rows_frame = ctk.CTkScrollableFrame(
            panel, fg_color="transparent",
            scrollbar_button_color=BORDER_CLR,
            scrollbar_button_hover_color=ACCENT_BLUE
        )
        self._rows_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self._rows_frame.grid_columnconfigure(0, weight=1)

        # Empty state placeholder
        self._empty_label = ctk.CTkLabel(
            self._rows_frame,
            text="👤  No employee accounts yet.\nCreate one using the form →",
            font=ctk.CTkFont("Helvetica", 13), text_color=TEXT_MUTED,
            justify="center"
        )
        self._empty_label.grid(row=0, column=0, pady=60)

    def _add_table_row(self, idx: int, user: dict):
        """Render one employee row into the scrollable frame."""
        bg = BG_ROW_ODD if idx % 2 == 0 else BG_ROW_EVEN
        row = ctk.CTkFrame(self._rows_frame, fg_color=bg, corner_radius=8, height=44)
        row.grid(row=idx, column=0, padx=2, pady=2, sticky="ew")
        row.grid_propagate(False)

        weights = [4, 20, 24, 14, 16, 12]
        for i, w in enumerate(weights):
            row.grid_columnconfigure(i, weight=w)

        # Hover effect
        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=BG_ROW_HOVER))
        row.bind("<Leave>", lambda e, r=row, b=bg: r.configure(fg_color=b))

        uid       = user.get("user_id", "")
        username  = user.get("username", "")
        full_name = user.get("full_name") or "—"
        role      = user.get("role", "employee").lower()
        phone     = user.get("phone") or "—"

        role_color = ROLE_COLORS.get(role, ACCENT_AMBER)
        role_icon  = ROLE_ICONS.get(role, "👤")

        def lbl(parent, text, color=TEXT_LIGHT, bold=False, col=0):
            w = ctk.CTkLabel(
                parent, text=text,
                font=ctk.CTkFont("Helvetica", 12, "bold" if bold else "normal"),
                text_color=color, anchor="w"
            )
            w.grid(row=0, column=col, padx=8, pady=0, sticky="w")
            return w

        lbl(row, f"{idx + 1}",        TEXT_MUTED,   col=0)
        lbl(row, f"🔑 {username}",    TEXT_LIGHT,   bold=True, col=1)
        lbl(row, full_name,            TEXT_MUTED,   col=2)

        # Role badge
        # Role badge background — map each role to a valid dark tint
        role_bg_map = {
            "admin":      "#2a1a4a",
            "pharmacist": "#1a2a4a",
            "cashier":    "#1a3a2e",
            "employee":   "#3a2e1a",
        }
        badge_bg = role_bg_map.get(role, "#2a2a2a")
        badge_frame = ctk.CTkFrame(row, fg_color=badge_bg,
                                   corner_radius=6, height=26)
        badge_frame.grid(row=0, column=3, padx=8, pady=9, sticky="w")
        ctk.CTkLabel(
            badge_frame, text=f" {role_icon} {role.capitalize()} ",
            font=ctk.CTkFont("Helvetica", 11, "bold"),
            text_color=role_color
        ).pack(padx=2)

        lbl(row, phone, TEXT_MUTED, col=4)

        # Delete button — never shown for admin accounts
        if role != "admin":
            del_btn = ctk.CTkButton(
                row, text="🗑", width=32, height=28, corner_radius=6,
                fg_color="transparent", hover_color="#3a1a1a",
                text_color=ACCENT_RED, font=ctk.CTkFont("Helvetica", 14),
                command=lambda u=uid, n=username: self._on_delete(u, n)
            )
            del_btn.grid(row=0, column=5, padx=8, pady=8)

    def _on_delete(self, user_id, username):
        ok = messagebox.askyesno(
            "Confirm Delete",
            f"Permanently delete employee account:\n\n  @{username}\n\nThis cannot be undone.",
            icon="warning"
        )
        if ok and self.controller:
            self.controller.on_delete_employee(user_id, username)

    # ──────────────────────── RIGHT: Create Account Form ─────────────

    def _build_form_panel(self, parent):
        # Outer card — holds the fixed title bar + the scrollable content below
        panel = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=16,
                             border_width=1, border_color=BORDER_CLR)
        panel.grid(row=0, column=2, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)   # row 1 = scrollable area expands

        # ── Fixed title bar (never scrolls away) ──────────────────
        title_bar = ctk.CTkFrame(panel, fg_color="transparent")
        title_bar.grid(row=0, column=0, sticky="ew")
        title_bar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_bar, text="➕  Create Employee Account",
            font=ctk.CTkFont("Helvetica", 14, "bold"), text_color=TEXT_LIGHT
        ).grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")
        ctk.CTkLabel(
            title_bar, text="Fill in the details below to register a new staff login.",
            font=ctk.CTkFont("Helvetica", 10), text_color=TEXT_MUTED,
            wraplength=280, justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 6), sticky="w")
        ctk.CTkFrame(title_bar, height=1, fg_color=BORDER_CLR).grid(
            row=2, column=0, sticky="ew", padx=16, pady=(0, 0))

        # ── Scrollable content (fields + buttons) ─────────────────
        # All widgets go inside `sf` so even on small screens the
        # "Create Account" button is always reachable by scrolling.
        sf = ctk.CTkScrollableFrame(
            panel, fg_color="transparent",
            scrollbar_button_color=BORDER_CLR,
            scrollbar_button_hover_color=ACCENT_BLUE,
        )
        sf.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        sf.grid_columnconfigure(0, weight=1)

        # Feedback banner (hidden until needed)
        self._form_msg = ctk.CTkLabel(
            sf, text="", height=32, corner_radius=8,
            font=ctk.CTkFont("Helvetica", 11),
            text_color=ACCENT_TEAL, fg_color="transparent"
        )
        self._form_msg.grid(row=0, column=0, padx=16, pady=(10, 4), sticky="ew")

        # ── Form fields ──────────────────────────────────────────────
        self._fields: dict = {}
        field_row = 1

        def section(text, row):
            ctk.CTkLabel(
                sf, text=text,
                font=ctk.CTkFont("Helvetica", 10, "bold"),
                text_color=TEXT_MUTED
            ).grid(row=row, column=0, padx=20, pady=(12, 2), sticky="w")

        def entry(key, placeholder, row, show=""):
            e = ctk.CTkEntry(
                sf, placeholder_text=placeholder,
                fg_color=BG_INPUT, border_color=BORDER_CLR,
                border_width=1, corner_radius=8,
                text_color=TEXT_LIGHT, placeholder_text_color=TEXT_MUTED,
                height=38, show=show
            )
            e.grid(row=row, column=0, padx=16, pady=(0, 4), sticky="ew")
            e.bind("<FocusIn>",  lambda ev, w=e: w.configure(border_color=BORDER_FOCUS))
            e.bind("<FocusOut>", lambda ev, w=e: w.configure(border_color=BORDER_CLR))
            self._fields[key] = e
            return e

        # ── Account credentials ───────────────────────────────────
        section("ACCOUNT CREDENTIALS", field_row); field_row += 1
        entry("username",         "Username  (e.g. john_doe)",       field_row); field_row += 1
        entry("password",         "Password  (min. 6 characters)",   field_row, show="•"); field_row += 1
        entry("confirm_password", "Confirm password",                 field_row, show="•"); field_row += 1

        # ── Personal info ──────────────────────────────────────────
        section("PERSONAL INFORMATION", field_row); field_row += 1
        entry("full_name", "Full name  (e.g. Jean Dupont)",          field_row); field_row += 1
        entry("phone",     "Phone  (optional)",                       field_row); field_row += 1

        # ── Role selector ──────────────────────────────────────────
        section("ROLE", field_row); field_row += 1

        role_menu = ctk.CTkOptionMenu(
            sf,
            values=["pharmacist", "cashier", "employee"],
            fg_color=BG_INPUT,
            button_color=ACCENT_BLUE,
            button_hover_color="#2563ab",
            dropdown_fg_color=BG_CARD,
            dropdown_hover_color=ACCENT_BLUE,
            text_color=TEXT_LIGHT,
            dropdown_text_color=TEXT_LIGHT,
            font=ctk.CTkFont("Helvetica", 12),
            height=38,
        )
        role_menu.set("pharmacist")
        role_menu.grid(row=field_row, column=0, padx=16, pady=(0, 4), sticky="ew")
        self._fields["role"] = role_menu
        field_row += 1

        self._role_hint = ctk.CTkLabel(
            sf, text=self._role_hint_text("pharmacist"),
            font=ctk.CTkFont("Helvetica", 10), text_color=TEXT_MUTED,
            wraplength=280, justify="left"
        )
        self._role_hint.grid(row=field_row, column=0, padx=20, pady=(0, 8), sticky="w")
        field_row += 1
        role_menu.configure(command=self._on_role_change)

        # ── Notes ─────────────────────────────────────────────────
        section("NOTES  (optional)", field_row); field_row += 1
        notes_box = ctk.CTkTextbox(
            sf, height=72,
            fg_color=BG_INPUT, border_color=BORDER_CLR,
            border_width=1, corner_radius=8,
            text_color=TEXT_LIGHT, font=ctk.CTkFont("Helvetica", 12),
        )
        notes_box.grid(row=field_row, column=0, padx=16, pady=(0, 8), sticky="ew")
        notes_box.bind("<FocusIn>",  lambda e: notes_box.configure(border_color=BORDER_FOCUS))
        notes_box.bind("<FocusOut>", lambda e: notes_box.configure(border_color=BORDER_CLR))
        self._notes_box = notes_box
        field_row += 1

        ctk.CTkFrame(sf, height=1, fg_color=BORDER_CLR).grid(
            row=field_row, column=0, sticky="ew", padx=16, pady=(4, 12))
        field_row += 1

        # ── Action buttons — always the last rows in the scroll area ──
        btn_frame = ctk.CTkFrame(sf, fg_color="transparent")
        btn_frame.grid(row=field_row, column=0, padx=16, pady=(0, 24), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_frame, text="↺  Clear",
            height=44, corner_radius=10,
            fg_color=BG_INPUT, hover_color=BORDER_CLR,
            text_color=TEXT_MUTED, font=ctk.CTkFont("Helvetica", 13),
            command=self.clear_form
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_frame, text="✔  Create Account",
            height=44, corner_radius=10,
            fg_color=ACCENT_TEAL, hover_color="#26a066",
            text_color="white", font=ctk.CTkFont("Helvetica", 13, "bold"),
            command=self._on_create_click
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _role_hint_text(self, role: str) -> str:
        hints = {
            "pharmacist": "💊 Full access to medicine stock and dispensing.",
            "cashier":    "🧾 Sales and checkout only. No stock editing.",
            "employee":   "👤 Basic access — view only by default.",
        }
        return hints.get(role, "")

    def _on_role_change(self, value: str):
        self._role_hint.configure(text=self._role_hint_text(value))

    def _on_create_click(self):
        if self.controller:
            self.controller.on_create_employee(self.get_form_data())

    # ══════════════════════════ PUBLIC API ════════════════════════════

    def render(self, users: list):
        """Populate the employee table. Clears existing rows first."""
        for w in self._rows_frame.winfo_children():
            w.destroy()

        # Filter out admin accounts from the display — admins are managed elsewhere
        visible = [u for u in users if u.get("role", "").lower() != "admin"]

        count = len(visible)
        self._count_badge.configure(text=f"{count} employee{'s' if count != 1 else ''}")

        if not visible:
            self._empty_label = ctk.CTkLabel(
                self._rows_frame,
                text="👤  No employee accounts yet.\nCreate one using the form →",
                font=ctk.CTkFont("Helvetica", 13), text_color=TEXT_MUTED,
                justify="center"
            )
            self._empty_label.grid(row=0, column=0, pady=60)
            return

        for idx, user in enumerate(visible):
            self._add_table_row(idx, user)

    def show_form_message(self, msg: str, success: bool = True):
        """Display a feedback message in the form panel."""
        text_color = ACCENT_TEAL  if success else ACCENT_RED
        bg_color   = "#1a3a2e"    if success else "#3a1a1a"   # dark teal / dark red — valid 6-digit hex
        icon       = "✔  "        if success else "✘  "
        self._form_msg.configure(
            text=f"{icon}{msg}",
            text_color=text_color,
            fg_color=bg_color,
        )
        # Auto-clear after 4 seconds
        self.after(4000, lambda: self._form_msg.configure(
            text="", fg_color="transparent"))

    def clear_form(self):
        """Reset all form fields to their default empty state."""
        for key, widget in self._fields.items():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
            elif isinstance(widget, ctk.CTkOptionMenu):
                widget.set("pharmacist")
                self._role_hint.configure(text=self._role_hint_text("pharmacist"))
        self._notes_box.delete("1.0", "end")
        self._form_msg.configure(text="", fg_color="transparent")

    def get_form_data(self) -> dict:
        """Return the current form values as a dictionary."""
        return {
            "username":         self._fields["username"].get().strip(),
            "password":         self._fields["password"].get(),
            "confirm_password": self._fields["confirm_password"].get(),
            "full_name":        self._fields["full_name"].get().strip(),
            "phone":            self._fields["phone"].get().strip(),
            "role":             self._fields["role"].get(),
            "notes":            self._notes_box.get("1.0", "end").strip(),
        }