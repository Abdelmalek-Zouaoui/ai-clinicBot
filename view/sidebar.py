# view/components/sidebar.py
"""
Sidebar — Shared navigation panel + Toast notification system.

Usage:
    from view.components.sidebar import Sidebar, Toast

    sidebar = Sidebar(parent=self, controller=controller, active="dashboard")
    sidebar.grid(row=0, column=0, sticky="ns")

    Toast.show(self._content, "Patient saved!", success=True)
"""

import customtkinter as ctk

LIGHT = {
    "sidebar_bg":    "#1E2A3A",
    "sidebar_hover": "#2D3F54",
    "sidebar_active":"#2563EB",
    "logo_bg":       "#152030",
    "text_dim":      "#94A3B8",
    "text_bright":   "#F1F5F9",
    "text_active":   "#FFFFFF",
    "toggle_bg":     "#2D3F54",
    "divider":       "#2D3F54",
    "user_bg":       "#152030",
}

DARK = {
    "sidebar_bg":    "#0F172A",
    "sidebar_hover": "#1E293B",
    "sidebar_active":"#3B82F6",
    "logo_bg":       "#080F1A",
    "text_dim":      "#64748B",
    "text_bright":   "#CBD5E1",
    "text_active":   "#FFFFFF",
    "toggle_bg":     "#1E293B",
    "divider":       "#1E293B",
    "user_bg":       "#080F1A",
}

NAV_ITEMS = [
    ("dashboard",    "🏠", "Dashboard"),
    ("patients",     "👤", "Patients"),
    ("appointments", "📅", "Appointments"),
    ("waiting_room", "🟢", "Waiting Room"),
    ("prescriptions","📋", "Prescriptions"),
    ("services",     "🩺", "Services"),
    ("export",       "📤", "Export"),
    ("users",        "👥", "Users"),
    ("settings",     "⚙️", "Settings"),
]

FONT = "Helvetica"

# Bottom section fixed height (toggle + user badge + logout)
BOTTOM_H = 170


class Sidebar(ctk.CTkFrame):

    WIDTH = 210

    def __init__(self, parent, controller, active="dashboard"):
        self._is_dark = self._load_dark_pref(controller)
        p = DARK if self._is_dark else LIGHT

        super().__init__(parent, fg_color=p["sidebar_bg"],
                         width=self.WIDTH, corner_radius=0)
        self.grid_propagate(False)

        self.controller = controller
        self.active     = active
        self._p         = p
        self._btn_refs  = {}

        self.grid_columnconfigure(0, weight=1)

        self._build_logo()
        self._build_nav()
        # Bottom pinned via place() after widget is mapped
        self.bind("<Configure>", self._on_resize)
        self._bottom = self._build_bottom()

    def _on_resize(self, event):
        """Re-pin bottom panel whenever sidebar height changes."""
        h = event.height
        if h > BOTTOM_H:
            self._bottom.configure(width=self.WIDTH, height=BOTTOM_H)
            self._bottom.place(x=0, y=h - BOTTOM_H)

    def _build_logo(self):
        logo = ctk.CTkFrame(self, fg_color=self._p["logo_bg"],
                            height=74, corner_radius=0)
        logo.grid(row=0, column=0, sticky="ew")
        logo.grid_propagate(False)
        logo.grid_columnconfigure(0, weight=1)

        try:
            name = self.controller.get_app_name()
        except Exception:
            name = "CLINIC"

        ctk.CTkLabel(logo, text="🏥", font=ctk.CTkFont(size=22)
                     ).grid(row=0, column=0, pady=(12, 0))
        ctk.CTkLabel(logo, text=name[:16].upper(),
                     font=ctk.CTkFont(FONT, 10, "bold"),
                     text_color=self._p["text_bright"]
                     ).grid(row=1, column=0, pady=(2, 10))

    def _build_nav(self):
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        nav.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(nav, text="NAVIGATION",
                     font=ctk.CTkFont(FONT, 9, "bold"),
                     text_color=self._p["text_dim"]
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(4, 6))

        for i, (key, icon, label) in enumerate(NAV_ITEMS):
            is_active = (key == self.active)
            btn = ctk.CTkButton(
                nav,
                text=f"  {icon}  {label}",
                anchor="w",
                font=ctk.CTkFont(FONT, 13,
                                  weight="bold" if is_active else "normal"),
                fg_color=self._p["sidebar_active"] if is_active else "transparent",
                hover_color=self._p["sidebar_hover"],
                text_color=self._p["text_active"] if is_active
                           else self._p["text_bright"],
                height=38, corner_radius=8,
                command=lambda k=key: self.controller.navigate(k)
            )
            btn.grid(row=i + 1, column=0, sticky="ew", padx=8, pady=2)
            self._btn_refs[key] = btn

    def _build_bottom(self):
        """Build bottom section and return it (placed via _on_resize)."""
        bottom = ctk.CTkFrame(self, fg_color=self._p["user_bg"],
                              width=self.WIDTH, height=BOTTOM_H,
                              corner_radius=0)
        bottom.pack_propagate(False)
        bottom.grid_columnconfigure(0, weight=1)

        # Divider line
        ctk.CTkFrame(bottom, fg_color=self._p["divider"],
                     height=1).pack(fill="x")

        # Dark / Light toggle
        tr = ctk.CTkFrame(bottom, fg_color="transparent")
        tr.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(tr,
                     text=("☀️  Light Mode" if self._is_dark
                           else "🌙  Dark Mode"),
                     font=ctk.CTkFont(FONT, 11),
                     text_color=self._p["text_dim"]
                     ).pack(side="left")

        sw = ctk.CTkSwitch(tr, text="", width=36,
                           fg_color=self._p["toggle_bg"],
                           progress_color=self._p["sidebar_active"],
                           command=self._toggle_dark_mode)
        sw.pack(side="right")
        if self._is_dark:
            sw.select()

        # User badge
        try:
            user  = self.controller.current_user
            uname = user.get("username", "user")
            role  = user.get("role", "")
        except Exception:
            uname, role = "user", ""

        uf = ctk.CTkFrame(bottom, fg_color=self._p["toggle_bg"],
                          corner_radius=8)
        uf.pack(fill="x", padx=10, pady=(0, 4))

        av = ctk.CTkFrame(uf, fg_color=self._p["sidebar_active"],
                          width=30, height=30, corner_radius=15)
        av.pack(side="left", padx=(8, 6), pady=8)
        av.pack_propagate(False)
        ctk.CTkLabel(av, text=uname[0].upper(),
                     font=ctk.CTkFont(FONT, 12, "bold"),
                     text_color="#FFFFFF"
                     ).place(relx=0.5, rely=0.5, anchor="center")

        info = ctk.CTkFrame(uf, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(info, text=f"@{uname}",
                     font=ctk.CTkFont(FONT, 11, "bold"),
                     text_color=self._p["text_bright"],
                     anchor="w").pack(anchor="w")
        if role:
            ctk.CTkLabel(info, text=role.capitalize(),
                         font=ctk.CTkFont(FONT, 9),
                         text_color=self._p["text_dim"],
                         anchor="w").pack(anchor="w")

        # Logout
        ctk.CTkButton(
            bottom, text="⎋  Logout", anchor="w",
            font=ctk.CTkFont(FONT, 12),
            fg_color="transparent",
            hover_color=self._p["sidebar_hover"],
            text_color=self._p["text_dim"],
            height=34, corner_radius=8,
            command=lambda: self.controller.navigate("logout")
        ).pack(fill="x", padx=8, pady=(2, 8))

        return bottom

    def _toggle_dark_mode(self):
        self._is_dark = not self._is_dark
        mode = "dark" if self._is_dark else "light"
        try:
            self.controller.db.set_setting("app_theme", mode)
        except Exception:
            pass
        ctk.set_appearance_mode(mode)

    @staticmethod
    def _load_dark_pref(controller):
        try:
            return controller.db.get_setting("app_theme", "light") == "dark"
        except Exception:
            return False


# ═════════════════════════════════════════════════════════════════════════════
# TOAST  — animated slide-up notification banner
# ═════════════════════════════════════════════════════════════════════════════

class Toast:
    """
    Slide-up toast notification displayed over any CTkFrame.

    Usage:
        Toast.show(self._content, "Saved!", success=True)
        Toast.show(self._content, "Error!", success=False)
        Toast.show(self._content, "Note", kind="info")
        Toast.show(self._content, "Careful", kind="warning")
    """

    _STYLES = {
        "success": ("#15803D", "#F0FDF4", "#86EFAC"),
        "error":   ("#DC2626", "#FEF2F2", "#FCA5A5"),
        "info":    ("#2563EB", "#EFF6FF", "#93C5FD"),
        "warning": ("#D97706", "#FFFBEB", "#FCD34D"),
    }
    _ICONS = {
        "success": "✅",
        "error":   "❌",
        "info":    "ℹ️",
        "warning": "⚠️",
    }

    @classmethod
    def show(cls, parent, message: str,
             success: bool = None,
             kind: str = None,
             duration_ms: int = 3500):

        if kind is None:
            kind = "success" if success is True  else \
                   "error"   if success is False else "info"

        color, bg, border = cls._STYLES.get(kind, cls._STYLES["info"])
        icon = cls._ICONS.get(kind, "ℹ️")

        toast = ctk.CTkFrame(parent, fg_color=bg,
                             border_width=1, border_color=border,
                             corner_radius=10)

        inner = ctk.CTkFrame(toast, fg_color="transparent")
        inner.pack(padx=14, pady=10, fill="x")
        inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(inner, text=icon,
                     font=ctk.CTkFont(size=18)
                     ).grid(row=0, column=0, padx=(0, 10))

        ctk.CTkLabel(inner, text=message,
                     font=ctk.CTkFont(FONT, 13),
                     text_color=color,
                     anchor="w", wraplength=250
                     ).grid(row=0, column=1, sticky="w")

        ctk.CTkButton(inner, text="✕", width=22, height=22,
                      font=ctk.CTkFont(FONT, 11),
                      fg_color="transparent", hover_color=border,
                      text_color=color, corner_radius=6,
                      command=lambda: cls._dismiss(toast)
                      ).grid(row=0, column=2, padx=(10, 0))

        parent.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        tw = min(360, pw - 40)
        th = 64
        x  = pw - tw - 20
        y0 = ph + 10
        y1 = ph - th - 20

        toast.configure(width=tw, height=th)
        toast.place(x=x, y=y0)
        toast.lift()

        cls._animate(toast, y0, y1, steps=14, delay=10)
        parent.after(duration_ms,
                     lambda: cls._animate(toast, y1, ph + 10,
                                          steps=10, delay=12,
                                          on_done=lambda: cls._dismiss(toast)))

    @classmethod
    def _animate(cls, widget, y_from, y_to,
                 steps, delay, on_done=None):
        if not widget.winfo_exists():
            return
        if steps <= 0:
            widget.place_configure(y=int(y_to))
            if on_done:
                on_done()
            return
        new_y = y_from + (y_to - y_from) / steps
        widget.place_configure(y=int(new_y))
        widget.after(delay,
                     lambda: cls._animate(widget, new_y, y_to,
                                          steps - 1, delay, on_done))

    @staticmethod
    def _dismiss(widget):
        try:
            widget.place_forget()
            widget.destroy()
        except Exception:
            pass