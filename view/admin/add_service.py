"""
views/admin/medicine_list.py
-----------------------------
Medicine List View — Smart Pharmacy Management System (Algeria).
Pure UI layer: search bar, scrollable table, per-row Edit/Delete actions.

MVC contract
------------
  Controller sets:  self.controller = <ControllerInstance>
  Controller calls: view.render_medicines(list[dict])
                    view.show_loading(bool)
  View calls back:  controller.on_edit_medicine(barcode)
                    controller.on_delete_medicine(barcode)
                    controller.on_search(query)
                    controller.on_refresh()
"""

import customtkinter as ctk

# ═══════════════════════════ COLOUR PALETTE ══════════════════════════════
# Strict 6-digit hex only — NO alpha suffixes to prevent TclError.

BG_MAIN       = "#242424"   # Main window / outer background
BG_TOPBAR     = "#1e1e1e"   # Top-bar strip
BG_CARD       = "#2d2d2d"   # Table container card
BG_ROW_ODD    = "#2a2a2a"   # Odd table rows
BG_ROW_EVEN   = "#323232"   # Even table rows (subtle stripe)
BG_ROW_HOVER  = "#3a3a3a"   # Row highlight on mouse-enter
BG_HEADER_ROW = "#1a1a2e"   # Column-header row
BG_INPUT      = "#1e1e2e"   # Search entry background
BG_BADGE_LOW  = "#3b1a1a"   # Low-stock badge background
BG_BADGE_OK   = "#1a3b2a"   # In-stock badge background
BG_BADGE_EXP  = "#3b2e1a"   # Expiring-soon badge background

ACCENT_BLUE   = "#1f538d"   # Primary accent (Edit button, active states)
ACCENT_TEAL   = "#2fa572"   # Secondary accent (header icon, success)
ACCENT_AMBER  = "#f59e0b"   # Warning (low stock, expiring soon)
ACCENT_RED    = "#ef4444"   # Danger (delete button, expired)

TEXT_LIGHT    = "#e2e8f0"   # Primary text
TEXT_MUTED    = "#94a3b8"   # Secondary / placeholder text
TEXT_HEADER   = "#7dd3fc"   # Column header labels
BORDER_CLR    = "#374151"   # Subtle card border
BORDER_FOCUS  = "#1f538d"   # Search field focus border

# ═══════════════════════════ COLUMN SCHEMA ═══════════════════════════════
# (header_label, dict_key, min_width, anchor)
COLUMNS = [
    ("Barcode",       "barcode",      110, "w"),
    ("Product Name",  "name",         170, "w"),
    ("Generic Name",  "generic_name", 150, "w"),
    ("Price (DZD)",   "price",         90, "e"),
    ("Stock",         "quantity",      70, "center"),
    ("Expiry Date",   "expiry_date",  110, "center"),
    ("Actions",       None,           120, "center"),
]

# Low-stock threshold (rows below this qty get amber badge)
LOW_STOCK_QTY = 10


# ═══════════════════════════ MAIN VIEW CLASS ═════════════════════════════

class MedicineListView(ctk.CTkFrame):
    """
    Scrollable medicine catalogue with search, refresh, and per-row actions.
    Designed to slot directly into the Admin Dashboard's main content area.
    """

    def __init__(self, parent, controller=None):
        super().__init__(parent, fg_color=BG_MAIN, corner_radius=0)
        self.controller = controller

        # Track row-frame references so hover bindings can update them
        self._row_frames: list[ctk.CTkFrame] = []
        self._row_colors: list[str] = []       # original bg per row
        self._row_data:   dict[str, dict] = {} # barcode → full med dict (for edit/delete)
        self._is_loading = False

        # Fill the parent
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)    # table area expands
        self.grid_columnconfigure(0, weight=1)

        self._setup_header()
        self._setup_column_headers()
        self._setup_table()
        self._setup_status_bar()

    # ═══════════════════════ SECTION BUILDERS ════════════════════════════

    def _setup_header(self):
        """
        Top bar: back button, page title, search entry, and action buttons.
        Sits in row=0 of the outer frame.

        Column layout inside bar:
          col 0 — Back button       (fixed width)
          col 1 — Page title block  (fixed width)
          col 2 — Search entry      (weight=1, stretches)
          col 3 — Refresh / Add New (fixed width)
        """
        bar = ctk.CTkFrame(self, fg_color=BG_TOPBAR, corner_radius=0, height=72)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(2, weight=1)   # search entry stretches

        # ── col 0: Back button ───────────────────────────────────────────
        ctk.CTkButton(
            bar,
            text="⬅",
            width=40, height=40,
            corner_radius=20,
            fg_color="transparent",
            hover_color="#3a3a3a",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont("Helvetica", 16),
            command=self._on_back_click,
        ).grid(row=0, column=0, padx=(16, 4), pady=16)

        # ── col 1: Page title ────────────────────────────────────────────
        title_block = ctk.CTkFrame(bar, fg_color="transparent")
        title_block.grid(row=0, column=1, padx=(4, 0), pady=12, sticky="w")

        ctk.CTkLabel(
            title_block,
            text="💊  Medicine Catalogue",
            font=ctk.CTkFont("Helvetica", 20, "bold"),
            text_color=TEXT_LIGHT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_block,
            text="Browse, search and manage your pharmacy stock",
            font=ctk.CTkFont("Helvetica", 10),
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w")

        # ── col 2: Search entry ──────────────────────────────────────────
        search_frame = ctk.CTkFrame(bar, fg_color="transparent")
        search_frame.grid(row=0, column=2, padx=24, pady=16, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍   Search by name, barcode or generic name…",
            height=40,
            corner_radius=12,
            fg_color=BG_INPUT,
            border_color=BORDER_CLR,
            text_color=TEXT_LIGHT,
            placeholder_text_color=TEXT_MUTED,
            font=ctk.CTkFont("Helvetica", 13),
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")

        # Trigger search on every keystroke
        self.search_entry.bind("<KeyRelease>", self._on_search_keyrelease)
        # Highlight border on focus
        self.search_entry.bind("<FocusIn>",
            lambda e: self.search_entry.configure(border_color=BORDER_FOCUS))
        self.search_entry.bind("<FocusOut>",
            lambda e: self.search_entry.configure(border_color=BORDER_CLR))

        # ── col 3: Right-side buttons ────────────────────────────────────
        btn_bar = ctk.CTkFrame(bar, fg_color="transparent")
        btn_bar.grid(row=0, column=3, padx=(0, 20), pady=16)

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            btn_bar,
            text="⟳  Refresh",
            width=110, height=40,
            corner_radius=12,
            fg_color=ACCENT_BLUE,
            hover_color="#2563ab",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont("Helvetica", 13, "bold"),
            command=self._on_refresh_click,
        )
        self.refresh_btn.grid(row=0, column=0, padx=(0, 8))

        # Add New Medicine shortcut button
        self.add_btn = ctk.CTkButton(
            btn_bar,
            text="＋  Add New",
            width=110, height=40,
            corner_radius=12,
            fg_color=ACCENT_TEAL,
            hover_color="#27916a",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont("Helvetica", 13, "bold"),
            command=self._on_add_click,
        )
        self.add_btn.grid(row=0, column=1)

    def _setup_column_headers(self):
        """
        Fixed (non-scrolling) column header row.
        Sits in row=1 of the outer frame, directly above the scrollable table.
        """
        header_bg = ctk.CTkFrame(
            self, fg_color=BG_HEADER_ROW, corner_radius=0, height=38
        )
        header_bg.grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 0))
        header_bg.grid_propagate(False)
        header_bg.grid_columnconfigure(len(COLUMNS) - 1, weight=1)

        for col_idx, (label, _, min_w, anchor) in enumerate(COLUMNS):
            ctk.CTkLabel(
                header_bg,
                text=label,
                font=ctk.CTkFont("Helvetica", 11, "bold"),
                text_color=TEXT_HEADER,
                anchor=anchor,
                width=min_w,
            ).grid(row=0, column=col_idx, padx=(10, 4), pady=8, sticky="ew")

    def _setup_table(self):
        """
        Scrollable frame that holds the data rows.
        Sits in row=2 (weight=1) so it fills all remaining vertical space.
        """
        # Outer card wraps the scrollable area for the rounded border
        self.table_card = ctk.CTkFrame(
            self,
            fg_color=BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER_CLR,
        )
        self.table_card.grid(row=2, column=0, sticky="nsew",
                              padx=16, pady=(4, 8))
        self.table_card.grid_rowconfigure(0, weight=1)
        self.table_card.grid_columnconfigure(0, weight=1)

        # Scrollable inner container
        self.table_frame = ctk.CTkScrollableFrame(
            self.table_card,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=BORDER_CLR,
            scrollbar_button_hover_color=ACCENT_BLUE,
        )
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.table_frame.grid_columnconfigure(len(COLUMNS) - 1, weight=1)

        # Progress bar (hidden by default, shown during loading)
        self.progress_bar = ctk.CTkProgressBar(
            self.table_card,
            orientation="horizontal",
            mode="indeterminate",
            fg_color=BG_CARD,
            progress_color=ACCENT_BLUE,
            height=4,
            corner_radius=0,
        )
        # Not gridded yet — shown only when loading

        # Placeholder label shown when table is empty
        self.empty_label = ctk.CTkLabel(
            self.table_frame,
            text="🔬  No medicines found.\nUse 'Add New' to register your first product.",
            font=ctk.CTkFont("Helvetica", 14),
            text_color=TEXT_MUTED,
            justify="center",
        )

    def _setup_status_bar(self):
        """
        Thin status strip at the bottom: row count + last-updated hint.
        Sits in row=3 of the outer frame.
        """
        bar = ctk.CTkFrame(self, fg_color=BG_TOPBAR,
                            corner_radius=0, height=28)
        bar.grid(row=3, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        self.count_label = ctk.CTkLabel(
            bar,
            text="0 medicines",
            font=ctk.CTkFont("Helvetica", 10),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.count_label.grid(row=0, column=0, padx=20, sticky="w")

        self.status_label = ctk.CTkLabel(
            bar,
            text="",
            font=ctk.CTkFont("Helvetica", 10),
            text_color=TEXT_MUTED,
            anchor="e",
        )
        self.status_label.grid(row=0, column=2, padx=20, sticky="e")

    # ═══════════════════════ ROW BUILDER ═════════════════════════════════

    def _add_row(self, med_data: dict, row_index: int):
        """
        Build one table row from a medicine data dictionary.

        Expected keys (all strings unless noted):
            barcode, name, generic_name, price, quantity (int), expiry_date

        The row registers <Enter>/<Leave> bindings for the hover effect and
        wires Edit / Delete buttons to controller callbacks.
        """
        # Alternate row colours for readability
        base_color = BG_ROW_ODD if row_index % 2 == 0 else BG_ROW_EVEN

        row_frame = ctk.CTkFrame(
            self.table_frame,
            fg_color=base_color,
            corner_radius=8,
            border_width=0,
        )
        row_frame.grid(row=row_index, column=0, sticky="ew",
                       padx=4, pady=2, ipady=2)

        # Let each column inside the row keep its min width
        for col_idx, (_, __, min_w, ___) in enumerate(COLUMNS):
            row_frame.grid_columnconfigure(col_idx, minsize=min_w)
        row_frame.grid_columnconfigure(len(COLUMNS) - 1, weight=1)

        # ── Hover effect binding ─────────────────────────────────────────
        def _on_enter(e, f=row_frame):
            f.configure(fg_color=BG_ROW_HOVER)

        def _on_leave(e, f=row_frame, c=base_color):
            f.configure(fg_color=c)

        row_frame.bind("<Enter>", _on_enter)
        row_frame.bind("<Leave>", _on_leave)

        # ── Cell helpers ─────────────────────────────────────────────────
        def _cell(text, col, anchor="w", text_col=TEXT_LIGHT,
                  bold=False, width=None):
            """Place a simple text label in the given column."""
            lbl = ctk.CTkLabel(
                row_frame,
                text=str(text),
                font=ctk.CTkFont("Helvetica", 12, "bold" if bold else "normal"),
                text_color=text_col,
                anchor=anchor,
                width=width or COLUMNS[col][2],
            )
            lbl.grid(row=0, column=col, padx=(10, 4), pady=6, sticky="ew")
            # Propagate hover to child labels too
            lbl.bind("<Enter>", _on_enter)
            lbl.bind("<Leave>", _on_leave)
            return lbl

        # col 0 — Barcode (monospace-style, muted)
        _cell(med_data.get("barcode", "—"), 0, text_col=TEXT_MUTED)

        # col 1 — Product Name (bold)
        _cell(med_data.get("name", "—"), 1, bold=True)

        # col 2 — Generic Name
        _cell(med_data.get("generic_name", "—"), 2, text_col=TEXT_MUTED)

        # col 3 — Price (right-aligned, teal accent)
        _cell(f"{med_data.get('price', '0')} DZD", 3,
              anchor="e", text_col=ACCENT_TEAL)

        # col 4 — Stock quantity with colour badge
        qty = int(med_data.get("quantity", 0))
        stock_text  = str(qty)
        stock_color = ACCENT_AMBER if qty <= LOW_STOCK_QTY else ACCENT_TEAL
        _cell(stock_text, 4, anchor="center", text_col=stock_color, bold=True)

        # col 5 — Expiry Date
        expiry_str   = med_data.get("expiry_date", "—")
        expiry_color = TEXT_LIGHT
        if expiry_str.lower() in ("expired", "—"):
            expiry_color = ACCENT_RED
        _cell(expiry_str, 5, anchor="center", text_col=expiry_color)

        # col 6 — Action buttons (Edit + Delete)
        self._add_action_buttons(row_frame, med_data, col=6,
                                  hover_enter=_on_enter, hover_leave=_on_leave)

        # Store for potential bulk operations and edit lookup
        self._row_frames.append(row_frame)
        self._row_colors.append(base_color)
        self._row_data[str(med_data.get("barcode", ""))] = med_data

    def _add_action_buttons(self, parent: ctk.CTkFrame, med_data: dict,
                             col: int, hover_enter, hover_leave):
        """
        Place Edit and Delete buttons in the Actions column.
        Both buttons propagate the row hover event so the row stays
        highlighted while the cursor is over a button.
        """
        barcode = med_data.get("barcode", "")

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=0, column=col, padx=(4, 8), pady=4, sticky="e")
        btn_frame.bind("<Enter>", hover_enter)
        btn_frame.bind("<Leave>", hover_leave)

        # Edit button ── blue, pencil icon
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="✏  Edit",
            width=72, height=30,
            corner_radius=8,
            fg_color=ACCENT_BLUE,
            hover_color="#2563ab",
            text_color=TEXT_LIGHT,
            font=ctk.CTkFont("Helvetica", 11, "bold"),
            command=lambda b=barcode: self._on_edit_click(b),
        )
        edit_btn.grid(row=0, column=0, padx=(0, 6))
        edit_btn.bind("<Enter>", hover_enter)
        edit_btn.bind("<Leave>", hover_leave)

        # Delete button ── red, trash icon
        del_btn = ctk.CTkButton(
            btn_frame,
            text="🗑  Del",
            width=72, height=30,
            corner_radius=8,
            fg_color=BG_CARD,
            hover_color=ACCENT_RED,
            border_width=1,
            border_color=ACCENT_RED,
            text_color=ACCENT_RED,
            font=ctk.CTkFont("Helvetica", 11, "bold"),
            command=lambda b=barcode: self._on_delete_click(b),
        )
        del_btn.grid(row=0, column=1)
        del_btn.bind("<Enter>", hover_enter)
        del_btn.bind("<Leave>", hover_leave)

    # ═══════════════════════ CALLBACK STUBS ══════════════════════════════

    def _on_back_click(self):
        """Navigate back to the Dashboard via the controller."""
        if self.controller and hasattr(self.controller, "navigate"):
            self.controller.navigate("dashboard")

    def _on_search_keyrelease(self, event=None):
        """Relay search query to controller on every keystroke."""
        query = self.search_entry.get().strip()
        if self.controller and hasattr(self.controller, "on_search"):
            self.controller.on_search(query)

    def _on_refresh_click(self):
        if self.controller and hasattr(self.controller, "on_refresh"):
            self.controller.on_refresh()

    def _on_add_click(self):
        """Navigate to the Add Medicine form via the controller router."""
        if self.controller and hasattr(self.controller, "navigate"):
            self.controller.navigate("add_medicine")

    def _on_edit_click(self, barcode: str):
        """Pass the full row data dict to the controller so the form can be pre-filled."""
        if self.controller and hasattr(self.controller, "open_edit_medicine"):
            # Find the med_data for this barcode from the stored row data
            self.controller.open_edit_medicine(self._row_data.get(barcode, {"barcode": barcode}))

    def _on_delete_click(self, barcode: str):
        """Show a confirmation dialog before deleting."""
        from tkinter import messagebox
        name = self._row_data.get(barcode, {}).get("name", barcode)
        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete:\n\n  {name}  ({barcode})?\n\nThis cannot be undone.",
            icon="warning"
        )
        if confirmed and self.controller and hasattr(self.controller, "on_delete_medicine"):
            self.controller.on_delete_medicine(barcode)

    # ═══════════════════════ PUBLIC API (Controller) ═════════════════════

    def render_medicines(self, medicines_list: list[dict]):
        """
        Clear the current table and populate it with a fresh data set.

        Called by the controller after fetching from the database.

        Parameters
        ----------
        medicines_list : list[dict]
            Each dict must contain at minimum:
            {barcode, name, generic_name, price, quantity, expiry_date}
        """
        # 1. Destroy all existing row widgets
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self._row_frames.clear()
        self._row_colors.clear()
        self._row_data.clear()

        # 2. Hide or show the empty-state label
        if not medicines_list:
            self.empty_label = ctk.CTkLabel(
                self.table_frame,
                text="🔬  No medicines found.\nUse 'Add New' to register your first product.",
                font=ctk.CTkFont("Helvetica", 14),
                text_color=TEXT_MUTED,
                justify="center",
            )
            self.empty_label.grid(row=0, column=0, pady=60)
            self.count_label.configure(text="0 medicines")
            return

        # 3. Build rows
        for idx, med in enumerate(medicines_list):
            self._add_row(med, row_index=idx)

        # 4. Update status bar
        total = len(medicines_list)
        low   = sum(1 for m in medicines_list
                    if int(m.get("quantity", 0)) <= LOW_STOCK_QTY)
        summary = f"{total} medicine{'s' if total != 1 else ''}"
        if low:
            summary += f"  ·  ⚠ {low} low stock"
        self.count_label.configure(text=summary)
        self.status_label.configure(text="Last updated just now")

    def show_loading(self, loading: bool):
        """
        Show / hide an indeterminate progress bar and disable interactive
        controls while data is being fetched.

        Parameters
        ----------
        loading : bool
            True  → show spinner, disable buttons
            False → hide spinner, re-enable buttons
        """
        self._is_loading = loading

        if loading:
            # Mount progress bar directly below column headers (above card)
            self.progress_bar.grid(row=1, column=0, sticky="ew",
                                    padx=16, pady=(0, 0))
            self.progress_bar.start()
            self.refresh_btn.configure(state="disabled", text="Loading…")
            self.search_entry.configure(state="disabled")
            self.add_btn.configure(state="disabled")
            self.configure(cursor="watch")
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_forget()
            self.refresh_btn.configure(state="normal", text="⟳  Refresh")
            self.search_entry.configure(state="normal")
            self.add_btn.configure(state="normal")
            self.configure(cursor="")

    def get_search_query(self) -> str:
        """Return the current text in the search box (controller may poll this)."""
        return self.search_entry.get().strip()

    def clear_search(self):
        """Reset the search field to empty."""
        self.search_entry.delete(0, "end")
        self.search_entry.configure(border_color=BORDER_CLR)


# ═══════════════════════════ STANDALONE DEMO ═════════════════════════════
# Run this file directly to preview the view with sample data.
# python medicine_list.py

if __name__ == "__main__":
    import random, datetime

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    SAMPLE_NAMES = [
        ("Paracetamol 500mg",   "Paracétamol"),
        ("Amoxicilline 1g",     "Amoxicilline"),
        ("Ibuprofen 400mg",     "Ibuprofène"),
        ("Metformine 850mg",    "Metformine"),
        ("Oméprazole 20mg",     "Oméprazole"),
        ("Amlodipine 5mg",      "Amlodipine"),
        ("Atorvastatine 20mg",  "Atorvastatine"),
        ("Salbutamol 100mcg",   "Salbutamol"),
        ("Cetirizine 10mg",     "Cétirizine"),
        ("Azithromycine 500mg", "Azithromycine"),
    ]

    def _random_expiry():
        delta = random.randint(-30, 500)
        d = datetime.date.today() + datetime.timedelta(days=delta)
        return d.strftime("%d/%m/%Y")

    sample_data = [
        {
            "barcode":      f"34009{random.randint(100000, 999999)}",
            "name":         name,
            "generic_name": generic,
            "price":        random.randint(80, 1200),
            "quantity":     random.randint(0, 120),
            "expiry_date":  _random_expiry(),
        }
        for name, generic in SAMPLE_NAMES
    ]

    root = ctk.CTk()
    root.title("Medicine List — Demo")
    root.geometry("1100x680")
    root.minsize(800, 500)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    view = MedicineListView(root)
    view.render_medicines(sample_data)

    root.mainloop()