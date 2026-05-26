"""
view/admin/supplier_view.py
---------------------------
Supplier Management Page — Smart Pharmacy Management System.

Layout (3-panel):
  Left   (55 %) : Scrollable supplier roster with medicine-type tags
  Right  (45 %) : Two stacked cards —
                    top  → Add / Edit Supplier form
                    bottom → Medicine Types supplied by selected supplier

Pure UI — no SQL, no logic. All actions fire controller callbacks.

Controller callbacks expected
-----------------------------
controller.navigate(key)
controller.on_save_supplier(data: dict)
controller.on_delete_supplier(supplier_id, name)
controller.on_select_supplier(supplier_id)
controller.on_add_supplier_medicine(data: dict)
controller.on_delete_supplier_medicine(row_id, supplier_id)
"""

import customtkinter as ctk
from tkinter import messagebox

# ─────────────────────────── Colour tokens ────────────────────────────
BG_DARK    = "#242424"
BG_SIDEBAR = "#1a1a2e"
BG_CARD    = "#2d2d2d"
BG_INPUT   = "#1e1e2e"
BG_HEADER  = "#1a1a2e"
BG_ODD     = "#2a2a2a"
BG_EVEN    = "#323232"
BG_HOVER   = "#3a3a3a"
ACCENT_BLUE  = "#1f538d"
ACCENT_TEAL  = "#2fa572"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED   = "#ef4444"
ACCENT_PURPLE= "#7c3aed"
TEXT_LIGHT = "#e2e8f0"
TEXT_MUTED = "#94a3b8"
TEXT_HEAD  = "#7dd3fc"
BORDER_CLR = "#374151"
BORDER_FOC = "#1f538d"

WILAYA_LIST = [
    "Adrar","Chlef","Laghouat","Oum El Bouaghi","Batna","Béjaïa","Biskra",
    "Béchar","Blida","Bouira","Tamanrasset","Tébessa","Tlemcen","Tiaret",
    "Tizi Ouzou","Alger","Djelfa","Jijel","Sétif","Saïda","Skikda",
    "Sidi Bel Abbès","Annaba","Guelma","Constantine","Médéa","Mostaganem",
    "M'Sila","Mascara","Ouargla","Oran","El Bayadh","Illizi","Bordj Bou Arréridj",
    "Boumerdès","El Tarf","Tindouf","Tissemsilt","El Oued","Khenchela",
    "Souk Ahras","Tipaza","Mila","Aïn Defla","Naâma","Aïn Témouchent",
    "Ghardaïa","Relizane","Timimoun","Bordj Badji Mokhtar","Ouled Djellal",
    "Béni Abbès","In Salah","In Guezzam","Touggourt","Djanet",
    "El M'Ghair","El Meniaa",
]

MED_CATEGORIES = [
    "Antibiotics", "Analgesics / Pain Relief", "Antipyretics",
    "Antivirals", "Antifungals", "Antiparasitics",
    "Cardiovascular", "Antidiabetics", "Antihypertensives",
    "Respiratory / Bronchodilators", "Gastrointestinal",
    "Dermatology", "Ophthalmology", "Neurology / CNS",
    "Oncology", "Immunology / Vaccines", "Vitamins & Supplements",
    "Hormones & Endocrinology", "Psychiatric / Psychotropic",
    "Surgical / Anaesthesia", "Paediatrics", "Gynaecology",
    "Medical Devices & Consumables", "Herbal / Traditional",
    "Other",
]


class SupplierView(ctk.CTkFrame):
    """Supplier Management Page."""

    def __init__(self, parent, controller=None):
        super().__init__(parent, fg_color=BG_DARK, corner_radius=0)
        self.controller = controller
        self._selected_supplier_id: int | None = None

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

        ctk.CTkButton(
            hdr, text="←  Back", width=90, height=36, corner_radius=8,
            fg_color="transparent", hover_color=ACCENT_BLUE,
            text_color=TEXT_MUTED, font=ctk.CTkFont("Helvetica", 13),
            command=lambda: self.controller and self.controller.navigate("dashboard")
        ).grid(row=0, column=0, padx=(16, 0), pady=14)

        title_f = ctk.CTkFrame(hdr, fg_color="transparent")
        title_f.grid(row=0, column=1, padx=20, sticky="w")

        ctk.CTkLabel(title_f, text="🏭  Supplier Management",
                     font=ctk.CTkFont("Helvetica", 20, "bold"),
                     text_color=TEXT_LIGHT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_f, text="Track suppliers · Medicine types · Contact details",
                     font=ctk.CTkFont("Helvetica", 11),
                     text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w")

    # ══════════════════════════ BODY ══════════════════════════════════

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=55)
        body.grid_columnconfigure(1, weight=0)   # divider
        body.grid_columnconfigure(2, weight=45)

        self._build_roster(body)
        ctk.CTkFrame(body, width=1, fg_color=BORDER_CLR).grid(
            row=0, column=1, sticky="ns", padx=10)
        self._build_right_panel(body)

    # ─────────────────────────── LEFT: Roster ─────────────────────────

    def _build_roster(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=16,
                             border_width=1, border_color=BORDER_CLR)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Title bar
        tb = ctk.CTkFrame(panel, fg_color="transparent")
        tb.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="ew")
        tb.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tb, text="🏭  Supplier Roster",
                     font=ctk.CTkFont("Helvetica", 15, "bold"),
                     text_color=TEXT_LIGHT).grid(row=0, column=0, sticky="w")

        self._count_lbl = ctk.CTkLabel(tb, text="0 suppliers",
                                       font=ctk.CTkFont("Helvetica", 11),
                                       text_color=TEXT_MUTED)
        self._count_lbl.grid(row=0, column=2, sticky="e")

        # Column headers
        hdr = ctk.CTkFrame(panel, fg_color=BG_HEADER, corner_radius=8)
        hdr.grid(row=1, column=0, padx=10, pady=(0, 4), sticky="ew")
        cols = [
            ("#",        3), ("Supplier / Company", 22), ("Phone",     12),
            ("Wilaya",   10), ("Medicine Types",     30), ("Products",   8),
            ("Actions",   8),
        ]
        for i, (lbl, w) in enumerate(cols):
            hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(hdr, text=lbl,
                         font=ctk.CTkFont("Helvetica", 11, "bold"),
                         text_color=TEXT_HEAD, anchor="w"
                         ).grid(row=0, column=i, padx=8, pady=8, sticky="w")

        self._rows_frame = ctk.CTkScrollableFrame(
            panel, fg_color="transparent",
            scrollbar_button_color=BORDER_CLR,
            scrollbar_button_hover_color=ACCENT_BLUE)
        self._rows_frame.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self._rows_frame.grid_columnconfigure(0, weight=1)

        self._empty_lbl = ctk.CTkLabel(
            self._rows_frame,
            text="🏭  No suppliers yet.\nAdd one using the form →",
            font=ctk.CTkFont("Helvetica", 13), text_color=TEXT_MUTED,
            justify="center")
        self._empty_lbl.grid(row=0, column=0, pady=60)

    def _add_roster_row(self, idx: int, sup: dict):
        bg  = BG_ODD if idx % 2 == 0 else BG_EVEN
        selected = (sup["supplier_id"] == self._selected_supplier_id)
        row_bg = ACCENT_BLUE if selected else bg

        row = ctk.CTkFrame(self._rows_frame, fg_color=row_bg,
                           corner_radius=8, height=46)
        row.grid(row=idx, column=0, padx=2, pady=2, sticky="ew")
        row.grid_propagate(False)

        weights = [3, 22, 12, 10, 30, 8, 8]
        for i, w in enumerate(weights):
            row.grid_columnconfigure(i, weight=w)

        def hover_in(e, r=row, b=row_bg):
            if r.cget("fg_color") != ACCENT_BLUE:
                r.configure(fg_color=BG_HOVER)
        def hover_out(e, r=row, b=row_bg):
            if r.cget("fg_color") != ACCENT_BLUE:
                r.configure(fg_color=b)

        row.bind("<Enter>", hover_in)
        row.bind("<Leave>", hover_out)
        row.bind("<Button-1>",
                 lambda e, sid=sup["supplier_id"]: self._on_row_click(sid))

        def lbl(text, col, color=TEXT_LIGHT, bold=False):
            w = ctk.CTkLabel(row, text=text, anchor="w",
                             font=ctk.CTkFont("Helvetica", 12,
                                              "bold" if bold else "normal"),
                             text_color=color)
            w.grid(row=0, column=col, padx=8, sticky="w")
            w.bind("<Button-1>",
                   lambda e, sid=sup["supplier_id"]: self._on_row_click(sid))

        lbl(str(idx + 1),          0, TEXT_MUTED)
        name_text = sup["name"]
        if sup["company"]:
            name_text += f"\n  {sup['company']}"
        lbl(name_text,             1, TEXT_LIGHT, bold=True)
        lbl(sup["phone"] or "—",   2, TEXT_MUTED)
        lbl(sup["wilaya"] or "—",  3, TEXT_MUTED)

        # Medicine type tags — truncate if too long
        types_text = sup.get("types", "—")
        if len(types_text) > 40:
            types_text = types_text[:38] + "…"
        lbl(types_text, 4, ACCENT_TEAL)

        # Product count badge
        count = sup.get("product_count", 0)
        badge_f = ctk.CTkFrame(row, fg_color=BG_INPUT, corner_radius=6, height=26)
        badge_f.grid(row=0, column=5, padx=8, pady=10, sticky="w")
        ctk.CTkLabel(badge_f, text=f" {count} ",
                     font=ctk.CTkFont("Helvetica", 11, "bold"),
                     text_color=ACCENT_AMBER).pack(padx=2)

        # Delete button
        ctk.CTkButton(
            row, text="🗑", width=32, height=28, corner_radius=6,
            fg_color="transparent", hover_color="#3a1a1a",
            text_color=ACCENT_RED, font=ctk.CTkFont("Helvetica", 14),
            command=lambda sid=sup["supplier_id"], n=sup["name"]:
                self._on_delete_supplier(sid, n)
        ).grid(row=0, column=6, padx=6, pady=9)

    def _on_row_click(self, supplier_id: int):
        self._selected_supplier_id = supplier_id
        if self.controller:
            self.controller.on_select_supplier(supplier_id)

    def _on_delete_supplier(self, supplier_id, name):
        ok = messagebox.askyesno(
            "Confirm Delete",
            f"Delete supplier:\n\n  {name}\n\n"
            "All their medicine records will also be removed.\n"
            "This cannot be undone.",
            icon="warning"
        )
        if ok and self.controller:
            self.controller.on_delete_supplier(supplier_id, name)

    # ─────────────────────────── RIGHT PANEL ──────────────────────────

    def _build_right_panel(self, parent):
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=0, column=2, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_supplier_form(right)
        self._build_medicines_panel(right)

    # ── Add/Edit Supplier Form ─────────────────────────────────────

    def _build_supplier_form(self, parent):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=16,
                            border_width=1, border_color=BORDER_CLR)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        # Fixed title
        th = ctk.CTkFrame(card, fg_color="transparent")
        th.grid(row=0, column=0, padx=16, pady=(14, 0), sticky="ew")
        th.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(th, text="➕  Add New Supplier",
                     font=ctk.CTkFont("Helvetica", 14, "bold"),
                     text_color=TEXT_LIGHT).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(th, text="Fill in supplier contact and company details",
                     font=ctk.CTkFont("Helvetica", 10),
                     text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w")
        ctk.CTkFrame(th, height=1, fg_color=BORDER_CLR).grid(
            row=2, column=0, sticky="ew", pady=(8, 0))

        # Scrollable form content
        sf = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                    scrollbar_button_color=BORDER_CLR,
                                    scrollbar_button_hover_color=ACCENT_BLUE)
        sf.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        sf.grid_columnconfigure(0, weight=1)

        # Feedback
        self._form_msg = ctk.CTkLabel(sf, text="", height=28,
                                      font=ctk.CTkFont("Helvetica", 11),
                                      text_color=ACCENT_TEAL,
                                      fg_color="transparent")
        self._form_msg.grid(row=0, column=0, padx=14, pady=(8, 2), sticky="ew")

        self._fields: dict = {}
        r = 1

        def section(txt, row):
            ctk.CTkLabel(sf, text=txt,
                         font=ctk.CTkFont("Helvetica", 10, "bold"),
                         text_color=TEXT_MUTED
                         ).grid(row=row, column=0, padx=18, pady=(10, 2), sticky="w")

        def entry(key, ph, row, **kw):
            e = ctk.CTkEntry(sf, placeholder_text=ph, height=36,
                             fg_color=BG_INPUT, border_color=BORDER_CLR,
                             border_width=1, corner_radius=8,
                             text_color=TEXT_LIGHT,
                             placeholder_text_color=TEXT_MUTED, **kw)
            e.grid(row=row, column=0, padx=14, pady=(0, 4), sticky="ew")
            e.bind("<FocusIn>",  lambda ev, w=e: w.configure(border_color=BORDER_FOC))
            e.bind("<FocusOut>", lambda ev, w=e: w.configure(border_color=BORDER_CLR))
            self._fields[key] = e

        section("CONTACT PERSON", r); r += 1
        entry("name",    "Full name  (required)", r); r += 1
        entry("phone",   "Phone number",           r); r += 1
        entry("email",   "Email address",          r); r += 1

        section("COMPANY", r); r += 1
        entry("company", "Company / Lab name",    r); r += 1
        entry("address", "Street address",         r); r += 1

        # Wilaya dropdown
        ctk.CTkLabel(sf, text="WILAYA",
                     font=ctk.CTkFont("Helvetica", 10, "bold"),
                     text_color=TEXT_MUTED
                     ).grid(row=r, column=0, padx=18, pady=(10, 2), sticky="w")
        r += 1
        wilaya_menu = ctk.CTkOptionMenu(
            sf, values=WILAYA_LIST,
            fg_color=BG_INPUT, button_color=ACCENT_BLUE,
            button_hover_color="#2563ab", dropdown_fg_color=BG_CARD,
            dropdown_hover_color=ACCENT_BLUE,
            text_color=TEXT_LIGHT, dropdown_text_color=TEXT_LIGHT,
            font=ctk.CTkFont("Helvetica", 12), height=36,
        )
        wilaya_menu.set("Blida")
        wilaya_menu.grid(row=r, column=0, padx=14, pady=(0, 4), sticky="ew")
        self._fields["wilaya"] = wilaya_menu
        r += 1

        section("NOTES  (optional)", r); r += 1
        notes_box = ctk.CTkTextbox(sf, height=52, fg_color=BG_INPUT,
                                   border_color=BORDER_CLR, border_width=1,
                                   corner_radius=8, text_color=TEXT_LIGHT,
                                   font=ctk.CTkFont("Helvetica", 12))
        notes_box.grid(row=r, column=0, padx=14, pady=(0, 6), sticky="ew")
        notes_box.bind("<FocusIn>",  lambda e: notes_box.configure(border_color=BORDER_FOC))
        notes_box.bind("<FocusOut>", lambda e: notes_box.configure(border_color=BORDER_CLR))
        self._notes_box = notes_box
        r += 1

        ctk.CTkFrame(sf, height=1, fg_color=BORDER_CLR).grid(
            row=r, column=0, sticky="ew", padx=14, pady=(4, 10))
        r += 1

        btns = ctk.CTkFrame(sf, fg_color="transparent")
        btns.grid(row=r, column=0, padx=14, pady=(0, 18), sticky="ew")
        btns.grid_columnconfigure(0, weight=1)
        btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btns, text="↺  Clear", height=40, corner_radius=10,
                      fg_color=BG_INPUT, hover_color=BORDER_CLR,
                      text_color=TEXT_MUTED, font=ctk.CTkFont("Helvetica", 13),
                      command=self.clear_supplier_form
                      ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(btns, text="✔  Save Supplier", height=40, corner_radius=10,
                      fg_color=ACCENT_TEAL, hover_color="#26a066",
                      text_color="white", font=ctk.CTkFont("Helvetica", 13, "bold"),
                      command=self._on_save_supplier
                      ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    # ── Medicine Types Panel ───────────────────────────────────────

    def _build_medicines_panel(self, parent):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=16,
                            border_width=1, border_color=BORDER_CLR)
        card.grid(row=1, column=0, sticky="nsew", pady=(0, 0))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        # Title
        th = ctk.CTkFrame(card, fg_color="transparent")
        th.grid(row=0, column=0, padx=16, pady=(14, 0), sticky="ew")
        th.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(th, text="💊  Medicine Types Supplied",
                     font=ctk.CTkFont("Helvetica", 13, "bold"),
                     text_color=TEXT_LIGHT).grid(row=0, column=0, sticky="w")

        self._med_panel_hint = ctk.CTkLabel(
            th, text="← Select a supplier to manage their products",
            font=ctk.CTkFont("Helvetica", 10), text_color=TEXT_MUTED)
        self._med_panel_hint.grid(row=1, column=0, sticky="w", pady=(2, 0))

        ctk.CTkFrame(th, height=1, fg_color=BORDER_CLR).grid(
            row=2, column=0, sticky="ew", pady=(8, 0))

        # Compact add-medicine-type row
        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.grid(row=1, column=0, padx=14, pady=(10, 6), sticky="ew")
        add_row.grid_columnconfigure(0, weight=1)
        add_row.grid_columnconfigure(1, weight=1)
        add_row.grid_columnconfigure(2, weight=0)

        self._med_type_menu = ctk.CTkOptionMenu(
            add_row, values=MED_CATEGORIES,
            fg_color=BG_INPUT, button_color=ACCENT_BLUE,
            button_hover_color="#2563ab", dropdown_fg_color=BG_CARD,
            dropdown_hover_color=ACCENT_BLUE,
            text_color=TEXT_LIGHT, dropdown_text_color=TEXT_LIGHT,
            font=ctk.CTkFont("Helvetica", 11), height=32,
        )
        self._med_type_menu.set("Antibiotics")
        self._med_type_menu.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self._brand_entry = ctk.CTkEntry(
            add_row, placeholder_text="Brand names (optional)",
            fg_color=BG_INPUT, border_color=BORDER_CLR, border_width=1,
            corner_radius=8, height=32, text_color=TEXT_LIGHT,
            placeholder_text_color=TEXT_MUTED,
            font=ctk.CTkFont("Helvetica", 11))
        self._brand_entry.grid(row=0, column=1, padx=(0, 4), sticky="ew")

        ctk.CTkButton(
            add_row, text="＋", width=36, height=32, corner_radius=8,
            fg_color=ACCENT_TEAL, hover_color="#26a066",
            text_color="white", font=ctk.CTkFont("Helvetica", 15, "bold"),
            command=self._on_add_med_type
        ).grid(row=0, column=2)

        # List of current medicine types for selected supplier
        self._med_list = ctk.CTkScrollableFrame(
            card, fg_color="transparent", height=120,
            scrollbar_button_color=BORDER_CLR,
            scrollbar_button_hover_color=ACCENT_BLUE)
        self._med_list.grid(row=2, column=0, padx=10, pady=(0, 12), sticky="nsew")
        self._med_list.grid_columnconfigure(0, weight=1)

        self._med_empty = ctk.CTkLabel(
            self._med_list,
            text="No medicine types added yet.",
            font=ctk.CTkFont("Helvetica", 11), text_color=TEXT_MUTED)
        self._med_empty.grid(row=0, column=0, pady=20)

    def _on_add_med_type(self):
        if not self._selected_supplier_id:
            self.show_form_message("Select a supplier first.", success=False)
            return
        if self.controller:
            self.controller.on_add_supplier_medicine({
                "supplier_id":   self._selected_supplier_id,
                "medicine_type": self._med_type_menu.get(),
                "brand_names":   self._brand_entry.get().strip(),
            })

    def _on_save_supplier(self):
        if self.controller:
            self.controller.on_save_supplier(self.get_supplier_form_data())

    # ══════════════════════════ PUBLIC API ════════════════════════════

    def render_suppliers(self, suppliers: list):
        """Populate the roster table."""
        for w in self._rows_frame.winfo_children():
            w.destroy()

        count = len(suppliers)
        self._count_lbl.configure(text=f"{count} supplier{'s' if count != 1 else ''}")

        if not suppliers:
            self._empty_lbl = ctk.CTkLabel(
                self._rows_frame,
                text="🏭  No suppliers yet.\nAdd one using the form →",
                font=ctk.CTkFont("Helvetica", 13),
                text_color=TEXT_MUTED, justify="center")
            self._empty_lbl.grid(row=0, column=0, pady=60)
            return

        for i, sup in enumerate(suppliers):
            self._add_roster_row(i, sup)

    def render_supplier_medicines(self, medicines: list, supplier_name: str = ""):
        """Populate the medicine-types list for the selected supplier."""
        for w in self._med_list.winfo_children():
            w.destroy()

        if supplier_name:
            self._med_panel_hint.configure(
                text=f"Products supplied by  {supplier_name}",
                text_color=ACCENT_TEAL)
        else:
            self._med_panel_hint.configure(
                text="← Select a supplier to manage their products",
                text_color=TEXT_MUTED)

        if not medicines:
            ctk.CTkLabel(self._med_list,
                         text="No medicine types added yet.",
                         font=ctk.CTkFont("Helvetica", 11),
                         text_color=TEXT_MUTED
                         ).grid(row=0, column=0, pady=20)
            return

        for i, med in enumerate(medicines):
            bg = BG_ODD if i % 2 == 0 else BG_EVEN
            row = ctk.CTkFrame(self._med_list, fg_color=bg, corner_radius=8, height=38)
            row.grid(row=i, column=0, padx=2, pady=2, sticky="ew")
            row.grid_propagate(False)
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=2)
            row.grid_columnconfigure(2, weight=0)

            ctk.CTkLabel(row, text=f"💊  {med['medicine_type']}",
                         font=ctk.CTkFont("Helvetica", 12, "bold"),
                         text_color=ACCENT_TEAL, anchor="w"
                         ).grid(row=0, column=0, padx=10, sticky="w")

            brands = med.get("brand_names", "")
            if brands:
                ctk.CTkLabel(row, text=brands,
                             font=ctk.CTkFont("Helvetica", 11),
                             text_color=TEXT_MUTED, anchor="w"
                             ).grid(row=0, column=1, padx=4, sticky="w")

            ctk.CTkButton(
                row, text="✕", width=28, height=26, corner_radius=6,
                fg_color="transparent", hover_color="#3a1a1a",
                text_color=ACCENT_RED, font=ctk.CTkFont("Helvetica", 13),
                command=lambda rid=med["id"], sid=med["supplier_id"]:
                    self._confirm_delete_med(rid, sid, med["medicine_type"])
            ).grid(row=0, column=2, padx=6, pady=6)

    def _confirm_delete_med(self, row_id, supplier_id, med_type):
        ok = messagebox.askyesno(
            "Remove Medicine Type",
            f"Remove  '{med_type}'  from this supplier?")
        if ok and self.controller:
            self.controller.on_delete_supplier_medicine(row_id, supplier_id)

    def show_form_message(self, msg: str, success: bool = True):
        color = ACCENT_TEAL if success else ACCENT_RED
        bg    = "#1a3a2e"   if success else "#3a1a1a"
        icon  = "✔  "       if success else "✘  "
        self._form_msg.configure(
            text=f"{icon}{msg}", text_color=color, fg_color=bg)
        self.after(4000, lambda: self._form_msg.configure(
            text="", fg_color="transparent"))

    def clear_supplier_form(self):
        for key, w in self._fields.items():
            if isinstance(w, ctk.CTkEntry):
                w.delete(0, "end")
            elif isinstance(w, ctk.CTkOptionMenu):
                w.set("Blida")
        self._notes_box.delete("1.0", "end")
        self._form_msg.configure(text="", fg_color="transparent")

    def get_supplier_form_data(self) -> dict:
        return {
            "name":    self._fields["name"].get().strip(),
            "phone":   self._fields["phone"].get().strip(),
            "email":   self._fields["email"].get().strip(),
            "company": self._fields["company"].get().strip(),
            "address": self._fields["address"].get().strip(),
            "wilaya":  self._fields["wilaya"].get(),
            "notes":   self._notes_box.get("1.0", "end").strip(),
        }