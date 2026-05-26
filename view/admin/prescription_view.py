# view/admin/prescription_view.py
"""
PrescriptionView — Prescription management
Style : Light / Professional

Layout:
  ├── Sidebar (col 0 fixed)
  └── Content:
        ├── Top bar : title + date + "New Prescription" button
        └── Full-width Rx history table (all patients, self-loading)

Popups:
  • NewPrescriptionWindow  — patient picker + medicine rows + notes
  • RxDetailWindow         — read-only view of a saved prescription
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
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
RX_GREEN       = "#065F46"
RX_BG          = "#ECFDF5"

FONT = "Helvetica"

FREQUENCY_OPTIONS = [
    "Once daily", "Twice daily", "3× daily", "4× daily",
    "Every 6 hours", "Every 8 hours", "Every 12 hours",
    "As needed", "Before meals", "After meals", "At bedtime",
]
DURATION_OPTIONS = [
    "3 days", "5 days", "7 days", "10 days", "14 days",
    "1 month", "2 months", "3 months", "Ongoing", "As directed",
]


# ══════════════════════════════════════════════════════════════════════════════
# POPUP — New Prescription
# ══════════════════════════════════════════════════════════════════════════════

class NewPrescriptionWindow(ctk.CTkToplevel):

    def __init__(self, parent_view, controller, on_saved=None):
        super().__init__()
        self.parent_view    = parent_view
        self.controller     = controller
        self.on_saved       = on_saved
        self._selected_patient = None
        self._all_patients  = []
        self._medicine_rows = []

        self.title("📋  New Prescription")
        self.geometry("680x780")
        self.resizable(True, True)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build()
        self._load_patients()

    # ── Data ──────────────────────────────────────────────────────────────

    def _load_patients(self):
        try:
            fn = (getattr(self.controller.patient_model,
                          "get_all_patients", None) or
                  getattr(self.controller.patient_model, "get_all", None))
            rows = fn() if fn else []
        except Exception:
            rows = []
        keys = ["patient_id", "full_name", "phone", "gender",
                "date_of_birth", "wilaya"]
        self._all_patients = []
        for r in (rows or []):
            self._all_patients.append(
                r if isinstance(r, dict) else dict(zip(keys, r)))
        self._populate_pt_list(self._all_patients)

    # ── Build ─────────────────────────────────────────────────────────────

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        self._scroll = scroll

        # Header
        hdr = ctk.CTkFrame(scroll, fg_color=RX_BG,
                           corner_radius=10,
                           border_width=1, border_color="#A7F3D0")
        hdr.grid(row=0, column=0, sticky="ew",
                 padx=20, pady=(20, 14))
        ctk.CTkLabel(hdr, text="📋  New Prescription",
                     font=ctk.CTkFont(FONT, 16, "bold"),
                     text_color=RX_GREEN
                     ).pack(anchor="w", padx=20, pady=12)

        # ── Patient search ────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="Patient *",
                     font=ctk.CTkFont(FONT, 12, "bold"),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=1, column=0, sticky="w",
                            padx=20, pady=(0, 4))

        self._pt_search_var = ctk.StringVar()
        self._pt_search_var.trace_add("write", self._on_pt_search)
        ctk.CTkEntry(scroll, textvariable=self._pt_search_var,
                     placeholder_text="Type name or phone…",
                     font=ctk.CTkFont(FONT, 13),
                     fg_color=PANEL_ALT,
                     border_width=1, border_color=BORDER,
                     text_color=TEXT_PRIMARY, height=38
                     ).grid(row=2, column=0, sticky="ew",
                            padx=20, pady=(0, 4))

        self._pt_badge = ctk.CTkLabel(
            scroll, text="No patient selected",
            font=ctk.CTkFont(FONT, 12),
            text_color=TEXT_SECONDARY, anchor="w")
        self._pt_badge.grid(row=3, column=0, sticky="w",
                            padx=20, pady=(0, 4))

        self._pt_list = ctk.CTkScrollableFrame(
            scroll, fg_color=PANEL_BG,
            border_width=1, border_color=BORDER,
            height=130, corner_radius=8)
        self._pt_list.grid(row=4, column=0, sticky="ew",
                           padx=20, pady=(0, 14))
        self._pt_list.grid_columnconfigure(0, weight=1)

        # Divider
        ctk.CTkFrame(scroll, fg_color=BORDER, height=1
                     ).grid(row=5, column=0, sticky="ew",
                            padx=20, pady=(0, 14))

        # ── Medicines section ─────────────────────────────────────────────
        med_hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        med_hdr.grid(row=6, column=0, sticky="ew",
                     padx=20, pady=(0, 8))
        med_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(med_hdr, text="💊  Medicines",
                     font=ctk.CTkFont(FONT, 13, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            med_hdr, text="＋  Add Medicine",
            width=130, height=32,
            font=ctk.CTkFont(FONT, 12, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            corner_radius=8,
            command=self._add_medicine_row
        ).grid(row=0, column=1, sticky="e")

        # Medicine rows container
        self._med_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._med_frame.grid(row=7, column=0, sticky="ew", padx=20)
        self._med_frame.grid_columnconfigure(0, weight=1)

        self._med_empty = ctk.CTkLabel(
            self._med_frame,
            text="Click  '＋ Add Medicine'  to start writing.",
            font=ctk.CTkFont(FONT, 12),
            text_color=TEXT_SECONDARY)
        self._med_empty.grid(row=0, column=0, pady=20)

        # ── Notes ─────────────────────────────────────────────────────────
        ctk.CTkFrame(scroll, fg_color=BORDER, height=1
                     ).grid(row=8, column=0, sticky="ew",
                            padx=20, pady=(14, 10))

        ctk.CTkLabel(scroll, text="General Notes",
                     font=ctk.CTkFont(FONT, 12, "bold"),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=9, column=0, sticky="w",
                            padx=20, pady=(0, 4))

        self._notes_box = ctk.CTkTextbox(
            scroll, height=70,
            font=ctk.CTkFont(FONT, 12),
            fg_color=PANEL_ALT,
            border_width=1, border_color=BORDER,
            text_color=TEXT_PRIMARY)
        self._notes_box.grid(row=10, column=0, sticky="ew",
                              padx=20, pady=(0, 8))

        # Feedback
        self._msg_lbl = ctk.CTkLabel(
            scroll, text="",
            font=ctk.CTkFont(FONT, 12),
            text_color=DANGER, anchor="w")
        self._msg_lbl.grid(row=11, column=0, sticky="w",
                           padx=20, pady=(0, 4))

        # Buttons
        br = ctk.CTkFrame(scroll, fg_color="transparent")
        br.grid(row=12, column=0, sticky="ew",
                padx=20, pady=(4, 24))
        br.grid_columnconfigure(0, weight=1)
        br.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(br, text="💾  Save & Print PDF",
                      font=ctk.CTkFont(FONT, 13, "bold"),
                      fg_color=SUCCESS, hover_color="#15803D",
                      height=42, corner_radius=8,
                      command=self._submit
                      ).grid(row=0, column=0, sticky="ew",
                             padx=(0, 6))

        ctk.CTkButton(br, text="Cancel",
                      font=ctk.CTkFont(FONT, 13),
                      fg_color=PANEL_ALT, hover_color=BORDER,
                      text_color=TEXT_PRIMARY,
                      height=42, corner_radius=8,
                      command=self.destroy
                      ).grid(row=0, column=1, sticky="ew",
                             padx=(6, 0))

    # ── Medicine row ──────────────────────────────────────────────────────

    def _add_medicine_row(self):
        if self._med_empty and self._med_empty.winfo_exists():
            self._med_empty.destroy()

        idx = len(self._medicine_rows)
        row_data = {}

        card = ctk.CTkFrame(self._med_frame, fg_color=PANEL_BG,
                            border_width=1, border_color=BORDER,
                            corner_radius=10)
        card.grid(row=idx, column=0, sticky="ew", pady=5)
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)
        row_data["frame"] = card

        # Row header with number + remove
        rh = ctk.CTkFrame(card, fg_color=PANEL_ALT, corner_radius=0)
        rh.grid(row=0, column=0, columnspan=2, sticky="ew")
        rh.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(rh, text=f"💊  Medicine #{idx + 1}",
                     font=ctk.CTkFont(FONT, 11, "bold"),
                     text_color=RX_GREEN, anchor="w"
                     ).grid(row=0, column=0, padx=12, pady=6,
                            sticky="w")

        ctk.CTkButton(rh, text="✕ Remove",
                      width=80, height=26,
                      font=ctk.CTkFont(FONT, 11),
                      fg_color=DANGER_LIGHT,
                      hover_color="#FECACA",
                      text_color=DANGER, corner_radius=6,
                      command=lambda c=card, d=row_data:
                          self._remove_medicine_row(c, d)
                      ).grid(row=0, column=1, padx=8, pady=6,
                             sticky="e")

        def labeled_entry(row, col, label, key, placeholder="",
                           colspan=1):
            fr = ctk.CTkFrame(card, fg_color="transparent")
            fr.grid(row=row, column=col, columnspan=colspan,
                    sticky="ew", padx=(12, 8), pady=4)
            fr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(fr, text=label,
                         font=ctk.CTkFont(FONT, 10, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            var = ctk.StringVar()
            ctk.CTkEntry(fr, textvariable=var,
                         placeholder_text=placeholder,
                         font=ctk.CTkFont(FONT, 12),
                         fg_color=PANEL_ALT,
                         border_width=1, border_color=BORDER,
                         text_color=TEXT_PRIMARY, height=32
                         ).grid(row=1, column=0, sticky="ew")
            row_data[key] = var

        def labeled_option(row, col, label, key, values,
                            colspan=1):
            fr = ctk.CTkFrame(card, fg_color="transparent")
            fr.grid(row=row, column=col, columnspan=colspan,
                    sticky="ew", padx=(12, 8), pady=4)
            fr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(fr, text=label,
                         font=ctk.CTkFont(FONT, 10, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            var = ctk.StringVar(value=values[0])
            ctk.CTkOptionMenu(fr, variable=var, values=values,
                              font=ctk.CTkFont(FONT, 11),
                              fg_color=PANEL_ALT,
                              button_color=ACCENT,
                              button_hover_color=ACCENT_HOVER,
                              dropdown_fg_color=PANEL_BG,
                              text_color=TEXT_PRIMARY, height=32
                              ).grid(row=1, column=0, sticky="ew")
            row_data[key] = var

        labeled_entry(1, 0, "Medicine Name *", "name",
                      "e.g. Amoxicillin")
        labeled_entry(1, 1, "Dosage", "dose", "e.g. 500mg")
        labeled_option(2, 0, "Frequency", "freq", FREQUENCY_OPTIONS)
        labeled_option(2, 1, "Duration",  "dur",  DURATION_OPTIONS)
        labeled_entry(3, 0, "Instructions", "instr",
                      "e.g. Take with food", colspan=2)

        self._medicine_rows.append(row_data)

    def _remove_medicine_row(self, card, row_data):
        card.destroy()
        if row_data in self._medicine_rows:
            self._medicine_rows.remove(row_data)

    # ── Patient list ──────────────────────────────────────────────────────

    def _on_pt_search(self, *_):
        q = self._pt_search_var.get().strip().lower()
        filtered = ([p for p in self._all_patients
                     if q in p.get("full_name", "").lower()
                     or q in p.get("phone", "").lower()]
                    if q else self._all_patients)
        self._populate_pt_list(filtered)

    def _populate_pt_list(self, patients):
        for w in self._pt_list.winfo_children():
            w.destroy()
        if not patients:
            ctk.CTkLabel(self._pt_list,
                         text="No patients found.",
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_SECONDARY
                         ).pack(pady=10)
            return
        for p in patients[:30]:
            label = (f"{p.get('full_name','—')}"
                     f"  ·  {p.get('phone','') or '—'}")
            ctk.CTkButton(
                self._pt_list, text=label,
                anchor="w", height=32,
                font=ctk.CTkFont(FONT, 12),
                fg_color="transparent",
                hover_color=ACCENT_LIGHT,
                text_color=TEXT_PRIMARY, corner_radius=6,
                command=lambda pt=p: self._pick(pt)
            ).pack(fill="x", padx=4, pady=1)

    def _pick(self, patient):
        self._selected_patient = patient
        self._pt_badge.configure(
            text=f"✓  {patient['full_name']}",
            text_color=SUCCESS)
        self._pt_search_var.set("")
        self._populate_pt_list([])

    # ── Submit ────────────────────────────────────────────────────────────

    def _collect_items(self):
        items = []
        for row in self._medicine_rows:
            name = row["name"].get().strip()
            if not name:
                continue
            items.append({
                "medicine_name": name,
                "dosage":        row["dose"].get().strip(),
                "frequency":     row["freq"].get(),
                "duration":      row["dur"].get(),
                "instructions":  row["instr"].get().strip(),
            })
        return items

    def _submit(self):
        if not self._selected_patient:
            self._msg_lbl.configure(
                text="Please select a patient first.")
            return
        items = self._collect_items()
        if not items:
            self._msg_lbl.configure(
                text="Add at least one medicine.")
            return
        data = {
            "patient_id":     self._selected_patient["patient_id"],
            "appointment_id": None,
            "notes":          self._notes_box.get("1.0", "end").strip(),
            "items":          items,
        }
        self.controller.on_create_prescription(data)
        if self.on_saved:
            self.after(300, self.on_saved)
        self.after(400, self.destroy)


# ══════════════════════════════════════════════════════════════════════════════
# POPUP — Rx Detail (read-only view)
# ══════════════════════════════════════════════════════════════════════════════

class RxDetailWindow(ctk.CTkToplevel):

    def __init__(self, rx: dict, items: list, controller=None):
        super().__init__()
        self.rx         = rx
        self.items      = items
        self.controller = controller
        patient = rx.get("patient_name", "Patient")
        self.title(f"📋  Rx #{rx.get('rx_id', 0):04d}  —  {patient}")
        self.geometry("480x600")
        self.resizable(True, True)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build(rx, items)

    def _build(self, rx, items):
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # Rx header card
        hdr = ctk.CTkFrame(scroll, fg_color=RX_BG,
                           border_width=1, border_color="#A7F3D0",
                           corner_radius=12)
        hdr.grid(row=0, column=0, sticky="ew",
                 padx=20, pady=(20, 14))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr, text="ℝ𝕩  PRESCRIPTION",
                     font=ctk.CTkFont(FONT, 18, "bold"),
                     text_color=RX_GREEN
                     ).grid(row=0, column=0, sticky="w",
                            padx=16, pady=(14, 2))

        date_str = (rx.get("issued_date") or "")[:10] or "—"
        ctk.CTkLabel(hdr,
                     text=f"Patient: {rx.get('patient_name','—')}   "
                          f"Date: {date_str}   "
                          f"Rx #{rx.get('rx_id',0):04d}",
                     font=ctk.CTkFont(FONT, 11),
                     text_color=RX_GREEN, anchor="w"
                     ).grid(row=1, column=0, sticky="w",
                            padx=16, pady=(0, 12))

        # Medicines
        ctk.CTkLabel(scroll, text="💊  Medicines",
                     font=ctk.CTkFont(FONT, 13, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=1, column=0, sticky="w",
                            padx=20, pady=(0, 8))

        if not items:
            ctk.CTkLabel(scroll, text="No medicines recorded.",
                         font=ctk.CTkFont(FONT, 12),
                         text_color=TEXT_SECONDARY
                         ).grid(row=2, column=0, pady=20)
        else:
            for i, item in enumerate(items):
                card = ctk.CTkFrame(scroll, fg_color=PANEL_BG,
                                    border_width=1, border_color=BORDER,
                                    corner_radius=8)
                card.grid(row=2 + i, column=0, sticky="ew",
                          padx=20, pady=3)
                card.grid_columnconfigure(0, weight=1)

                name_line = (f"{i+1}.  {item.get('medicine_name','—')}"
                             + (f"  —  {item['dosage']}"
                                if item.get("dosage") else ""))
                ctk.CTkLabel(card, text=name_line,
                             font=ctk.CTkFont(FONT, 12, "bold"),
                             text_color=TEXT_PRIMARY, anchor="w"
                             ).grid(row=0, column=0, padx=12,
                                    pady=(8, 2), sticky="w")

                detail = "  ·  ".join(filter(None, [
                    item.get("frequency", ""),
                    item.get("duration", ""),
                    item.get("instructions", ""),
                ]))
                if detail:
                    ctk.CTkLabel(card, text=detail,
                                 font=ctk.CTkFont(FONT, 11),
                                 text_color=TEXT_SECONDARY,
                                 anchor="w"
                                 ).grid(row=1, column=0, padx=12,
                                        pady=(0, 8), sticky="w")

        # Notes
        if rx.get("notes"):
            ctk.CTkFrame(scroll, fg_color=BORDER, height=1
                         ).grid(row=2 + len(items), column=0,
                                sticky="ew", padx=20, pady=(12, 8))
            ctk.CTkLabel(scroll,
                         text=f"📝  Notes: {rx['notes']}",
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_SECONDARY,
                         anchor="w", wraplength=400
                         ).grid(row=3 + len(items), column=0,
                                sticky="w", padx=20,
                                pady=(0, 16))

        # Buttons
        btn_fr = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_fr.grid(row=10, column=0, sticky="ew",
                    padx=20, pady=(8, 24))
        btn_fr.grid_columnconfigure(0, weight=1)
        btn_fr.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_fr, text="🖨  Print / PDF",
                      font=ctk.CTkFont(FONT, 13, "bold"),
                      fg_color=SUCCESS, hover_color="#15803D",
                      height=40, corner_radius=8,
                      command=self._print_pdf
                      ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(btn_fr, text="Close",
                      font=ctk.CTkFont(FONT, 12),
                      fg_color=PANEL_ALT, hover_color=BORDER,
                      text_color=TEXT_PRIMARY,
                      height=40, corner_radius=8,
                      command=self.destroy
                      ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _print_pdf(self):
        rx_id = self.rx.get("rx_id")
        if not rx_id:
            return
        if self.controller:
            try:
                self.controller.reprint_prescription_pdf(rx_id)
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("PDF Error", str(e), parent=self)
        else:
            from tkinter import messagebox
            messagebox.showinfo(
                "PDF",
                f"Prescription Rx-{rx_id:04d} PDF is saved in the "
                "'prescriptions/' folder.",
                parent=self)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════

class PrescriptionView(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller      = controller
        self._rx_cache       = []

        # Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(self, controller, active="prescriptions")
        self._sidebar.grid(row=0, column=0, sticky="ns")

        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_table()
        self._load_rx()

    # ══════════════════════════════════════════════════════════════════════
    # DATA
    # ══════════════════════════════════════════════════════════════════════

    def _load_rx(self):
        """Load all prescriptions directly from DB."""
        try:
            rows = self.controller.db.fetch_all(
                """SELECT r.rx_id, p.full_name, r.issued_date,
                          r.notes, r.patient_id,
                          COUNT(ri.item_id) AS med_count
                   FROM prescriptions r
                   JOIN patients p ON r.patient_id = p.patient_id
                   LEFT JOIN prescription_items ri
                          ON r.rx_id = ri.rx_id
                   GROUP BY r.rx_id
                   ORDER BY r.issued_date DESC"""
            ) or []
        except Exception:
            rows = []

        keys = ["rx_id", "patient_name", "issued_date",
                "notes", "patient_id", "med_count"]
        self._rx_cache = [dict(zip(keys, r)) for r in rows]
        self._render_table(self._rx_cache)

    def _load_rx_items(self, rx_id: int) -> list:
        try:
            rows = self.controller.db.fetch_all(
                """SELECT medicine_name, dosage, frequency,
                          duration, instructions
                   FROM prescription_items WHERE rx_id=?""",
                (rx_id,)
            ) or []
        except Exception:
            rows = []
        keys = ["medicine_name", "dosage", "frequency",
                "duration", "instructions"]
        return [dict(zip(keys, r)) for r in rows]

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

        ctk.CTkLabel(bar, text="📋  Prescriptions",
                     font=ctk.CTkFont(FONT, 20, "bold"),
                     text_color=TEXT_PRIMARY
                     ).grid(row=0, column=0, padx=24, sticky="w")

        ctk.CTkLabel(bar,
                     text=datetime.now().strftime("%A, %d %B %Y"),
                     font=ctk.CTkFont(FONT, 12),
                     text_color=TEXT_SECONDARY
                     ).grid(row=0, column=1, padx=8, sticky="w")

        acts = ctk.CTkFrame(bar, fg_color="transparent")
        acts.grid(row=0, column=2, padx=24, pady=14)

        ctk.CTkButton(
            acts, text="↻  Refresh", width=100, height=36,
            font=ctk.CTkFont(FONT, 12),
            fg_color=PANEL_ALT, hover_color=ACCENT_LIGHT,
            text_color=TEXT_PRIMARY, corner_radius=8,
            command=self._load_rx
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            acts, text="＋  New Prescription", width=170, height=36,
            font=ctk.CTkFont(FONT, 13, "bold"),
            fg_color=SUCCESS, hover_color="#15803D",
            corner_radius=8,
            command=self._open_new_rx
        ).pack(side="left")

    # ══════════════════════════════════════════════════════════════════════
    # FULL-WIDTH TABLE
    # ══════════════════════════════════════════════════════════════════════

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

        ctk.CTkLabel(tr, text="Prescription Records",
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
            ("Rx #",       70),
            ("Patient",   220),
            ("Date",      120),
            ("Medicines",  90),
            ("Notes",     320),
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

    def _render_table(self, records: list):
        for w in self._table_scroll.winfo_children():
            w.destroy()

        n = len(records)
        self._count_lbl.configure(
            text=f"{n} prescription{'s' if n != 1 else ''}")

        if not records:
            ctk.CTkLabel(self._table_scroll,
                         text="No prescriptions found.",
                         font=ctk.CTkFont(FONT, 13),
                         text_color=TEXT_SECONDARY
                         ).grid(row=0, column=0, pady=60)
            return

        for idx, rx in enumerate(records):
            self._render_row(rx, idx)

    def _render_row(self, rx: dict, idx: int):
        bg = PANEL_BG if idx % 2 == 0 else "#FAFBFD"

        row = ctk.CTkFrame(self._table_scroll,
                           fg_color=bg, height=48,
                           corner_radius=0)
        row.grid(row=idx, column=0, sticky="ew")
        row.grid_propagate(False)

        def enter(e, r=row): r.configure(fg_color="#ECFDF5")
        def leave(e, r=row, b=bg): r.configure(fg_color=b)
        def click(e, r=rx): self._open_detail(r)

        row.bind("<Enter>", enter)
        row.bind("<Leave>", leave)
        row.bind("<Button-1>", click)

        date_str = (rx.get("issued_date") or "")[:10] or "—"
        med_count = rx.get("med_count", 0)
        notes = (rx.get("notes") or "—")[:45]

        COLS = [
            (f"Rx #{rx.get('rx_id',0):04d}", 70,  ACCENT,        "bold"),
            (rx.get("patient_name", "—"),    220, TEXT_PRIMARY,  "bold"),
            (date_str,                       120, TEXT_SECONDARY,"normal"),
            (f"{med_count} medicine{'s' if med_count!=1 else ''}",
                                              90,  RX_GREEN,      "normal"),
            (notes,                          320, TEXT_SECONDARY,"normal"),
        ]
        for col, (txt, w, color, weight) in enumerate(COLS):
            lbl = ctk.CTkLabel(row, text=txt,
                               font=ctk.CTkFont(FONT, 12, weight=weight),
                               text_color=color,
                               width=w, anchor="w")
            lbl.grid(row=0, column=col,
                     padx=(14 if col == 0 else 8, 4),
                     sticky="w")
            lbl.bind("<Enter>", enter)
            lbl.bind("<Leave>", leave)
            lbl.bind("<Button-1>", click)

    # ══════════════════════════════════════════════════════════════════════
    # POPUP OPENERS
    # ══════════════════════════════════════════════════════════════════════

    def _open_new_rx(self):
        NewPrescriptionWindow(
            parent_view=self,
            controller=self.controller,
            on_saved=self._load_rx
        )

    def _open_detail(self, rx: dict):
        items = self._load_rx_items(rx["rx_id"])
        RxDetailWindow(rx=rx, items=items, controller=self.controller)

    # ══════════════════════════════════════════════════════════════════════
    # CONTROLLER INTERFACE
    # ══════════════════════════════════════════════════════════════════════

    def render_patients(self, patients: list):
        """Compatibility — patients loaded directly in popup."""
        pass

    def show_form_message(self, message: str, success: bool = True):
        try:
            Toast.show(self._content, message, success=success)
        except Exception:
            pass

    def clear_prescription_form(self):
        self._load_rx()