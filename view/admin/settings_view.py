# view/admin/settings_view.py
"""
SettingsView — Clinic identity, backup management, app preferences.
Style : Light / Professional

Layout (tabbed):
  Tab 1 — Clinic Identity  (name, subtitle, address, phone)
  Tab 2 — Backup           (stats, backup list, actions)
  Tab 3 — About            (version, credits)

Controller interface expected:
    on_save_app_identity(data: dict)
    get_all_identity_settings() -> dict
    on_manual_backup_here()
    on_manual_backup_choose()
    on_delete_old_backups()
    get_backup_stats() -> dict
    get_backup_list() -> list
    navigate(page_key: str)

View methods called by controller:
    set_identity_fields(data: dict)
    show_identity_message(msg, success)
    show_backup_message(msg, success)
    refresh(stats: dict, backup_list: list)
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from view.sidebar import Sidebar, Toast

# ── Palette ───────────────────────────────────────────────────────────────────
BG             = "#F7F8FA"
PANEL_BG       = "#FFFFFF"
PANEL_ALT      = "#F1F5F9"
BORDER         = "#E2E6ED"
TEXT_PRIMARY   = "#1A202C"
TEXT_SECONDARY = "#64748B"
ACCENT         = "#2563EB"
ACCENT_LIGHT   = "#DBEAFE"
ACCENT_HOVER   = "#1D4ED8"
SUCCESS        = "#16A34A"
SUCCESS_LIGHT  = "#DCFCE7"
DANGER         = "#DC2626"
DANGER_LIGHT   = "#FEE2E2"
WARNING        = "#D97706"
WARNING_LIGHT  = "#FEF3C7"

FONT = "Helvetica"


# ─────────────────────────────────────────────────────────────────────────────
class SettingsView(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller = controller
        self._identity_vars: dict = {}
        self._backup_list_widgets: list = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self._sidebar = Sidebar(self, controller, active="settings")
        self._sidebar.grid(row=0, column=0, sticky="ns")

        # Content wrapper
        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_tabs()

    # ══════════════════════════════════════════════════════════════════════
    # TOP BAR
    # ══════════════════════════════════════════════════════════════════════

    def _build_topbar(self):
        bar = ctk.CTkFrame(self._content, fg_color=PANEL_BG, height=64,
                           border_width=1, border_color=BORDER,
                           corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="⚙️  Settings",
                     font=ctk.CTkFont(FONT, 20, "bold"),
                     text_color=TEXT_PRIMARY
                     ).grid(row=0, column=0, padx=24, sticky="w")

    # ══════════════════════════════════════════════════════════════════════
    # TABS
    # ══════════════════════════════════════════════════════════════════════

    def _build_tabs(self):
        self._tabview = ctk.CTkTabview(
            self._content,
            fg_color=PANEL_BG,
            border_width=1, border_color=BORDER,
            segmented_button_fg_color="#F1F5F9",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT_HOVER,
            segmented_button_unselected_color="#F1F5F9",
            segmented_button_unselected_hover_color=ACCENT_LIGHT,
            text_color=TEXT_SECONDARY,
            text_color_disabled=TEXT_SECONDARY,
        )
        self._tabview.grid(row=1, column=0, sticky="nsew",
                           padx=16, pady=16)

        self._tabview.add("🏥  Clinic Identity")
        self._tabview.add("💾  Backup")
        self._tabview.add("ℹ️  About")

        self._build_identity_tab(
            self._tabview.tab("🏥  Clinic Identity"))
        self._build_backup_tab(
            self._tabview.tab("💾  Backup"))
        self._build_about_tab(
            self._tabview.tab("ℹ️  About"))

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1 — Clinic Identity
    # ══════════════════════════════════════════════════════════════════════

    def _build_identity_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        # Centred card
        card = ctk.CTkFrame(tab, fg_color=PANEL_BG,
                            border_width=1, border_color=BORDER,
                            corner_radius=12)
        card.grid(row=0, column=0, sticky="nsew", padx=60, pady=20)
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)

        # Section header
        hdr = ctk.CTkFrame(card, fg_color=ACCENT_LIGHT,
                           corner_radius=0, height=44)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr,
                     text="🏥  Clinic Information",
                     font=ctk.CTkFont(FONT, 14, "bold"),
                     text_color=ACCENT, anchor="w"
                     ).pack(side="left", padx=20, pady=10)

        def field(row, col, label, key, placeholder="", colspan=1):
            fr = ctk.CTkFrame(card, fg_color="transparent")
            fr.grid(row=row, column=col, columnspan=colspan,
                    sticky="ew", padx=20, pady=(10, 0))
            fr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(fr, text=label,
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            var = ctk.StringVar()
            ctk.CTkEntry(fr, textvariable=var,
                         placeholder_text=placeholder,
                         font=ctk.CTkFont(FONT, 13),
                         fg_color="#F8FAFC",
                         border_width=1, border_color=BORDER,
                         text_color=TEXT_PRIMARY, height=38
                         ).grid(row=1, column=0, sticky="ew",
                                pady=(4, 0))
            self._identity_vars[key] = var

        field(1, 0, "Clinic Name *", "app_name",
              "e.g. CABINET DR. AHMED", colspan=2)
        field(2, 0, "Subtitle / Speciality", "app_subtitle",
              "e.g. General Practice — Algeria", colspan=2)
        field(3, 0, "Address", "app_address",
              "Street, City, Wilaya")
        field(3, 1, "Phone", "app_phone", "+213 …")

        # Feedback
        self._identity_msg = ctk.CTkLabel(
            card, text="",
            font=ctk.CTkFont(FONT, 12),
            text_color=SUCCESS, anchor="w")
        self._identity_msg.grid(row=4, column=0, columnspan=2,
                                padx=20, pady=(12, 0), sticky="w")

        # Save button
        ctk.CTkButton(
            card, text="💾  Save Changes",
            font=ctk.CTkFont(FONT, 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            height=42, corner_radius=8,
            command=self._save_identity
        ).grid(row=5, column=0, columnspan=2,
               sticky="ew", padx=20, pady=(8, 24))

        # Pre-fill from controller
        try:
            self.set_identity_fields(
                self.controller.get_all_identity_settings())
        except Exception:
            pass

    def _save_identity(self):
        data = {k: v.get().strip()
                for k, v in self._identity_vars.items()}
        self.controller.on_save_app_identity(data)

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — Backup
    # ══════════════════════════════════════════════════════════════════════

    def _build_backup_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # ── Stats row ────────────────────────────────────────────────────
        stats_row = ctk.CTkFrame(tab, fg_color="transparent")
        stats_row.grid(row=0, column=0, columnspan=2,
                       sticky="ew", pady=(8, 16))
        for i in range(3):
            stats_row.grid_columnconfigure(i, weight=1)

        self._stat_cards = {}
        stats_meta = [
            ("total",   "Total Backups",    "💾", ACCENT,   ACCENT_LIGHT),
            ("auto",    "Auto Backups",     "🔄", SUCCESS,  SUCCESS_LIGHT),
            ("last",    "Last Backup",      "🕐", WARNING,  WARNING_LIGHT),
        ]
        for col, (key, title, icon, color, light) in enumerate(stats_meta):
            card = ctk.CTkFrame(stats_row, fg_color=PANEL_BG,
                                border_width=1, border_color=BORDER,
                                corner_radius=10)
            card.grid(row=0, column=col, sticky="ew",
                      padx=(0 if col == 0 else 8, 0))
            card.grid_columnconfigure(1, weight=1)

            bubble = ctk.CTkFrame(card, fg_color=light,
                                  width=40, height=40, corner_radius=10)
            bubble.grid(row=0, column=0, rowspan=2, padx=(14, 10),
                        pady=14)
            bubble.grid_propagate(False)
            ctk.CTkLabel(bubble, text=icon,
                         font=ctk.CTkFont(size=18)
                         ).place(relx=0.5, rely=0.5, anchor="center")

            val_lbl = ctk.CTkLabel(card, text="—",
                                   font=ctk.CTkFont(FONT, 20, "bold"),
                                   text_color=color)
            val_lbl.grid(row=0, column=1, sticky="w",
                         padx=(0, 14), pady=(14, 0))
            self._stat_cards[key] = val_lbl

            ctk.CTkLabel(card, text=title,
                         font=ctk.CTkFont(FONT, 10),
                         text_color=TEXT_SECONDARY
                         ).grid(row=1, column=1, sticky="w",
                                padx=(0, 14), pady=(0, 14))

        # ── Action buttons ────────────────────────────────────────────────
        act_panel = ctk.CTkFrame(tab, fg_color=PANEL_BG,
                                 border_width=1, border_color=BORDER,
                                 corner_radius=12)
        act_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        act_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(act_panel, text="Backup Actions",
                     font=ctk.CTkFont(FONT, 13, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, padx=16,
                            pady=(16, 12), sticky="w")

        actions = [
            ("💾  Backup Here",
             "Save to default backup folder",
             ACCENT, ACCENT_HOVER,
             self.controller.on_manual_backup_here),
            ("📁  Backup to Folder…",
             "Choose a custom destination",
             SUCCESS, "#15803D",
             self.controller.on_manual_backup_choose),
            ("🗑  Delete Old Backups",
             "Remove backups older than 30 days",
             DANGER, "#B91C1C",
             self.controller.on_delete_old_backups),
        ]

        for i, (label, desc, color, hover, cmd) in enumerate(actions):
            fr = ctk.CTkFrame(act_panel, fg_color="#F8FAFC",
                              border_width=1, border_color=BORDER,
                              corner_radius=8)
            fr.grid(row=i + 1, column=0, sticky="ew",
                    padx=14, pady=4)
            fr.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(fr, text=desc,
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, padx=12,
                                pady=(8, 0), sticky="w")
            ctk.CTkButton(
                fr, text=label,
                font=ctk.CTkFont(FONT, 12, "bold"),
                fg_color=color, hover_color=hover,
                height=36, corner_radius=8,
                command=cmd
            ).grid(row=1, column=0, sticky="ew",
                   padx=12, pady=(4, 10))

        # Feedback
        self._backup_msg = ctk.CTkLabel(
            act_panel, text="",
            font=ctk.CTkFont(FONT, 11),
            text_color=SUCCESS, anchor="w")
        self._backup_msg.grid(row=len(actions) + 1, column=0,
                              padx=16, pady=(4, 16), sticky="w")

        # ── Backup list ───────────────────────────────────────────────────
        list_panel = ctk.CTkFrame(tab, fg_color=PANEL_BG,
                                  border_width=1, border_color=BORDER,
                                  corner_radius=12)
        list_panel.grid(row=1, column=1, sticky="nsew")
        list_panel.grid_rowconfigure(1, weight=1)
        list_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(list_panel, text="Recent Backups",
                     font=ctk.CTkFont(FONT, 13, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, padx=16,
                            pady=(16, 8), sticky="w")

        self._backup_scroll = ctk.CTkScrollableFrame(
            list_panel, fg_color="transparent")
        self._backup_scroll.grid(row=1, column=0, sticky="nsew",
                                  padx=0, pady=(0, 12))
        self._backup_scroll.grid_columnconfigure(0, weight=1)

    def _render_backup_list(self, backup_list: list):
        for w in self._backup_scroll.winfo_children():
            w.destroy()

        if not backup_list:
            ctk.CTkLabel(self._backup_scroll,
                         text="No backups found.",
                         font=ctk.CTkFont(FONT, 12),
                         text_color=TEXT_SECONDARY
                         ).grid(row=0, column=0, pady=24)
            return

        for i, bk in enumerate(backup_list[:20]):
            name = (bk.get("filename") or bk.get("name", "")
                    if isinstance(bk, dict) else str(bk))
            size = (bk.get("size", "") if isinstance(bk, dict) else "")

            row = ctk.CTkFrame(self._backup_scroll,
                               fg_color="#F8FAFC",
                               border_width=1, border_color=BORDER,
                               corner_radius=8)
            row.grid(row=i, column=0, sticky="ew",
                     padx=10, pady=3)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(row,
                         text=f"💾  {name}",
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_PRIMARY, anchor="w"
                         ).grid(row=0, column=0, padx=12,
                                pady=(8, 0), sticky="w")
            if size:
                ctk.CTkLabel(row,
                             text=str(size),
                             font=ctk.CTkFont(FONT, 10),
                             text_color=TEXT_SECONDARY, anchor="w"
                             ).grid(row=1, column=0, padx=12,
                                    pady=(0, 8), sticky="w")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3 — About
    # ══════════════════════════════════════════════════════════════════════

    def _build_about_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(tab, fg_color=PANEL_BG,
                            border_width=1, border_color=BORDER,
                            corner_radius=12)
        card.grid(row=0, column=0, sticky="nsew", padx=100, pady=30)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="🏥",
                     font=ctk.CTkFont(size=52)
                     ).grid(row=0, column=0, pady=(36, 8))

        ctk.CTkLabel(card, text="Clinic Manager",
                     font=ctk.CTkFont(FONT, 24, "bold"),
                     text_color=TEXT_PRIMARY
                     ).grid(row=1, column=0)

        ctk.CTkLabel(card, text="Version 1.0  •  Medical Clinic — Algeria",
                     font=ctk.CTkFont(FONT, 12),
                     text_color=TEXT_SECONDARY
                     ).grid(row=2, column=0, pady=(4, 0))

        ctk.CTkFrame(card, fg_color=BORDER,
                     height=1).grid(row=3, column=0,
                                    sticky="ew", padx=40, pady=20)

        info_items = [
            ("Database",   "SQLite  (local, encrypted backup)"),
            ("Framework",  "CustomTkinter  +  Python 3.11+"),
            ("PDF Engine", "ReportLab"),
            ("Year",       str(date.today().year)),
        ]
        for i, (label, val) in enumerate(info_items):
            row_f = ctk.CTkFrame(card, fg_color="transparent")
            row_f.grid(row=4 + i, column=0, sticky="ew",
                       padx=40, pady=3)
            row_f.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row_f, text=label,
                         font=ctk.CTkFont(FONT, 12, "bold"),
                         text_color=TEXT_SECONDARY,
                         width=110, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row_f, text=val,
                         font=ctk.CTkFont(FONT, 12),
                         text_color=TEXT_PRIMARY, anchor="w"
                         ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(card,
                     text="Built for Algerian medical clinics.",
                     font=ctk.CTkFont(FONT, 11),
                     text_color=TEXT_SECONDARY
                     ).grid(row=4 + len(info_items), column=0,
                            pady=(20, 36))

    # ══════════════════════════════════════════════════════════════════════
    # CONTROLLER INTERFACE
    # ══════════════════════════════════════════════════════════════════════

    def set_identity_fields(self, data: dict):
        for key, var in self._identity_vars.items():
            var.set(data.get(key, ""))

    def show_identity_message(self, message: str, success: bool = True):
        color = SUCCESS if success else DANGER
        self._identity_msg.configure(text=message, text_color=color)

    def show_backup_message(self, message: str, success: bool = True):
        color = SUCCESS if success else DANGER
        self._backup_msg.configure(text=message, text_color=color)

    def refresh(self, stats: dict, backup_list: list):
        """Called by controller after backup operations."""
        total = stats.get("total", 0)
        auto  = stats.get("auto",  0)
        last  = stats.get("last_backup", "—") or "—"
        if isinstance(last, str) and len(last) > 16:
            last = last[:16]

        if "total" in self._stat_cards:
            self._stat_cards["total"].configure(text=str(total))
        if "auto" in self._stat_cards:
            self._stat_cards["auto"].configure(text=str(auto))
        if "last" in self._stat_cards:
            self._stat_cards["last"].configure(text=str(last))

        self._render_backup_list(backup_list or [])


# ─────────────────────────────────────────────────────────────────────────────
# UserFormWindow — Add / Edit user popup
# ─────────────────────────────────────────────────────────────────────────────

class UserFormWindow(ctk.CTkToplevel):

    ROLES = ["admin", "employee", "doctor", "nurse", "receptionist"]

    def __init__(self, parent_view, controller,
                 prefill: dict = None, on_saved=None):
        super().__init__()
        self.parent_view = parent_view
        self.controller  = controller
        self.prefill     = prefill or {}
        self.on_saved    = on_saved
        self._edit_mode  = bool(prefill)
        self._form_vars  = {}

        ROLE_COLORS = {
            "admin":        (ACCENT_LIGHT,    ACCENT),
            "doctor":       (SUCCESS_LIGHT,   SUCCESS),
            "nurse":        ("#FCE7F3",        "#BE185D"),
            "receptionist": (WARNING_LIGHT,   WARNING),
            "employee":     ("#F3F4F6",        TEXT_SECONDARY),
        }

        title = "Edit Account" if self._edit_mode else "Add Staff Account"
        self.title(f"👥  {title}")
        self.geometry("540x560")
        self.resizable(True, True)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        # Header
        hdr_bg = WARNING_LIGHT if self._edit_mode else ACCENT_LIGHT
        hdr_fg = WARNING       if self._edit_mode else ACCENT
        icon   = "✏️" if self._edit_mode else "➕"
        title  = "Edit Account" if self._edit_mode else "Add Staff Account"

        hdr = ctk.CTkFrame(scroll, fg_color=hdr_bg, corner_radius=10)
        hdr.grid(row=0, column=0, columnspan=2,
                 sticky="ew", padx=20, pady=(20, 14))
        ctk.CTkLabel(hdr, text=f"{icon}  {title}",
                     font=ctk.CTkFont(FONT, 16, "bold"),
                     text_color=hdr_fg
                     ).pack(anchor="w", padx=20, pady=12)

        def entry(row, col, label, key,
                  placeholder="", show="", colspan=1):
            fr = ctk.CTkFrame(scroll, fg_color="transparent")
            fr.grid(row=row, column=col, columnspan=colspan,
                    sticky="ew", padx=(20, 10), pady=5)
            fr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(fr, text=label,
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            var = ctk.StringVar(value=self.prefill.get(key, ""))
            ctk.CTkEntry(fr, textvariable=var,
                         placeholder_text=placeholder,
                         show=show,
                         font=ctk.CTkFont(FONT, 12),
                         fg_color=PANEL_ALT,
                         border_width=1, border_color=BORDER,
                         text_color=TEXT_PRIMARY, height=36
                         ).grid(row=1, column=0, sticky="ew")
            self._form_vars[key] = var

        def option(row, col, label, key, values, colspan=1):
            fr = ctk.CTkFrame(scroll, fg_color="transparent")
            fr.grid(row=row, column=col, columnspan=colspan,
                    sticky="ew", padx=(20, 10), pady=5)
            fr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(fr, text=label,
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            cur = self.prefill.get(key, values[0])
            if cur not in values:
                cur = values[0]
            var = ctk.StringVar(value=cur)
            ctk.CTkOptionMenu(fr, variable=var, values=values,
                              font=ctk.CTkFont(FONT, 12),
                              fg_color=PANEL_ALT,
                              button_color=ACCENT,
                              button_hover_color=ACCENT_HOVER,
                              dropdown_fg_color=PANEL_BG,
                              text_color=TEXT_PRIMARY, height=36
                              ).grid(row=1, column=0, sticky="ew")
            self._form_vars[key] = var

        entry(1, 0, "Username *", "username", "min. 3 characters", colspan=2)
        entry(2, 0, "Full Name",  "full_name", "Dr. Ahmed Benali")
        entry(2, 1, "Phone",      "phone",     "+213 …")

        if not self._edit_mode:
            entry(3, 0, "Password *",        "password",
                  "min. 6 characters", show="•")
            entry(3, 1, "Confirm Password *", "confirm_password",
                  "repeat password",   show="•")

        option(4, 0, "Role", "role", self.ROLES, colspan=2)

        # Feedback
        self._msg_lbl = ctk.CTkLabel(
            scroll, text="",
            font=ctk.CTkFont(FONT, 12),
            text_color=DANGER, anchor="w")
        self._msg_lbl.grid(row=5, column=0, columnspan=2,
                           padx=20, pady=(4, 0), sticky="w")

        # Buttons
        br = ctk.CTkFrame(scroll, fg_color="transparent")
        br.grid(row=6, column=0, columnspan=2,
                sticky="ew", padx=20, pady=(8, 24))
        br.grid_columnconfigure(0, weight=1)
        br.grid_columnconfigure(1, weight=1)

        save_lbl = "Save Changes" if self._edit_mode else "Create Account"
        ctk.CTkButton(br, text=save_lbl,
                      font=ctk.CTkFont(FONT, 13, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      height=42, corner_radius=8,
                      command=self._submit
                      ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(br, text="Cancel",
                      font=ctk.CTkFont(FONT, 13),
                      fg_color=PANEL_ALT, hover_color=BORDER,
                      text_color=TEXT_PRIMARY,
                      height=42, corner_radius=8,
                      command=self.destroy
                      ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        if self._edit_mode:
            ctk.CTkButton(br, text="🗑  Delete Account",
                          font=ctk.CTkFont(FONT, 12),
                          fg_color="transparent",
                          hover_color=DANGER_LIGHT,
                          text_color=DANGER,
                          border_width=1, border_color=DANGER,
                          height=40, corner_radius=8,
                          command=self._confirm_delete
                          ).grid(row=1, column=0, columnspan=2,
                                 sticky="ew", pady=(8, 0))

    def _submit(self):
        data = {k: (v.get() if not isinstance(v, ctk.CTkTextbox)
                    else v.get("1.0","end").strip())
                for k, v in self._form_vars.items()}

        if self._edit_mode:
            uid = self.prefill.get("user_id")
            ok = self.controller.user_model.update_user(
                uid,
                full_name = data.get("full_name","").strip(),
                phone     = data.get("phone","").strip(),
                role      = data.get("role","employee"),
            )
            if ok:
                if self.on_saved:
                    self.after(200, self.on_saved)
                self.after(300, self.destroy)
            else:
                self._msg_lbl.configure(text="Update failed.")
        else:
            uname = data.get("username","").strip()
            pwd   = data.get("password","")
            cpwd  = data.get("confirm_password","")
            if not uname or len(uname) < 3:
                self._msg_lbl.configure(
                    text="Username must be at least 3 characters.")
                return
            if not pwd or len(pwd) < 6:
                self._msg_lbl.configure(
                    text="Password must be at least 6 characters.")
                return
            if pwd != cpwd:
                self._msg_lbl.configure(
                    text="Passwords do not match.")
                return
            if self.controller.user_model.user_exists(uname):
                self._msg_lbl.configure(
                    text=f"Username \'{uname}\' is already taken.")
                return

            d = {
                "username":         uname,
                "password":         pwd,
                "confirm_password": cpwd,
                "full_name":        data.get("full_name","").strip(),
                "phone":            data.get("phone","").strip(),
                "role":             data.get("role","employee"),
                "notes":            "",
            }
            self.controller.on_create_employee(d)
            if self.on_saved:
                self.after(200, self.on_saved)
            self.after(300, self.destroy)

    def _confirm_delete(self):
        uid   = self.prefill.get("user_id")
        uname = self.prefill.get("username","")
        if messagebox.askyesno(
                "Delete Account",
                f"Delete account @{uname}?\nYou cannot remove the last admin.",
                icon="warning", parent=self):
            self.controller.on_delete_employee(uid, uname)
            if self.on_saved:
                self.after(100, self.on_saved)
            self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# UserMgmtView — full-width table + popups
# ─────────────────────────────────────────────────────────────────────────────

class UserMgmtView(ctk.CTkFrame):

    ROLE_COLORS = {
        "admin":        (ACCENT_LIGHT,  ACCENT),
        "doctor":       (SUCCESS_LIGHT, SUCCESS),
        "nurse":        ("#FCE7F3",      "#BE185D"),
        "receptionist": (WARNING_LIGHT, WARNING),
        "employee":     ("#F3F4F6",      TEXT_SECONDARY),
    }

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller   = controller
        self._users_cache = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(self, controller, active="users")
        self._sidebar.grid(row=0, column=0, sticky="ns")

        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_table()
        self._load_users()

    # ── Data ──────────────────────────────────────────────────────────────

    def _load_users(self):
        try:
            users = self.controller.user_model.get_all_users()
        except Exception:
            users = []
        self.render(users or [])

    # ── Top bar ───────────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = ctk.CTkFrame(self._content, fg_color=PANEL_BG, height=64,
                           border_width=1, border_color=BORDER,
                           corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="👥  User Management",
                     font=ctk.CTkFont(FONT, 20, "bold"),
                     text_color=TEXT_PRIMARY
                     ).grid(row=0, column=0, padx=24, sticky="w")

        acts = ctk.CTkFrame(bar, fg_color="transparent")
        acts.grid(row=0, column=2, padx=24, pady=14)

        ctk.CTkButton(
            acts, text="↻  Refresh", width=100, height=36,
            font=ctk.CTkFont(FONT, 12),
            fg_color=PANEL_ALT, hover_color=ACCENT_LIGHT,
            text_color=TEXT_PRIMARY, corner_radius=8,
            command=self._load_users
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            acts, text="＋  Add User", width=130, height=36,
            font=ctk.CTkFont(FONT, 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            corner_radius=8,
            command=self._open_add
        ).pack(side="left")

    # ── Full-width table ──────────────────────────────────────────────────

    def _build_table(self):
        wrapper = ctk.CTkFrame(self._content, fg_color=PANEL_BG,
                               border_width=1, border_color=BORDER,
                               corner_radius=12)
        wrapper.grid(row=1, column=0, sticky="nsew",
                     padx=16, pady=16)
        wrapper.grid_rowconfigure(2, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        # Title + count
        tr = ctk.CTkFrame(wrapper, fg_color="transparent")
        tr.grid(row=0, column=0, sticky="ew",
                padx=16, pady=(14, 6))
        tr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tr, text="Staff Accounts",
                     font=ctk.CTkFont(FONT, 14, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")

        self._count_lbl = ctk.CTkLabel(
            tr, text="",
            font=ctk.CTkFont(FONT, 11),
            text_color=TEXT_SECONDARY)
        self._count_lbl.grid(row=0, column=1, sticky="e")

        # Column headers
        COLS = [
            ("Username",   140),
            ("Full Name",  200),
            ("Role",       120),
            ("Phone",      140),
            ("Created",    130),
        ]
        hdr = ctk.CTkFrame(wrapper, fg_color="#F8FAFC",
                           height=34, corner_radius=0)
        hdr.grid(row=1, column=0, sticky="ew")
        hdr.grid_propagate(False)

        for col, (lbl, w) in enumerate(COLS):
            ctk.CTkLabel(hdr, text=lbl,
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_SECONDARY,
                         width=w, anchor="w"
                         ).grid(row=0, column=col,
                                padx=(14 if col == 0 else 8, 4),
                                sticky="w")

        self._table_scroll = ctk.CTkScrollableFrame(
            wrapper, fg_color="transparent")
        self._table_scroll.grid(row=2, column=0, sticky="nsew")
        self._table_scroll.grid_columnconfigure(0, weight=1)

    def _render_row(self, user: dict, idx: int):
        role   = user.get("role", "employee")
        r_bg, r_fg = self.ROLE_COLORS.get(
            role, ("#F3F4F6", TEXT_SECONDARY))
        bg = PANEL_BG if idx % 2 == 0 else "#FAFBFD"

        row = ctk.CTkFrame(self._table_scroll,
                           fg_color=bg, height=48,
                           corner_radius=0)
        row.grid(row=idx, column=0, sticky="ew")
        row.grid_propagate(False)

        def enter(e, r=row): r.configure(fg_color=ACCENT_LIGHT)
        def leave(e, r=row, b=bg): r.configure(fg_color=b)
        def click(e, u=user): self._open_detail(u)

        row.bind("<Enter>", enter)
        row.bind("<Leave>", leave)
        row.bind("<Button-1>", click)

        created = (user.get("created_at") or "")[:10] or "—"

        # Username
        l0 = ctk.CTkLabel(row, text=f"@{user.get('username','—')}",
                          font=ctk.CTkFont(FONT, 13, "bold"),
                          text_color=ACCENT, width=140, anchor="w")
        l0.grid(row=0, column=0, padx=(14, 4), sticky="w")

        # Full name
        l1 = ctk.CTkLabel(row,
                          text=user.get("full_name","—") or "—",
                          font=ctk.CTkFont(FONT, 12),
                          text_color=TEXT_PRIMARY,
                          width=200, anchor="w")
        l1.grid(row=0, column=1, padx=(8, 4), sticky="w")

        # Role badge
        badge_cell = ctk.CTkFrame(row, fg_color="transparent",
                                   width=120)
        badge_cell.grid(row=0, column=2, padx=(8, 4), sticky="w")
        badge_cell.grid_propagate(False)
        badge = ctk.CTkFrame(badge_cell, fg_color=r_bg,
                              corner_radius=6)
        badge.pack(anchor="w", pady=13)
        ctk.CTkLabel(badge, text=role.capitalize(),
                     font=ctk.CTkFont(FONT, 10, "bold"),
                     text_color=r_fg
                     ).pack(padx=10, pady=3)

        # Phone
        l3 = ctk.CTkLabel(row,
                          text=user.get("phone","—") or "—",
                          font=ctk.CTkFont(FONT, 12),
                          text_color=TEXT_SECONDARY,
                          width=140, anchor="w")
        l3.grid(row=0, column=3, padx=(8, 4), sticky="w")

        # Created
        l4 = ctk.CTkLabel(row, text=created,
                          font=ctk.CTkFont(FONT, 11),
                          text_color=TEXT_SECONDARY,
                          width=130, anchor="w")
        l4.grid(row=0, column=4, padx=(8, 14), sticky="w")

        for w in [l0, l1, l3, l4, badge_cell, badge]:
            try:
                w.bind("<Enter>", enter)
                w.bind("<Leave>", leave)
                w.bind("<Button-1>", click)
            except Exception:
                pass

    # ── Popup openers ──────────────────────────────────────────────────────

    def _open_add(self):
        UserFormWindow(
            parent_view=self,
            controller=self.controller,
            prefill=None,
            on_saved=self._load_users
        )

    def _open_detail(self, user: dict):
        UserFormWindow(
            parent_view=self,
            controller=self.controller,
            prefill=user,
            on_saved=self._load_users
        )

    # ── Controller interface ───────────────────────────────────────────────

    def render(self, users: list):
        self._users_cache = users
        for w in self._table_scroll.winfo_children():
            w.destroy()

        n = len(users)
        self._count_lbl.configure(
            text=f"{n} account{'s' if n != 1 else ''}")

        if not users:
            ctk.CTkLabel(self._table_scroll,
                         text="No accounts found.",
                         font=ctk.CTkFont(FONT, 13),
                         text_color=TEXT_SECONDARY
                         ).grid(row=0, column=0, pady=60)
            return

        for idx, user in enumerate(users):
            self._render_row(user, idx)

    def show_form_message(self, message: str, success: bool = True):
        try:
            Toast.show(self._content, message, success=success)
        except Exception:
            pass

    def clear_form(self):
        self._load_users()