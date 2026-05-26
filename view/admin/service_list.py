# view/admin/service_list.py
"""
ServiceListView — Medical Services Catalog
Style : Light / Professional

Layout:
  ├── Sidebar (col 0 fixed)
  └── Content:
        ├── Top bar  : title + search + category filter + "Add Service"
        └── Full-width services table (self-loading)

Popups:
  • ServiceFormWindow  — add or edit a service
  • ServiceDetailWindow — read-only view with edit/delete actions
"""

import customtkinter as ctk
from tkinter import messagebox
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
PURPLE         = "#7C3AED"
PURPLE_LIGHT   = "#EDE9FE"

FONT = "Helvetica"

CATEGORIES = [
    "Consultation", "Procedure", "Laboratory", "Imaging",
    "Vaccination", "Physiotherapy", "Surgery", "Emergency",
    "Follow-up", "Other",
]

CAT_COLORS = {
    "Consultation":  (ACCENT_LIGHT,  ACCENT),
    "Procedure":     (PURPLE_LIGHT,  PURPLE),
    "Laboratory":    ("#FEF9C3",     "#854D0E"),
    "Imaging":       ("#F0FDF4",     SUCCESS),
    "Vaccination":   ("#FCE7F3",     "#BE185D"),
    "Physiotherapy": ("#FFF7ED",     WARNING),
    "Surgery":       (DANGER_LIGHT,  DANGER),
    "Emergency":     (DANGER_LIGHT,  DANGER),
    "Follow-up":     (SUCCESS_LIGHT, SUCCESS),
    "Other":         ("#F3F4F6",     TEXT_SECONDARY),
}


# ══════════════════════════════════════════════════════════════════════════════
# POPUP — Add / Edit service
# ══════════════════════════════════════════════════════════════════════════════

class ServiceFormWindow(ctk.CTkToplevel):

    def __init__(self, parent_view, controller,
                 prefill: dict = None, on_saved=None):
        super().__init__()
        self.parent_view = parent_view
        self.controller  = controller
        self.prefill     = prefill or {}
        self.on_saved    = on_saved
        self._edit_mode  = bool(prefill)
        self._form_vars  = {}

        title = "Edit Service" if self._edit_mode else "Add New Service"
        self.title(f"🩺  {title}")
        self.geometry("560x520")
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
        hdr_bg = WARNING_LIGHT if self._edit_mode else SUCCESS_LIGHT
        hdr_fg = WARNING       if self._edit_mode else SUCCESS
        icon   = "✏️" if self._edit_mode else "➕"
        title  = "Edit Service" if self._edit_mode else "Add New Service"

        hdr = ctk.CTkFrame(scroll, fg_color=hdr_bg, corner_radius=10)
        hdr.grid(row=0, column=0, columnspan=2,
                 sticky="ew", padx=20, pady=(20, 14))
        ctk.CTkLabel(hdr, text=f"{icon}  {title}",
                     font=ctk.CTkFont(FONT, 16, "bold"),
                     text_color=hdr_fg
                     ).pack(anchor="w", padx=20, pady=12)

        def entry(row, col, label, key, placeholder="", colspan=1):
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

        def textbox(row, col, label, key, colspan=1):
            fr = ctk.CTkFrame(scroll, fg_color="transparent")
            fr.grid(row=row, column=col, columnspan=colspan,
                    sticky="ew", padx=(20, 10), pady=5)
            fr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(fr, text=label,
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            box = ctk.CTkTextbox(fr, height=75,
                                  font=ctk.CTkFont(FONT, 12),
                                  fg_color=PANEL_ALT,
                                  border_width=1, border_color=BORDER,
                                  text_color=TEXT_PRIMARY)
            box.grid(row=1, column=0, sticky="ew")
            val = self.prefill.get(key, "") or ""
            if val:
                box.insert("1.0", val)
            self._form_vars[key] = box

        # Fields
        entry(1, 0, "Service Code", "barcode", "e.g. CONS-001")
        option(1, 1, "Category", "category", CATEGORIES)
        entry(2, 0, "Service Name *", "name",
              "e.g. General Consultation", colspan=2)

        # Price and duration with prefill conversion
        price_val = str(self.prefill.get("price", "")) if self.prefill else ""
        dur_val   = str(self.prefill.get("duration_min", "")) if self.prefill else ""
        self.prefill["selling_price"] = price_val
        self.prefill["quantity"]      = dur_val

        entry(3, 0, "Price (DA) *", "selling_price", "0.00")
        entry(3, 1, "Duration (min)", "quantity", "30")
        textbox(4, 0, "Description", "notes", colspan=2)

        # Feedback
        self._msg_lbl = ctk.CTkLabel(
            scroll, text="",
            font=ctk.CTkFont(FONT, 12),
            text_color=SUCCESS, anchor="w")
        self._msg_lbl.grid(row=5, column=0, columnspan=2,
                           padx=20, pady=(4, 0), sticky="w")

        # Buttons
        br = ctk.CTkFrame(scroll, fg_color="transparent")
        br.grid(row=6, column=0, columnspan=2,
                sticky="ew", padx=20, pady=(8, 24))
        br.grid_columnconfigure(0, weight=1)
        br.grid_columnconfigure(1, weight=1)

        save_lbl   = "Update Service" if self._edit_mode else "Add Service"
        save_color = WARNING if self._edit_mode else SUCCESS
        save_hover = "#B45309" if self._edit_mode else "#15803D"

        ctk.CTkButton(br, text=save_lbl,
                      font=ctk.CTkFont(FONT, 13, "bold"),
                      fg_color=save_color, hover_color=save_hover,
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
            ctk.CTkButton(br, text="🗑  Delete Service",
                          font=ctk.CTkFont(FONT, 12),
                          fg_color="transparent",
                          hover_color=DANGER_LIGHT,
                          text_color=DANGER,
                          border_width=1, border_color=DANGER,
                          height=40, corner_radius=8,
                          command=self._confirm_delete
                          ).grid(row=1, column=0, columnspan=2,
                                 sticky="ew", pady=(8, 0))

    def _get_data(self):
        data = {}
        for key, var in self._form_vars.items():
            if isinstance(var, ctk.CTkTextbox):
                data[key] = var.get("1.0", "end").strip()
            else:
                data[key] = var.get().strip()
        return data

    def _submit(self):
        data = self._get_data()
        if not data.get("name"):
            self._msg_lbl.configure(
                text="Service name is required.", text_color=DANGER)
            return
        try:
            float(data.get("selling_price") or 0)
        except ValueError:
            self._msg_lbl.configure(
                text="Invalid price.", text_color=DANGER)
            return

        if self._edit_mode:
            sid = self.prefill.get("service_id")
            self.controller.service_model.update_service(
                sid,
                name         = data["name"],
                category     = data.get("category", CATEGORIES[0]),
                price        = float(data.get("selling_price") or 0),
                duration_min = int(data.get("quantity") or 30),
                description  = data.get("notes", ""),
            )
        else:
            code = data.get("barcode", "").strip()
            if code and self.controller.service_model.service_exists(code):
                self._msg_lbl.configure(
                    text="Service code already exists.", text_color=DANGER)
                return
            self.controller.service_model.add_service(
                code         = code,
                name         = data["name"],
                category     = data.get("category", CATEGORIES[0]),
                price        = float(data.get("selling_price") or 0),
                duration_min = int(data.get("quantity") or 30),
                description  = data.get("notes", ""),
            )

        if self.on_saved:
            self.after(300, self.on_saved)
        self.after(400, self.destroy)

    def _confirm_delete(self):
        name = self.prefill.get("name", "")
        sid  = self.prefill.get("service_id")
        if messagebox.askyesno(
                "Delete Service",
                f"Delete '{name}'?\nThis cannot be undone.",
                icon="warning", parent=self):
            self.controller.on_delete_service(sid)
            if self.on_saved:
                self.after(100, self.on_saved)
            self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# POPUP — Service Detail (read-only + actions)
# ══════════════════════════════════════════════════════════════════════════════

class ServiceDetailWindow(ctk.CTkToplevel):

    def __init__(self, parent_view, controller,
                 service: dict, on_refresh=None):
        super().__init__()
        self.parent_view = parent_view
        self.controller  = controller
        self.service     = service
        self.on_refresh  = on_refresh

        self.title(f"🩺  {service.get('name', 'Service')}")
        self.geometry("440x420")
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

        svc = self.service
        cat_bg, cat_fg = CAT_COLORS.get(
            svc.get("category", "Other"), ("#F3F4F6", TEXT_SECONDARY))

        # Header card
        hdr = ctk.CTkFrame(scroll, fg_color=PANEL_BG,
                           border_width=1, border_color=BORDER,
                           corner_radius=12)
        hdr.grid(row=0, column=0, sticky="ew",
                 padx=20, pady=(20, 12))
        hdr.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew",
                 padx=16, pady=(14, 6))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top, text=svc.get("name", "—"),
                     font=ctk.CTkFont(FONT, 17, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")

        badge = ctk.CTkFrame(top, fg_color=cat_bg, corner_radius=8)
        badge.grid(row=0, column=1)
        ctk.CTkLabel(badge, text=svc.get("category", "—"),
                     font=ctk.CTkFont(FONT, 11, "bold"),
                     text_color=cat_fg
                     ).pack(padx=10, pady=4)

        ctk.CTkLabel(hdr,
                     text=f"Code: {svc.get('code','—') or '—'}",
                     font=ctk.CTkFont(FONT, 11),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=1, column=0, sticky="w",
                            padx=16, pady=(0, 12))

        # Price + duration cards
        stats = ctk.CTkFrame(scroll, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew",
                   padx=20, pady=(0, 12))
        stats.grid_columnconfigure(0, weight=1)
        stats.grid_columnconfigure(1, weight=1)

        for col, (label, val, color) in enumerate([
            ("Price", f"{svc.get('price', 0):,.2f} DA", ACCENT),
            ("Duration", f"{svc.get('duration_min', 30)} min", SUCCESS),
        ]):
            card = ctk.CTkFrame(stats, fg_color=PANEL_BG,
                                border_width=1, border_color=BORDER,
                                corner_radius=10)
            card.grid(row=0, column=col, sticky="ew",
                      padx=(0 if col == 0 else 6, 0))
            ctk.CTkLabel(card, text=val,
                         font=ctk.CTkFont(FONT, 20, "bold"),
                         text_color=color
                         ).pack(pady=(12, 2))
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_SECONDARY
                         ).pack(pady=(0, 12))

        # Description
        if svc.get("description"):
            desc_card = ctk.CTkFrame(scroll, fg_color=PANEL_BG,
                                     border_width=1, border_color=BORDER,
                                     corner_radius=10)
            desc_card.grid(row=2, column=0, sticky="ew",
                           padx=20, pady=(0, 12))
            ctk.CTkLabel(desc_card, text="Description",
                         font=ctk.CTkFont(FONT, 12, "bold"),
                         text_color=TEXT_PRIMARY, anchor="w"
                         ).grid(row=0, column=0, padx=14,
                                pady=(10, 4), sticky="w")
            ctk.CTkLabel(desc_card,
                         text=svc["description"],
                         font=ctk.CTkFont(FONT, 12),
                         text_color=TEXT_SECONDARY,
                         anchor="w", wraplength=360, justify="left"
                         ).grid(row=1, column=0, padx=14,
                                pady=(0, 12), sticky="w")

        # Action buttons
        acts = ctk.CTkFrame(scroll, fg_color="transparent")
        acts.grid(row=3, column=0, sticky="ew",
                  padx=20, pady=(0, 24))
        acts.grid_columnconfigure(0, weight=1)
        acts.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(acts, text="✏️  Edit Service",
                      font=ctk.CTkFont(FONT, 12, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      height=38, corner_radius=8,
                      command=self._open_edit
                      ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(acts, text="Close",
                      font=ctk.CTkFont(FONT, 12),
                      fg_color=PANEL_ALT, hover_color=BORDER,
                      text_color=TEXT_PRIMARY,
                      height=38, corner_radius=8,
                      command=self.destroy
                      ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _open_edit(self):
        self.destroy()
        ServiceFormWindow(
            parent_view=self.parent_view,
            controller=self.controller,
            prefill=self.service,
            on_saved=self.on_refresh
        )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════

class ServiceListView(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller       = controller
        self._services_cache  = []
        self._active_filter   = "All"

        # Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(self, controller, active="services")
        self._sidebar.grid(row=0, column=0, sticky="ns")

        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(2, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_filter_bar()
        self._build_table()
        self._load_services()

    # ══════════════════════════════════════════════════════════════════════
    # DATA
    # ══════════════════════════════════════════════════════════════════════

    def _load_services(self, query: str = ""):
        try:
            if query:
                fn = getattr(self.controller.service_model,
                             "search_service", None)
                services = fn(query) if fn else []
            else:
                services = (self.controller.service_model
                            .get_all_services())
        except Exception:
            services = []
        self.render_services(services or [])

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

        ctk.CTkLabel(bar, text="🩺  Services & Pricing",
                     font=ctk.CTkFont(FONT, 20, "bold"),
                     text_color=TEXT_PRIMARY
                     ).grid(row=0, column=0, padx=24, sticky="w")

        # Search
        sf = ctk.CTkFrame(bar, fg_color=PANEL_ALT,
                          border_width=1, border_color=BORDER,
                          corner_radius=8, height=36)
        sf.grid(row=0, column=1, padx=20, pady=14, sticky="ew")
        sf.grid_propagate(False)
        sf.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(sf, text="🔍",
                     font=ctk.CTkFont(size=13),
                     text_color=TEXT_SECONDARY
                     ).grid(row=0, column=0, padx=(10, 4))

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(sf, textvariable=self._search_var,
                     placeholder_text="Search by name or code…",
                     border_width=0, fg_color="transparent",
                     font=ctk.CTkFont(FONT, 13),
                     text_color=TEXT_PRIMARY
                     ).grid(row=0, column=1, sticky="ew",
                            padx=(0, 8), pady=4)

        # Buttons
        acts = ctk.CTkFrame(bar, fg_color="transparent")
        acts.grid(row=0, column=2, padx=24, pady=14)

        ctk.CTkButton(
            acts, text="↻  Refresh", width=100, height=36,
            font=ctk.CTkFont(FONT, 12),
            fg_color=PANEL_ALT, hover_color=ACCENT_LIGHT,
            text_color=TEXT_PRIMARY, corner_radius=8,
            command=self._load_services
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            acts, text="＋  Add Service", width=140, height=36,
            font=ctk.CTkFont(FONT, 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            corner_radius=8,
            command=self._open_add
        ).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════
    # CATEGORY FILTER PILLS
    # ══════════════════════════════════════════════════════════════════════

    def _build_filter_bar(self):
        bar = ctk.CTkFrame(self._content, fg_color=PANEL_BG,
                           height=46, border_width=1,
                           border_color=BORDER, corner_radius=0)
        bar.grid(row=1, column=0, sticky="ew")
        bar.grid_propagate(False)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.place(relx=0, rely=0.5, anchor="w", x=16)

        self._filter_btns = {}
        for cat in ["All"] + CATEGORIES:
            btn = ctk.CTkButton(
                inner, text=cat,
                width=max(42, len(cat) * 7 + 18),
                height=28,
                font=ctk.CTkFont(FONT, 11),
                corner_radius=14,
                fg_color=ACCENT if cat == "All" else PANEL_ALT,
                hover_color=ACCENT_LIGHT,
                text_color="white" if cat == "All" else TEXT_SECONDARY,
                command=lambda c=cat: self._apply_filter(c)
            )
            btn.pack(side="left", padx=3)
            self._filter_btns[cat] = btn

    def _apply_filter(self, category: str):
        self._active_filter = category
        for cat, btn in self._filter_btns.items():
            active = (cat == category)
            btn.configure(
                fg_color=ACCENT if active else PANEL_ALT,
                text_color="white" if active else TEXT_SECONDARY)
        self._render_table(self._services_cache)

    # ══════════════════════════════════════════════════════════════════════
    # FULL-WIDTH TABLE
    # ══════════════════════════════════════════════════════════════════════

    def _build_table(self):
        wrapper = ctk.CTkFrame(self._content, fg_color=PANEL_BG,
                               border_width=1, border_color=BORDER,
                               corner_radius=12)
        wrapper.grid(row=2, column=0, sticky="nsew",
                     padx=16, pady=16)
        wrapper.grid_rowconfigure(2, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        # Title + count
        tr = ctk.CTkFrame(wrapper, fg_color="transparent")
        tr.grid(row=0, column=0, sticky="ew",
                padx=16, pady=(14, 6))
        tr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tr, text="Service Catalog",
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
            ("Code",         90),
            ("Service Name", 240),
            ("Category",     130),
            ("Duration",      90),
            ("Price (DA)",   120),
            ("Description",  260),
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

    def _render_table(self, services: list):
        for w in self._table_scroll.winfo_children():
            w.destroy()

        filtered = (services if self._active_filter == "All"
                    else [s for s in services
                          if s.get("category") == self._active_filter])

        n = len(filtered)
        self._count_lbl.configure(
            text=f"{n} service{'s' if n != 1 else ''}")

        if not filtered:
            ctk.CTkLabel(self._table_scroll,
                         text="No services found.",
                         font=ctk.CTkFont(FONT, 13),
                         text_color=TEXT_SECONDARY
                         ).grid(row=0, column=0, pady=60)
            return

        for idx, svc in enumerate(filtered):
            self._render_row(svc, idx)

    def _render_row(self, svc: dict, idx: int):
        cat_bg, cat_fg = CAT_COLORS.get(
            svc.get("category", "Other"), ("#F3F4F6", TEXT_SECONDARY))
        bg = PANEL_BG if idx % 2 == 0 else "#FAFBFD"

        row = ctk.CTkFrame(self._table_scroll,
                           fg_color=bg, height=48,
                           corner_radius=0)
        row.grid(row=idx, column=0, sticky="ew")
        row.grid_propagate(False)

        def enter(e, r=row): r.configure(fg_color=ACCENT_LIGHT)
        def leave(e, r=row, b=bg): r.configure(fg_color=b)
        def click(e, s=svc): self._open_detail(s)

        row.bind("<Enter>", enter)
        row.bind("<Leave>", leave)
        row.bind("<Button-1>", click)

        desc = (svc.get("description") or "—")[:40]

        # Code
        lbl0 = ctk.CTkLabel(row,
                             text=svc.get("code", "—") or "—",
                             font=ctk.CTkFont(FONT, 11),
                             text_color=TEXT_SECONDARY,
                             width=90, anchor="w")
        lbl0.grid(row=0, column=0, padx=(14, 4), sticky="w")

        # Name
        lbl1 = ctk.CTkLabel(row, text=svc.get("name", "—"),
                             font=ctk.CTkFont(FONT, 13, "bold"),
                             text_color=TEXT_PRIMARY,
                             width=240, anchor="w")
        lbl1.grid(row=0, column=1, padx=(8, 4), sticky="w")

        # Category badge
        badge_cell = ctk.CTkFrame(row, fg_color="transparent",
                                   width=130)
        badge_cell.grid(row=0, column=2, padx=(8, 4), sticky="w")
        badge_cell.grid_propagate(False)
        badge = ctk.CTkFrame(badge_cell, fg_color=cat_bg,
                              corner_radius=6)
        badge.pack(anchor="w", pady=12)
        ctk.CTkLabel(badge, text=svc.get("category", "—"),
                     font=ctk.CTkFont(FONT, 10, "bold"),
                     text_color=cat_fg
                     ).pack(padx=8, pady=3)

        # Duration
        lbl3 = ctk.CTkLabel(row,
                             text=f"{svc.get('duration_min',30)} min",
                             font=ctk.CTkFont(FONT, 12),
                             text_color=TEXT_SECONDARY,
                             width=90, anchor="w")
        lbl3.grid(row=0, column=3, padx=(8, 4), sticky="w")

        # Price
        lbl4 = ctk.CTkLabel(row,
                             text=f"{svc.get('price', 0):,.2f}",
                             font=ctk.CTkFont(FONT, 13, "bold"),
                             text_color=ACCENT,
                             width=120, anchor="w")
        lbl4.grid(row=0, column=4, padx=(8, 4), sticky="w")

        # Description
        lbl5 = ctk.CTkLabel(row, text=desc,
                             font=ctk.CTkFont(FONT, 11),
                             text_color=TEXT_SECONDARY,
                             width=260, anchor="w")
        lbl5.grid(row=0, column=5, padx=(8, 14), sticky="w")

        for lbl in [lbl0, lbl1, lbl3, lbl4, lbl5,
                    badge_cell, badge]:
            try:
                lbl.bind("<Enter>", enter)
                lbl.bind("<Leave>", leave)
                lbl.bind("<Button-1>", click)
            except Exception:
                pass

    # ══════════════════════════════════════════════════════════════════════
    # POPUP OPENERS
    # ══════════════════════════════════════════════════════════════════════

    def _open_add(self):
        ServiceFormWindow(
            parent_view=self,
            controller=self.controller,
            prefill=None,
            on_saved=self._load_services
        )

    def _open_detail(self, svc: dict):
        ServiceDetailWindow(
            parent_view=self,
            controller=self.controller,
            service=svc,
            on_refresh=self._load_services
        )

    # ══════════════════════════════════════════════════════════════════════
    # CONTROLLER INTERFACE
    # ══════════════════════════════════════════════════════════════════════

    def render_services(self, services: list):
        self._services_cache = services
        self._render_table(services)

    def show_bar_message(self, message: str, success: bool = True):
        try:
            Toast.show(self._content, message, success=success)
        except Exception:
            pass

    # Legacy controller-compat methods (main.py may call these)
    def get_form_data(self): return {}
    def populate_form(self, svc): pass
    def set_edit_mode(self, state): pass
    def clear_form(self): self._load_services()

    def _on_search(self, *_):
        q = self._search_var.get().strip()
        self._load_services(q)
        try:
            self.controller.on_search(q)
        except Exception:
            pass


# Backwards-compat alias
class AddServiceView(ServiceListView):
    pass