# view/admin/patient_view.py
"""
PatientView — Patient Management Screen
Style : Light / Professional  (white background, blue accents)

Layout:
  ├── Sidebar      : shared nav (col 0, fixed)
  └── Content col  :
        ├── Top bar : title + search + Back + New Patient
        └── Full-width scrollable patient table

Add / Edit opens in a separate CTkToplevel popup window.
Clicking a row opens a detail popup (view + edit + delete).
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from view.sidebar import Sidebar, Toast

# ── Light Palette ─────────────────────────────────────────────────────────────
BG             = "#F7F8FA"
PANEL_BG       = "#FFFFFF"
PANEL_ALT      = "#F1F5F9"
BORDER         = "#E2E6ED"
TEXT_PRIMARY   = "#1A202C"
TEXT_SECONDARY = "#64748B"
ACCENT         = "#2563EB"
ACCENT_HOVER   = "#1D4ED8"
ACCENT_LIGHT   = "#DBEAFE"
SUCCESS        = "#16A34A"
SUCCESS_LIGHT  = "#DCFCE7"
DANGER         = "#DC2626"
DANGER_LIGHT   = "#FEE2E2"
WARNING        = "#D97706"

FONT = "Helvetica"

GENDER_OPTIONS = ["Other", "Male", "Female"]
BLOOD_OPTIONS  = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
WILAYAS = [
    "", "Adrar", "Chlef", "Laghouat", "Oum El Bouaghi", "Batna", "Béjaïa",
    "Biskra", "Béchar", "Blida", "Bouira", "Tamanrasset", "Tébessa",
    "Tlemcen", "Tiaret", "Tizi Ouzou", "Alger", "Djelfa", "Jijel", "Sétif",
    "Saïda", "Skikda", "Sidi Bel Abbès", "Annaba", "Guelma", "Constantine",
    "Médéa", "Mostaganem", "M'Sila", "Mascara", "Ouargla", "Oran",
    "El Bayadh", "Illizi", "Bordj Bou Arréridj", "Boumerdès", "El Tarf",
    "Tindouf", "Tissemsilt", "El Oued", "Khenchela", "Souk Ahras",
    "Tipaza", "Mila", "Aïn Defla", "Naâma", "Aïn Témouchent", "Ghardaïa",
    "Relizane",
]


# ══════════════════════════════════════════════════════════════════════════════
# POPUP WINDOW — Add / Edit patient
# ══════════════════════════════════════════════════════════════════════════════

class PatientFormWindow(ctk.CTkToplevel):
    """
    Standalone popup for adding or editing a patient.
    Closes itself after a successful save.
    """

    def __init__(self, parent_view, controller,
                 prefill: dict = None, on_saved=None):
        super().__init__()
        self.parent_view = parent_view
        self.controller  = controller
        self.prefill     = prefill or {}
        self.on_saved    = on_saved        # callback → called after save
        self._edit_mode  = bool(prefill)
        self._form_vars  = {}

        title = "Edit Patient" if self._edit_mode else "Add New Patient"
        self.title(f"🏥  {title}")
        self.geometry("620x700")
        self.resizable(True, True)
        self.grab_set()          # modal
        self.lift()
        self.focus_force()

        # Make the window expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build()

    def _build(self):
        # Outer scroll
        scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        # ── Header ────────────────────────────────────────────────────────
        hdr_bg = SUCCESS_LIGHT if not self._edit_mode else "#FFF7ED"
        hdr_fg = SUCCESS       if not self._edit_mode else WARNING
        icon   = "➕" if not self._edit_mode else "✏️"
        title  = "New Patient" if not self._edit_mode else "Edit Patient"

        hdr = ctk.CTkFrame(scroll, fg_color=hdr_bg, corner_radius=10)
        hdr.grid(row=0, column=0, columnspan=2,
                 sticky="ew", padx=20, pady=(20, 12))
        ctk.CTkLabel(hdr, text=f"{icon}  {title}",
                     font=ctk.CTkFont(FONT, 16, "bold"),
                     text_color=hdr_fg
                     ).pack(anchor="w", padx=20, pady=12)

        # ── Field helpers ─────────────────────────────────────────────────
        def entry(row, col, label, key, placeholder="",
                  colspan=1, is_text=False):
            fr = ctk.CTkFrame(scroll, fg_color="transparent")
            fr.grid(row=row, column=col, columnspan=colspan,
                    sticky="ew", padx=(20, 10), pady=5)
            fr.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(fr, text=label,
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=0, column=0, sticky="w")
            if is_text:
                box = ctk.CTkTextbox(fr, height=75,
                                      font=ctk.CTkFont(FONT, 12),
                                      fg_color=PANEL_ALT,
                                      border_width=1, border_color=BORDER,
                                      text_color=TEXT_PRIMARY)
                box.grid(row=1, column=0, sticky="ew")
                if self.prefill.get(key):
                    box.insert("1.0", self.prefill[key])
                self._form_vars[key] = box
            else:
                var = ctk.StringVar(
                    value=self.prefill.get(key, ""))
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

        # ── Fields ────────────────────────────────────────────────────────
        entry(1, 0, "Full Name *", "name",
              "e.g. Ahmed Benali", colspan=2)
        entry(2, 0, "Date of Birth", "date_of_birth", "YYYY-MM-DD")
        option(2, 1, "Gender", "gender", GENDER_OPTIONS)
        entry(3, 0, "Phone", "phone", "+213 …")
        entry(3, 1, "Email", "email", "patient@mail.com")
        option(4, 0, "Blood Type", "blood_type", BLOOD_OPTIONS)
        option(4, 1, "Wilaya", "wilaya", WILAYAS)
        entry(5, 0, "Address", "address",
              "Street / district…", colspan=2)
        entry(6, 0, "Allergies", "allergies",
              "List known allergies…", colspan=2)
        entry(7, 0, "Medical History", "medical_history",
              colspan=2, is_text=True)
        entry(8, 0, "Notes", "notes",
              colspan=2, is_text=True)

        # ── Feedback label ────────────────────────────────────────────────
        self._msg_lbl = ctk.CTkLabel(
            scroll, text="",
            font=ctk.CTkFont(FONT, 12),
            text_color=SUCCESS, anchor="w")
        self._msg_lbl.grid(row=9, column=0, columnspan=2,
                           padx=20, pady=(6, 0), sticky="w")

        # ── Buttons ───────────────────────────────────────────────────────
        br = ctk.CTkFrame(scroll, fg_color="transparent")
        br.grid(row=10, column=0, columnspan=2,
                sticky="ew", padx=20, pady=(8, 24))
        br.grid_columnconfigure(0, weight=1)
        br.grid_columnconfigure(1, weight=1)

        save_lbl = "Save Changes" if self._edit_mode else "Register Patient"
        ctk.CTkButton(
            br, text=save_lbl,
            font=ctk.CTkFont(FONT, 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            height=42, corner_radius=8,
            command=self._submit
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            br, text="Cancel",
            font=ctk.CTkFont(FONT, 13),
            fg_color=PANEL_ALT, hover_color=BORDER,
            text_color=TEXT_PRIMARY,
            height=42, corner_radius=8,
            command=self.destroy
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Delete button in edit mode
        if self._edit_mode:
            ctk.CTkButton(
                br, text="🗑  Delete Patient",
                font=ctk.CTkFont(FONT, 12),
                fg_color="transparent",
                hover_color=DANGER_LIGHT,
                text_color=DANGER,
                border_width=1, border_color=DANGER,
                height=40, corner_radius=8,
                command=self._confirm_delete
            ).grid(row=1, column=0, columnspan=2,
                   sticky="ew", pady=(8, 0))

    def _get_data(self) -> dict:
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
            self._show_msg("Full name is required.", success=False)
            return

        if self._edit_mode:
            pid = self.prefill.get("patient_id")
            if hasattr(self.controller, "on_update_patient"):
                self.controller.on_update_patient(pid, data)
            self._show_msg("Patient updated!", success=True)
        else:
            self.controller.on_save_patient(data)
            self._show_msg("Patient registered!", success=True)

        # Refresh the parent table
        if self.on_saved:
            self.after(600, self.on_saved)
        self.after(700, self.destroy)

    def _confirm_delete(self):
        name = self.prefill.get("full_name", "")
        pid  = self.prefill.get("patient_id")
        if messagebox.askyesno(
                "Delete Patient",
                f"Permanently delete '{name}'?\nThis cannot be undone.",
                icon="warning",
                parent=self):
            self.controller.on_delete_patient(pid, name)
            if self.on_saved:
                self.after(100, self.on_saved)
            self.destroy()

    def _show_msg(self, msg: str, success: bool = True):
        self._msg_lbl.configure(
            text=msg,
            text_color=SUCCESS if success else DANGER)


# ══════════════════════════════════════════════════════════════════════════════
# DETAIL POPUP — read-only patient info + action buttons
# ══════════════════════════════════════════════════════════════════════════════

class PatientDetailWindow(ctk.CTkToplevel):
    """Quick-view popup shown when a table row is clicked."""

    def __init__(self, parent_view, controller,
                 patient: dict, history: list, on_refresh=None):
        super().__init__()
        self.parent_view = parent_view
        self.controller  = controller
        self.patient     = patient
        self.history     = history
        self.on_refresh  = on_refresh

        self.title(f"🏥  {patient.get('full_name', 'Patient')}")
        self.geometry("520x640")
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

        p = self.patient

        # ── Avatar header ─────────────────────────────────────────────────
        card = ctk.CTkFrame(scroll, fg_color=ACCENT_LIGHT,
                            corner_radius=12,
                            border_width=1, border_color="#BFDBFE")
        card.grid(row=0, column=0, sticky="ew",
                  padx=20, pady=(20, 12))
        card.grid_columnconfigure(1, weight=1)

        av = ctk.CTkFrame(card, fg_color=ACCENT,
                          width=60, height=60, corner_radius=30)
        av.grid(row=0, column=0, rowspan=3, padx=16, pady=16)
        av.grid_propagate(False)
        initials = "".join(
            w[0].upper()
            for w in p.get("full_name", "?").split()[:2])
        ctk.CTkLabel(av, text=initials,
                     font=ctk.CTkFont(FONT, 20, "bold"),
                     text_color="#fff"
                     ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text=p.get("full_name", "—"),
                     font=ctk.CTkFont(FONT, 17, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=1, sticky="w",
                            padx=(0, 16), pady=(14, 2))

        age = _calc_age(p.get("date_of_birth", ""))
        meta = (f"Age {age}  •  " if age else "") + \
               f"{p.get('gender','—')}  •  {p.get('blood_type','—')}"
        ctk.CTkLabel(card, text=meta,
                     font=ctk.CTkFont(FONT, 12),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=1, column=1, sticky="w",
                            padx=(0, 16))

        phone_wilaya = p.get("phone", "—") + \
            ("  •  " + p.get("wilaya") if p.get("wilaya") else "")
        ctk.CTkLabel(card, text=phone_wilaya,
                     font=ctk.CTkFont(FONT, 11),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=2, column=1, sticky="w",
                            padx=(0, 16), pady=(0, 12))

        # ── Action buttons ────────────────────────────────────────────────
        acts = ctk.CTkFrame(scroll, fg_color="transparent")
        acts.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        acts.grid_columnconfigure(0, weight=1)
        acts.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            acts, text="✏️  Edit Patient",
            font=ctk.CTkFont(FONT, 12, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            height=36, corner_radius=8,
            command=self._open_edit
        ).grid(row=0, column=0, sticky="ew", padx=(0, 5))

        ctk.CTkButton(
            acts, text="📅  New Appointment",
            font=ctk.CTkFont(FONT, 12),
            fg_color=SUCCESS_LIGHT, hover_color="#BBF7D0",
            text_color=SUCCESS,
            border_width=1, border_color=SUCCESS,
            height=36, corner_radius=8,
            command=lambda: (self.destroy(),
                             self.controller.navigate("appointments"))
        ).grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # ── Info grid ─────────────────────────────────────────────────────
        info = ctk.CTkFrame(scroll, fg_color=PANEL_BG,
                            border_width=1, border_color=BORDER,
                            corner_radius=10)
        info.grid(row=2, column=0, sticky="ew",
                  padx=20, pady=(0, 12))
        info.grid_columnconfigure(0, weight=1)
        info.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(info, text="Patient Info",
                     font=ctk.CTkFont(FONT, 12, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, columnspan=2,
                            padx=14, pady=(10, 6), sticky="w")

        fields = [
            ("📅 Date of Birth", p.get("date_of_birth") or "—"),
            ("📧 Email",         p.get("email")         or "—"),
            ("📍 Address",       p.get("address")       or "—"),
            ("⚠️ Allergies",     p.get("allergies")     or "—"),
        ]
        for i, (lbl, val) in enumerate(fields):
            ctk.CTkLabel(info, text=lbl,
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=i+1, column=0,
                                padx=14, pady=3, sticky="w")
            ctk.CTkLabel(info, text=val,
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_PRIMARY,
                         anchor="w", wraplength=180
                         ).grid(row=i+1, column=1,
                                padx=(4, 14), pady=3, sticky="w")

        if p.get("medical_history"):
            ctk.CTkLabel(info, text="🏥 Medical History",
                         font=ctk.CTkFont(FONT, 11, "bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=len(fields)+1, column=0,
                                columnspan=2, padx=14,
                                pady=(6, 2), sticky="w")
            ctk.CTkLabel(info, text=p["medical_history"],
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_PRIMARY,
                         anchor="w", wraplength=440, justify="left"
                         ).grid(row=len(fields)+2, column=0,
                                columnspan=2, padx=14,
                                pady=(0, 10), sticky="w")

        # ── Visit history ─────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="📁  Visit History",
                     font=ctk.CTkFont(FONT, 13, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=3, column=0, padx=20,
                            pady=(8, 4), sticky="w")

        hf = ctk.CTkFrame(scroll, fg_color="transparent")
        hf.grid(row=4, column=0, sticky="ew",
                padx=20, pady=(0, 20))
        hf.grid_columnconfigure(0, weight=1)

        if not self.history:
            ctk.CTkLabel(hf, text="No visits recorded yet.",
                         font=ctk.CTkFont(FONT, 12),
                         text_color=TEXT_SECONDARY
                         ).grid(row=0, column=0, pady=12)
        else:
            for i, row in enumerate(self.history[:10]):
                appt_id, appt_date, status, \
                    visit_type, diagnosis, total = row
                self._render_history_row(
                    hf, i, appt_id, appt_date,
                    status, visit_type, diagnosis, total)

    def _render_history_row(self, parent, idx, appt_id,
                             appt_date, status, visit_type,
                             diagnosis, total):
        SC = {
            "Completed":   (SUCCESS_LIGHT, SUCCESS),
            "Pending":     ("#FEF3C7",     WARNING),
            "In Progress": (ACCENT_LIGHT,  ACCENT),
            "Cancelled":   (DANGER_LIGHT,  DANGER),
            "No Show":     ("#F3F4F6",     TEXT_SECONDARY),
        }
        bg, fg = SC.get(status, ("#F3F4F6", TEXT_SECONDARY))

        card = ctk.CTkFrame(parent, fg_color=PANEL_BG,
                            border_width=1, border_color=BORDER,
                            corner_radius=8)
        card.grid(row=idx, column=0, sticky="ew", pady=3)
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew",
                 padx=12, pady=(8, 2))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top,
                     text=f"#{appt_id:04d}  "
                          f"{(appt_date or '')[:10]}  —  "
                          f"{visit_type or '—'}",
                     font=ctk.CTkFont(FONT, 11, "bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")

        badge = ctk.CTkFrame(top, fg_color=bg, corner_radius=6)
        badge.grid(row=0, column=1)
        ctk.CTkLabel(badge, text=status,
                     font=ctk.CTkFont(FONT, 10, "bold"),
                     text_color=fg).pack(padx=8, pady=2)

        if diagnosis:
            ctk.CTkLabel(card, text=f"Dx: {diagnosis}",
                         font=ctk.CTkFont(FONT, 11),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=1, column=0, sticky="w",
                                padx=12, pady=(0, 2))

        ctk.CTkLabel(card, text=f"{total:,.2f} DA",
                     font=ctk.CTkFont(FONT, 11, "bold"),
                     text_color=ACCENT, anchor="e"
                     ).grid(row=0 if not diagnosis else 1,
                            column=0, sticky="e", padx=12,
                            pady=(8 if not diagnosis else 0, 8))

    def _open_edit(self):
        self.destroy()
        PatientFormWindow(
            self.parent_view,
            self.controller,
            prefill=self.patient,
            on_saved=self.on_refresh
        )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN VIEW
# ══════════════════════════════════════════════════════════════════════════════

class PatientView(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller       = controller
        self._patients_cache  = []

        # 2-column: sidebar | content
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(self, controller, active="patients")
        self._sidebar.grid(row=0, column=0, sticky="ns")

        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_table()
        self._load_patients()

    # ══════════════════════════════════════════════════════════════════════
    # DATA
    # ══════════════════════════════════════════════════════════════════════

    def _load_patients(self, query: str = ""):
        try:
            if query:
                fn = (getattr(self.controller.patient_model,
                              "search_patients", None) or
                      getattr(self.controller.patient_model,
                              "search_patient", None))
                patients = fn(query) if fn else []
            else:
                fn = (getattr(self.controller.patient_model,
                              "get_all_patients", None) or
                      getattr(self.controller.patient_model,
                              "get_all", None))
                patients = fn() if fn else []
        except Exception:
            patients = []

        # normalise tuples → dicts
        normalised = []
        keys = ["patient_id", "full_name", "date_of_birth", "gender",
                "phone", "email", "address", "wilaya", "blood_type",
                "allergies", "medical_history", "notes", "created_at"]
        for p in (patients or []):
            if isinstance(p, dict):
                normalised.append(p)
            else:
                normalised.append(dict(zip(keys, p)))

        self.render_patients(normalised)

    # ══════════════════════════════════════════════════════════════════════
    # TOP BAR
    # ══════════════════════════════════════════════════════════════════════

    def _build_topbar(self):
        bar = ctk.CTkFrame(self._content, fg_color=PANEL_BG,
                           height=64, border_width=1,
                           border_color=BORDER, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="👤  Patients",
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
                     placeholder_text="Search by name, phone or email…",
                     border_width=0, fg_color="transparent",
                     text_color=TEXT_PRIMARY,
                     font=ctk.CTkFont(FONT, 13)
                     ).grid(row=0, column=1, sticky="ew",
                            padx=(0, 8), pady=4)

        # Buttons
        acts = ctk.CTkFrame(bar, fg_color="transparent")
        acts.grid(row=0, column=2, padx=24, pady=14)

        ctk.CTkButton(
            acts, text="← Back", width=90, height=36,
            font=ctk.CTkFont(FONT, 12),
            fg_color=PANEL_ALT, hover_color=ACCENT_LIGHT,
            text_color=TEXT_PRIMARY, corner_radius=8,
            command=lambda: self.controller.navigate("dashboard")
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            acts, text="＋  New Patient", width=150, height=36,
            font=ctk.CTkFont(FONT, 13, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            corner_radius=8,
            command=self._open_add_window
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

        # Table title + count
        tr = ctk.CTkFrame(wrapper, fg_color="transparent")
        tr.grid(row=0, column=0, sticky="ew",
                padx=16, pady=(14, 6))
        tr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tr, text="Patient Records",
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
            ("#",           40),
            ("Full Name",  220),
            ("Phone",      130),
            ("Gender",      80),
            ("Blood",       60),
            ("Wilaya",     120),
            ("Age",         50),
            ("Registered", 130),
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

        # Scrollable rows
        self._table_scroll = ctk.CTkScrollableFrame(
            wrapper, fg_color="transparent")
        self._table_scroll.grid(row=2, column=0, sticky="nsew")
        self._table_scroll.grid_columnconfigure(0, weight=1)

    def _render_row(self, p: dict, idx: int):
        bg = PANEL_BG if idx % 2 == 0 else "#FAFBFD"

        row = ctk.CTkFrame(self._table_scroll,
                           fg_color=bg, height=46,
                           corner_radius=0)
        row.grid(row=idx, column=0, sticky="ew")
        row.grid_propagate(False)

        def enter(e, r=row): r.configure(fg_color=ACCENT_LIGHT)
        def leave(e, r=row, b=bg): r.configure(fg_color=b)
        def click(e, patient=p): self._open_detail_window(patient)

        row.bind("<Enter>", enter)
        row.bind("<Leave>", leave)
        row.bind("<Button-1>", click)

        age = _calc_age(p.get("date_of_birth", ""))
        reg = (p.get("created_at", "") or "")[:10]
        pid = p.get("patient_id", "")

        COLS = [
            (str(pid),                       40,  "normal",  TEXT_SECONDARY),
            (p.get("full_name",    "—"),     220, "bold",    TEXT_PRIMARY),
            (p.get("phone",        "—"),     130, "normal",  TEXT_SECONDARY),
            (p.get("gender",       "—"),      80, "normal",  TEXT_SECONDARY),
            (p.get("blood_type",   "—"),      60, "normal",  TEXT_SECONDARY),
            (p.get("wilaya",       "—"),     120, "normal",  TEXT_SECONDARY),
            (str(age) if age else "—",        50, "normal",  TEXT_SECONDARY),
            (reg or "—",                     130, "normal",  TEXT_SECONDARY),
        ]
        for col, (txt, w, weight, color) in enumerate(COLS):
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

    def _open_add_window(self):
        PatientFormWindow(
            parent_view=self,
            controller=self.controller,
            prefill=None,
            on_saved=self._load_patients
        )

    def _open_detail_window(self, patient: dict):
        # Fetch history first
        try:
            history = self.controller.db.fetch_all(
                """SELECT appointment_id, appointment_date, status,
                          visit_type, diagnosis, total_amount
                   FROM appointments WHERE patient_id=?
                   ORDER BY appointment_date DESC LIMIT 20""",
                (patient["patient_id"],)
            ) or []
        except Exception:
            history = []

        PatientDetailWindow(
            parent_view=self,
            controller=self.controller,
            patient=patient,
            history=history,
            on_refresh=self._load_patients
        )

    # ══════════════════════════════════════════════════════════════════════
    # CONTROLLER INTERFACE  (called by main.py)
    # ══════════════════════════════════════════════════════════════════════

    def render_patients(self, patients: list):
        self._patients_cache = patients

        for w in self._table_scroll.winfo_children():
            w.destroy()

        n = len(patients)
        self._count_lbl.configure(
            text=f"{n} patient{'s' if n != 1 else ''}")

        if not patients:
            ctk.CTkLabel(
                self._table_scroll,
                text="No patients found. Please add a new patient.",
                font=ctk.CTkFont(FONT, 13),
                text_color=TEXT_SECONDARY
            ).grid(row=0, column=0, pady=60)
            return

        for idx, p in enumerate(patients):
            self._render_row(p, idx)

    def render_patient_history(self, patient: dict, history: list):
        """Controller compatibility — opens detail popup."""
        PatientDetailWindow(
            parent_view=self,
            controller=self.controller,
            patient=patient,
            history=history,
            on_refresh=self._load_patients
        )

    def show_form_message(self, message: str, success: bool = True):
        try:
            Toast.show(self._content, message, success=success)
        except Exception:
            pass

    def clear_patient_form(self):
        self._load_patients()

    def _on_search(self, *_):
        query = self._search_var.get().strip()
        self._load_patients(query)
        try:
            self.controller.on_search(query)
        except Exception:
            pass


# ── Module-level helper (used by both classes) ───────────────────────────────

def _calc_age(dob_str: str):
    if not dob_str:
        return None
    try:
        dob   = date.fromisoformat(dob_str[:10])
        today = date.today()
        return (today.year - dob.year
                - ((today.month, today.day) < (dob.month, dob.day)))
    except Exception:
        return None