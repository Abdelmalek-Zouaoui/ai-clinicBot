# view/admin/appointment_view.py
"""
AppointmentView — Full-page appointment schedule
Patient flow: Scheduled → Waiting → In Progress → Completed

Layout:
  Sidebar | Content:
    Top bar + full-width schedule table
    Each row has a context-sensitive quick-action button.
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from view.sidebar import Sidebar, Toast

BG           = "#F7F8FA"
PANEL_BG     = "#FFFFFF"
PANEL_ALT    = "#F1F5F9"
BORDER       = "#E2E6ED"
TEXT_PRIMARY   = "#1A202C"
TEXT_SECONDARY = "#64748B"
ACCENT         = "#2563EB"
ACCENT_LIGHT   = "#DBEAFE"
ACCENT_HOVER   = "#1D4ED8"
SUCCESS        = "#16A34A"
SUCCESS_LIGHT  = "#DCFCE7"
WARNING        = "#D97706"
WARNING_LIGHT  = "#FEF3C7"
DANGER         = "#DC2626"
DANGER_LIGHT   = "#FEE2E2"
TEAL           = "#0D9488"
TEAL_LIGHT     = "#CCFBF1"

FONT = "Helvetica"

VISIT_TYPES = [
    "Consultation", "Follow-up", "Emergency",
    "Procedure", "Lab Results", "Vaccination", "Other",
]

STATUS_STYLE = {
    "Scheduled":   ("#F3F4F6",    TEXT_SECONDARY),
    "Waiting":     (TEAL_LIGHT,   TEAL),
    "Pending":     (WARNING_LIGHT, WARNING),
    "In Progress": (ACCENT_LIGHT,  ACCENT),
    "Completed":   (SUCCESS_LIGHT, SUCCESS),
    "Cancelled":   (DANGER_LIGHT,  DANGER),
    "No Show":     ("#F3F4F6",    TEXT_SECONDARY),
}


# ══════════════════════════════════════════════════════════════════════════════
# POPUP — New Appointment
# ══════════════════════════════════════════════════════════════════════════════

class NewAppointmentWindow(ctk.CTkToplevel):

    def __init__(self, parent_view, controller, on_saved=None):
        super().__init__()
        self.parent_view       = parent_view
        self.controller        = controller
        self.on_saved          = on_saved
        self._selected_patient = None
        self._all_patients     = []

        self.title("📅  New Appointment")
        self.geometry("560x680")
        self.resizable(True, True)
        self.grab_set(); self.lift(); self.focus_force()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self._load_patients()

    def _load_patients(self):
        try:
            fn = (getattr(self.controller.patient_model, "get_all_patients", None)
                  or getattr(self.controller.patient_model, "get_all", None))
            rows = fn() if fn else []
        except Exception:
            rows = []
        keys = ["patient_id","full_name","phone","gender","date_of_birth","wilaya"]
        self._all_patients = [r if isinstance(r,dict) else dict(zip(keys,r))
                               for r in (rows or [])]
        self._populate_list(self._all_patients)

    def _build(self):
        sc = ctk.CTkScrollableFrame(self, fg_color=BG)
        sc.grid(row=0, column=0, sticky="nsew")
        sc.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(sc, fg_color=ACCENT_LIGHT, corner_radius=10)
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(20,14))
        ctk.CTkLabel(hdr, text="📅  New Appointment",
                     font=ctk.CTkFont(FONT,16,"bold"),
                     text_color=ACCENT).pack(anchor="w", padx=20, pady=12)

        def lbl(r, text):
            ctk.CTkLabel(sc, text=text,
                         font=ctk.CTkFont(FONT,12,"bold"),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=r, column=0, sticky="w", padx=20, pady=(0,4))

        def entry_row(r, var, placeholder):
            ctk.CTkEntry(sc, textvariable=var,
                         placeholder_text=placeholder,
                         font=ctk.CTkFont(FONT,13), fg_color=PANEL_ALT,
                         border_width=1, border_color=BORDER,
                         text_color=TEXT_PRIMARY, height=38
                         ).grid(row=r, column=0, sticky="ew", padx=20, pady=(0,4))

        # Patient
        lbl(1, "Patient *")
        self._pt_search_var = ctk.StringVar()
        self._pt_search_var.trace_add("write", self._on_pt_search)
        entry_row(2, self._pt_search_var, "Type name or phone…")

        self._pt_badge = ctk.CTkLabel(sc, text="No patient selected",
                                       font=ctk.CTkFont(FONT,12),
                                       text_color=TEXT_SECONDARY, anchor="w")
        self._pt_badge.grid(row=3, column=0, sticky="w", padx=20, pady=(0,4))

        self._pt_list = ctk.CTkScrollableFrame(sc, fg_color=PANEL_BG,
                                                border_width=1, border_color=BORDER,
                                                height=120, corner_radius=8)
        self._pt_list.grid(row=4, column=0, sticky="ew", padx=20, pady=(0,12))
        self._pt_list.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(sc, fg_color=BORDER, height=1
                     ).grid(row=5, column=0, sticky="ew", padx=20, pady=(0,12))

        # Date & Time
        dt_row = ctk.CTkFrame(sc, fg_color="transparent")
        dt_row.grid(row=6, column=0, sticky="ew", padx=20, pady=(0,12))
        dt_row.grid_columnconfigure(0, weight=1)
        dt_row.grid_columnconfigure(1, weight=1)

        df = ctk.CTkFrame(dt_row, fg_color="transparent")
        df.grid(row=0, column=0, sticky="ew", padx=(0,8))
        df.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(df, text="📅  Date *",
                     font=ctk.CTkFont(FONT,12,"bold"),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w", pady=(0,4))
        self._date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ctk.CTkEntry(df, textvariable=self._date_var,
                     font=ctk.CTkFont(FONT,13), fg_color=PANEL_ALT,
                     border_width=1, border_color=BORDER,
                     text_color=TEXT_PRIMARY, height=38
                     ).grid(row=1, column=0, sticky="ew")

        tf = ctk.CTkFrame(dt_row, fg_color="transparent")
        tf.grid(row=0, column=1, sticky="ew")
        tf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tf, text="🕐  Time *",
                     font=ctk.CTkFont(FONT,12,"bold"),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w", pady=(0,4))
        qf = ctk.CTkFrame(tf, fg_color="transparent")
        qf.grid(row=0, column=1, sticky="e")
        self._time_var = ctk.StringVar(value=datetime.now().strftime("%H:%M"))
        for t in ["08:00","09:00","10:00","14:00","16:00"]:
            ctk.CTkButton(qf, text=t, width=46, height=22,
                          font=ctk.CTkFont(FONT,10),
                          fg_color=ACCENT_LIGHT, hover_color=ACCENT,
                          text_color=ACCENT, corner_radius=6,
                          command=lambda v=t: self._time_var.set(v)
                          ).pack(side="left", padx=1)
        ctk.CTkEntry(tf, textvariable=self._time_var,
                     font=ctk.CTkFont(FONT,13), fg_color=PANEL_ALT,
                     border_width=1, border_color=BORDER,
                     text_color=TEXT_PRIMARY, height=38
                     ).grid(row=1, column=0, columnspan=2, sticky="ew")

        lbl(7, "Visit Type *")
        self._visit_var = ctk.StringVar(value="Consultation")
        ctk.CTkOptionMenu(sc, variable=self._visit_var, values=VISIT_TYPES,
                          font=ctk.CTkFont(FONT,12), fg_color=PANEL_ALT,
                          button_color=ACCENT, button_hover_color=ACCENT_HOVER,
                          dropdown_fg_color=PANEL_BG,
                          text_color=TEXT_PRIMARY, height=38
                          ).grid(row=8, column=0, sticky="ew", padx=20, pady=(0,12))

        lbl(9, "Chief Complaint")
        self._complaint_var = ctk.StringVar()
        entry_row(10, self._complaint_var, "Main reason for visit…")

        lbl(11, "Notes / Diagnosis")
        self._notes_box = ctk.CTkTextbox(sc, height=70,
                                          font=ctk.CTkFont(FONT,12),
                                          fg_color=PANEL_ALT,
                                          border_width=1, border_color=BORDER,
                                          text_color=TEXT_PRIMARY)
        self._notes_box.grid(row=12, column=0, sticky="ew", padx=20, pady=(0,8))

        self._msg_lbl = ctk.CTkLabel(sc, text="",
                                      font=ctk.CTkFont(FONT,12),
                                      text_color=DANGER, anchor="w")
        self._msg_lbl.grid(row=13, column=0, sticky="w", padx=20, pady=(0,4))

        br = ctk.CTkFrame(sc, fg_color="transparent")
        br.grid(row=14, column=0, sticky="ew", padx=20, pady=(4,24))
        br.grid_columnconfigure(0, weight=1)
        br.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(br, text="✅  Create Appointment",
                      font=ctk.CTkFont(FONT,13,"bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      height=42, corner_radius=8, command=self._submit
                      ).grid(row=0, column=0, sticky="ew", padx=(0,6))
        ctk.CTkButton(br, text="Cancel",
                      font=ctk.CTkFont(FONT,13),
                      fg_color=PANEL_ALT, hover_color=BORDER,
                      text_color=TEXT_PRIMARY,
                      height=42, corner_radius=8, command=self.destroy
                      ).grid(row=0, column=1, sticky="ew", padx=(6,0))

    def _on_pt_search(self, *_):
        q = self._pt_search_var.get().strip().lower()
        filtered = ([p for p in self._all_patients
                     if q in p.get("full_name","").lower()
                     or q in p.get("phone","").lower()]
                    if q else self._all_patients)
        self._populate_list(filtered)

    def _populate_list(self, patients):
        for w in self._pt_list.winfo_children():
            w.destroy()
        if not patients:
            ctk.CTkLabel(self._pt_list, text="No patients found.",
                         font=ctk.CTkFont(FONT,11),
                         text_color=TEXT_SECONDARY).pack(pady=10)
            return
        for p in patients[:30]:
            ctk.CTkButton(self._pt_list,
                          text=f"{p.get('full_name','—')}  ·  {p.get('phone','') or '—'}",
                          anchor="w", height=32, font=ctk.CTkFont(FONT,12),
                          fg_color="transparent", hover_color=ACCENT_LIGHT,
                          text_color=TEXT_PRIMARY, corner_radius=6,
                          command=lambda pt=p: self._pick(pt)
                          ).pack(fill="x", padx=4, pady=1)

    def _pick(self, patient):
        self._selected_patient = patient
        self._pt_badge.configure(text=f"✓  {patient['full_name']}",
                                  text_color=SUCCESS)
        self._pt_search_var.set("")
        self._populate_list([])

    def _submit(self):
        if not self._selected_patient:
            self._msg_lbl.configure(text="Please select a patient first.")
            return
        try:
            appt_dt = datetime.strptime(
                f"{self._date_var.get().strip()} {self._time_var.get().strip() or '08:00'}",
                "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            self._msg_lbl.configure(text="Invalid date/time. Use YYYY-MM-DD and HH:MM.")
            return
        data = {
            "patient_id":       self._selected_patient["patient_id"],
            "visit_type":       self._visit_var.get(),
            "chief_complaint":  self._complaint_var.get().strip(),
            "diagnosis":        self._notes_box.get("1.0","end").strip(),
            "appointment_date": appt_dt,
        }
        self.controller.on_create_appointment(data)
        if self.on_saved:
            self.after(300, self.on_saved)
        self.after(400, self.destroy)


# ══════════════════════════════════════════════════════════════════════════════
# POPUP — Appointment Detail + Billing
# ══════════════════════════════════════════════════════════════════════════════

class AppointmentDetailWindow(ctk.CTkToplevel):

    def __init__(self, parent_view, controller, appt: dict, on_refresh=None):
        super().__init__()
        self.parent_view = parent_view
        self.controller  = controller
        self.appt        = appt
        self.on_refresh  = on_refresh
        self._cart_items = []

        self.title(f"📋  {appt.get('patient_name','Appointment')}")
        self.geometry("600x740")
        self.resizable(True, True)
        self.grab_set(); self.lift(); self.focus_force()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        try:
            self.parent_view._selected_appt_id = appt["appointment_id"]
        except Exception:
            pass
        self._build()

    def _build(self):
        sc = ctk.CTkScrollableFrame(self, fg_color=BG)
        sc.grid(row=0, column=0, sticky="nsew")
        sc.grid_columnconfigure(0, weight=1)

        appt   = self.appt
        status = appt.get("status","Pending")
        s_bg, s_fg = STATUS_STYLE.get(status,(WARNING_LIGHT,WARNING))

        # Header
        hdr = ctk.CTkFrame(sc, fg_color=PANEL_BG,
                           border_width=1, border_color=BORDER, corner_radius=12)
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(20,12))
        hdr.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14,6))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text=appt.get("patient_name","—"),
                     font=ctk.CTkFont(FONT,17,"bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")
        badge = ctk.CTkFrame(top, fg_color=s_bg, corner_radius=8)
        badge.grid(row=0, column=1)
        ctk.CTkLabel(badge, text=status,
                     font=ctk.CTkFont(FONT,11,"bold"),
                     text_color=s_fg).pack(padx=12, pady=4)
        visit_dt = appt.get("appointment_date","")
        if len(visit_dt) >= 16:
            visit_dt = visit_dt[:10]+"  "+visit_dt[11:16]
        elif len(visit_dt) >= 10:
            visit_dt = visit_dt[:10]
        ctk.CTkLabel(hdr,
                     text=f"🩺 {appt.get('visit_type','—')}   📅 {visit_dt}   🆔 #{appt.get('appointment_id',0):04d}",
                     font=ctk.CTkFont(FONT,11), text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=1, column=0, sticky="w", padx=16, pady=(0,6))
        if appt.get("chief_complaint"):
            ctk.CTkLabel(hdr, text=f"💬 {appt['chief_complaint']}",
                         font=ctk.CTkFont(FONT,11),
                         text_color=TEXT_SECONDARY, anchor="w"
                         ).grid(row=2, column=0, sticky="w", padx=16, pady=(0,12))

        # Flow section
        flow = ctk.CTkFrame(sc, fg_color=PANEL_BG,
                            border_width=1, border_color=BORDER, corner_radius=12)
        flow.grid(row=1, column=0, sticky="ew", padx=20, pady=(0,12))
        flow.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(flow, text="🔄  Patient Flow",
                     font=ctk.CTkFont(FONT,13,"bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14,8))

        # Progress bar
        steps_fr = ctk.CTkFrame(flow, fg_color=PANEL_ALT, corner_radius=8)
        steps_fr.grid(row=1, column=0, sticky="ew", padx=16, pady=(0,10))
        ORDER = ["Scheduled","Waiting","In Progress","Completed"]
        ICONS = ["📋","🟢","⚙️","✅"]
        cur_idx = ORDER.index(status) if status in ORDER else -1
        for i,(st,ic) in enumerate(zip(ORDER,ICONS)):
            is_done    = i < cur_idx
            is_current = i == cur_idx
            color = SUCCESS if is_done else ACCENT if is_current else TEXT_SECONDARY
            weight = "bold" if is_current else "normal"
            steps_fr.grid_columnconfigure(i*2, weight=1)
            ctk.CTkLabel(steps_fr, text=f"{ic}\n{st}",
                         font=ctk.CTkFont(FONT,10,weight=weight),
                         text_color=color, justify="center"
                         ).grid(row=0, column=i*2, padx=8, pady=10)
            if i < len(ORDER)-1:
                ctk.CTkLabel(steps_fr, text="→",
                             font=ctk.CTkFont(FONT,14),
                             text_color=TEXT_SECONDARY
                             ).grid(row=0, column=i*2+1)

        # Action buttons
        btns = ctk.CTkFrame(flow, fg_color="transparent")
        btns.grid(row=2, column=0, sticky="ew", padx=12, pady=(0,10))
        for c in range(3):
            btns.grid_columnconfigure(c, weight=1)
        FLOW_BTNS = [
            ("🟢 Patient Arrived","Waiting",     TEAL,    "#0F766E"),
            ("▶ Start Visit",    "In Progress",  ACCENT,  ACCENT_HOVER),
            ("✅ Complete",       "Completed",    SUCCESS, "#15803D"),
            ("✕ Cancel",         "Cancelled",    DANGER,  "#B91C1C"),
            ("👻 No Show",        "No Show",      WARNING, "#B45309"),
        ]
        for i,(lbl,st,color,hover) in enumerate(FLOW_BTNS):
            ctk.CTkButton(btns, text=lbl, height=34,
                          font=ctk.CTkFont(FONT,11,"bold"),
                          fg_color=color, hover_color=hover,
                          corner_radius=8,
                          command=lambda s=st: self._update_status(s)
                          ).grid(row=i//3, column=i%3, padx=4, pady=3, sticky="ew")

        ctk.CTkLabel(flow, text="Diagnosis / Notes",
                     font=ctk.CTkFont(FONT,11,"bold"),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=3, column=0, sticky="w", padx=16, pady=(0,4))
        self._diag_box = ctk.CTkTextbox(flow, height=70,
                                         font=ctk.CTkFont(FONT,12),
                                         fg_color=PANEL_ALT,
                                         border_width=1, border_color=BORDER,
                                         text_color=TEXT_PRIMARY)
        self._diag_box.grid(row=4, column=0, sticky="ew", padx=16, pady=(0,14))
        if appt.get("diagnosis"):
            self._diag_box.insert("1.0", appt["diagnosis"])

        # Billing
        sec2 = ctk.CTkFrame(sc, fg_color=PANEL_BG,
                            border_width=1, border_color=BORDER, corner_radius=12)
        sec2.grid(row=2, column=0, sticky="ew", padx=20, pady=(0,12))
        sec2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(sec2, text="💰  Billing",
                     font=ctk.CTkFont(FONT,13,"bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14,8))

        add_row = ctk.CTkFrame(sec2, fg_color="transparent")
        add_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0,8))
        add_row.grid_columnconfigure(0, weight=1)
        self._svc_var = ctk.StringVar()
        ctk.CTkEntry(add_row, textvariable=self._svc_var,
                     placeholder_text="Service code or name…",
                     font=ctk.CTkFont(FONT,12), fg_color=PANEL_ALT,
                     border_width=1, border_color=BORDER,
                     text_color=TEXT_PRIMARY, height=36
                     ).grid(row=0, column=0, sticky="ew", padx=(0,8))
        ctk.CTkButton(add_row, text="＋ Add", width=80, height=36,
                      font=ctk.CTkFont(FONT,12,"bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      corner_radius=8, command=self._add_service
                      ).grid(row=0, column=1)

        self._cart_frame = ctk.CTkScrollableFrame(sec2, fg_color="transparent", height=150)
        self._cart_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,8))
        self._cart_frame.grid_columnconfigure(0, weight=1)
        self._cart_empty = ctk.CTkLabel(self._cart_frame,
                                         text="No services added yet.",
                                         font=ctk.CTkFont(FONT,12),
                                         text_color=TEXT_SECONDARY)
        self._cart_empty.pack(pady=20)

        total_row = ctk.CTkFrame(sec2, fg_color=PANEL_ALT, corner_radius=8)
        total_row.grid(row=3, column=0, sticky="ew", padx=16, pady=(0,8))
        total_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(total_row, text="Total",
                     font=ctk.CTkFont(FONT,13,"bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=14, pady=10)
        self._total_lbl = ctk.CTkLabel(total_row, text="0.00 DA",
                                        font=ctk.CTkFont(FONT,16,"bold"),
                                        text_color=ACCENT)
        self._total_lbl.grid(row=0, column=1, sticky="e", padx=14, pady=10)
        self._bill_msg = ctk.CTkLabel(sec2, text="",
                                       font=ctk.CTkFont(FONT,11),
                                       text_color=SUCCESS, anchor="w")
        self._bill_msg.grid(row=4, column=0, sticky="w", padx=16, pady=(0,4))

        # Buttons
        co = ctk.CTkFrame(sc, fg_color="transparent")
        co.grid(row=3, column=0, sticky="ew", padx=20, pady=(0,24))
        co.grid_columnconfigure(0, weight=1)
        co.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(co, text="💳  Checkout",
                      font=ctk.CTkFont(FONT,13,"bold"),
                      fg_color=SUCCESS, hover_color="#15803D",
                      height=44, corner_radius=8, command=self._checkout
                      ).grid(row=0, column=0, sticky="ew", padx=(0,6))
        ctk.CTkButton(co, text="Close",
                      font=ctk.CTkFont(FONT,13),
                      fg_color=PANEL_ALT, hover_color=BORDER,
                      text_color=TEXT_PRIMARY,
                      height=44, corner_radius=8, command=self.destroy
                      ).grid(row=0, column=1, sticky="ew", padx=(6,0))
        ctk.CTkButton(co, text="🗑  Delete Appointment",
                      font=ctk.CTkFont(FONT,12),
                      fg_color="transparent", hover_color=DANGER_LIGHT,
                      text_color=DANGER, border_width=1, border_color=DANGER,
                      height=38, corner_radius=8,
                      command=self._delete_appointment
                      ).grid(row=1, column=0, columnspan=2,
                             sticky="ew", pady=(8,0))

    @staticmethod
    def _step_done(current, step):
        order = ["Scheduled","Waiting","In Progress","Completed"]
        try:
            return order.index(current) > order.index(step)
        except ValueError:
            return False

    def _update_status(self, status):
        appt_id = self.appt["appointment_id"]
        diag    = self._diag_box.get("1.0","end").strip()
        self.controller.on_update_appointment_status(appt_id, status, diag, None)
        self._bill_msg.configure(text=f"Status → {status}", text_color=SUCCESS)
        self.appt["status"] = status
        if self.on_refresh:
            self.on_refresh()

    def _add_service(self):
        code = self._svc_var.get().strip()
        if code:
            self.controller.on_add_service_to_appointment(code)
            self._svc_var.set("")

    def _checkout(self):
        if not self._cart_items:
            self._bill_msg.configure(text="Add at least one service.", text_color=DANGER)
            return
        if messagebox.askyesno("Checkout","Finalise visit and generate receipt?",parent=self):
            self.controller.on_checkout()
            if self.on_refresh: self.on_refresh()
            self.destroy()

    def _delete_appointment(self):
        appt_id = self.appt["appointment_id"]
        name    = self.appt.get("patient_name","")
        if not messagebox.askyesno("Delete Appointment",
                                    f"Permanently delete appointment for {name}?\nThis cannot be undone.",
                                    icon="warning", parent=self):
            return
        try:
            self.controller.db.execute_query(
                "DELETE FROM appointment_services WHERE appointment_id=?", (appt_id,))
            self.controller.db.execute_query(
                "DELETE FROM appointments WHERE appointment_id=?", (appt_id,))
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self); return
        if self.on_refresh: self.on_refresh()
        self.destroy()

    def add_cart_row(self, item: dict):
        try:
            if self._cart_empty.winfo_exists():
                self._cart_empty.destroy()
        except Exception:
            pass
        self._cart_items.append(item)
        sid = item.get("barcode") or item.get("service_id")
        idx = len(self._cart_items) - 1
        row = ctk.CTkFrame(self._cart_frame, fg_color=PANEL_ALT,
                           border_width=1, border_color=BORDER, corner_radius=8)
        row.grid(row=idx, column=0, sticky="ew", padx=6, pady=3)
        row.grid_columnconfigure(0, weight=1)
        top = ctk.CTkFrame(row, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(8,0))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text=item.get("name","—"),
                     font=ctk.CTkFont(FONT,12,"bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top, text=f"{item.get('subtotal','0.00')} DA",
                     font=ctk.CTkFont(FONT,12,"bold"),
                     text_color=SUCCESS).grid(row=0, column=1, sticky="e")
        bot = ctk.CTkFrame(row, fg_color="transparent")
        bot.grid(row=1, column=0, sticky="ew", padx=10, pady=(2,8))
        bot.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(bot, text=f"{item.get('price','0')} DA × {item.get('qty',1)}",
                     font=ctk.CTkFont(FONT,11),
                     text_color=TEXT_SECONDARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")
        ctrl = ctk.CTkFrame(bot, fg_color="transparent")
        ctrl.grid(row=0, column=1, sticky="e")
        for txt, delta in [("−",-1),("+",1)]:
            ctk.CTkButton(ctrl, text=txt, width=28, height=28,
                          font=ctk.CTkFont(FONT,12,"bold"),
                          fg_color=PANEL_ALT, hover_color=BORDER,
                          text_color=TEXT_PRIMARY, corner_radius=6,
                          command=lambda s=sid,d=delta: self.controller.on_qty_change(s,d)
                          ).pack(side="left", padx=2)
        ctk.CTkButton(ctrl, text="✕", width=28, height=28,
                      font=ctk.CTkFont(FONT,11),
                      fg_color=DANGER_LIGHT, hover_color="#FECACA",
                      text_color=DANGER, corner_radius=6,
                      command=lambda s=sid: self.controller.on_remove_from_appointment(s)
                      ).pack(side="left", padx=2)

    def set_total(self, text):
        self._total_lbl.configure(text=text)

    def clear_cart(self):
        self._cart_items = []
        for w in self._cart_frame.winfo_children():
            w.destroy()
        self._cart_empty = ctk.CTkLabel(self._cart_frame,
                                         text="No services added yet.",
                                         font=ctk.CTkFont(FONT,12),
                                         text_color=TEXT_SECONDARY)
        self._cart_empty.pack(pady=20)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN VIEW — full-page schedule
# ══════════════════════════════════════════════════════════════════════════════

class AppointmentView(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.controller        = controller
        self._queue            = []
        self._selected_appt_id = None
        self._detail_window    = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(self, controller, active="appointments")
        self._sidebar.grid(row=0, column=0, sticky="ns")

        self._content = ctk.CTkFrame(self, fg_color=BG)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(1, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_table()

    def _load_queue(self):
        try:
            rows = self.controller.db.fetch_all(
                """SELECT a.appointment_id, p.full_name,
                          a.appointment_date, a.status,
                          a.visit_type, a.chief_complaint,
                          a.diagnosis, a.total_amount, a.patient_id
                   FROM appointments a
                   JOIN patients p ON a.patient_id = p.patient_id
                   WHERE DATE(a.appointment_date) = DATE('now')
                   ORDER BY
                     CASE a.status
                       WHEN 'Waiting'     THEN 1
                       WHEN 'In Progress' THEN 2
                       WHEN 'Scheduled'   THEN 3
                       WHEN 'Pending'     THEN 3
                       WHEN 'Completed'   THEN 4
                       ELSE 5
                     END, a.appointment_date ASC"""
            ) or []
        except Exception:
            rows = []
        keys = ["appointment_id","patient_name","appointment_date","status",
                "visit_type","chief_complaint","diagnosis","total_amount","patient_id"]
        self.render_queue([dict(zip(keys,r)) for r in rows])

    def _build_topbar(self):
        bar = ctk.CTkFrame(self._content, fg_color=PANEL_BG, height=64,
                           border_width=1, border_color=BORDER, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="📅  Appointments",
                     font=ctk.CTkFont(FONT,20,"bold"),
                     text_color=TEXT_PRIMARY
                     ).grid(row=0, column=0, padx=24, sticky="w")

        ctk.CTkLabel(bar, text=datetime.now().strftime("%A, %d %B %Y"),
                     font=ctk.CTkFont(FONT,12),
                     text_color=TEXT_SECONDARY
                     ).grid(row=0, column=1, padx=8, sticky="w")

        acts = ctk.CTkFrame(bar, fg_color="transparent")
        acts.grid(row=0, column=2, padx=24, pady=14)

        ctk.CTkButton(acts, text="🟢  Waiting Room", width=150, height=36,
                      font=ctk.CTkFont(FONT,12,"bold"),
                      fg_color=TEAL, hover_color="#0F766E",
                      corner_radius=8,
                      command=lambda: self.controller.navigate("waiting_room")
                      ).pack(side="left", padx=(0,6))

        ctk.CTkButton(acts, text="↻  Refresh", width=100, height=36,
                      font=ctk.CTkFont(FONT,12),
                      fg_color=PANEL_ALT, hover_color=ACCENT_LIGHT,
                      text_color=TEXT_PRIMARY, corner_radius=8,
                      command=self._load_queue
                      ).pack(side="left", padx=(0,6))

        ctk.CTkButton(acts, text="＋  New Appointment", width=170, height=36,
                      font=ctk.CTkFont(FONT,13,"bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      corner_radius=8, command=self._open_new_appt
                      ).pack(side="left")

    def _build_table(self):
        wrapper = ctk.CTkFrame(self._content, fg_color=PANEL_BG,
                               border_width=1, border_color=BORDER, corner_radius=12)
        wrapper.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        wrapper.grid_rowconfigure(2, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        tr = ctk.CTkFrame(wrapper, fg_color="transparent")
        tr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14,6))
        tr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(tr, text="📋  Today's Schedule",
                     font=ctk.CTkFont(FONT,14,"bold"),
                     text_color=TEXT_PRIMARY, anchor="w"
                     ).grid(row=0, column=0, sticky="w")
        self._count_lbl = ctk.CTkLabel(tr, text="",
                                        font=ctk.CTkFont(FONT,11),
                                        text_color=TEXT_SECONDARY)
        self._count_lbl.grid(row=0, column=1, sticky="e")

        # Waiting room quick-link badge
        self._waiting_badge = ctk.CTkLabel(tr, text="",
                                            font=ctk.CTkFont(FONT,11,"bold"),
                                            text_color=TEAL)
        self._waiting_badge.grid(row=0, column=2, sticky="e", padx=(8,0))

        COLS = [
            ("#",          45), ("Patient",    200), ("Date & Time", 130),
            ("Visit Type", 120), ("Complaint", 180), ("Status",      110),
            ("Total DA",    95), ("Action",    105),
        ]
        hdr = ctk.CTkFrame(wrapper, fg_color="#F8FAFC", height=34, corner_radius=0)
        hdr.grid(row=1, column=0, sticky="ew")
        hdr.grid_propagate(False)
        for col,(lbl,w) in enumerate(COLS):
            ctk.CTkLabel(hdr, text=lbl,
                         font=ctk.CTkFont(FONT,11,"bold"),
                         text_color=TEXT_SECONDARY, width=w, anchor="w"
                         ).grid(row=0, column=col,
                                padx=(12 if col==0 else 6,4), sticky="w")

        self._table_scroll = ctk.CTkScrollableFrame(wrapper, fg_color="transparent")
        self._table_scroll.grid(row=2, column=0, sticky="nsew")
        self._table_scroll.grid_columnconfigure(0, weight=1)

    def _render_row(self, appt: dict, idx: int):
        status     = appt.get("status","Pending")
        s_bg, s_fg = STATUS_STYLE.get(status,(WARNING_LIGHT,WARNING))
        bg         = PANEL_BG if idx%2==0 else "#FAFBFD"

        row = ctk.CTkFrame(self._table_scroll, fg_color=bg,
                           height=50, corner_radius=0)
        row.grid(row=idx, column=0, sticky="ew")
        row.grid_propagate(False)

        def enter(e,r=row): r.configure(fg_color=ACCENT_LIGHT)
        def leave(e,r=row,b=bg): r.configure(fg_color=b)
        def click(e,a=appt): self._open_detail(a)
        row.bind("<Enter>",enter); row.bind("<Leave>",leave)
        row.bind("<Button-1>",click)

        dt = appt.get("appointment_date","")
        time_str = (dt[:10]+"  "+dt[11:16] if len(dt)>=16
                    else dt[:10] if len(dt)>=10 else "—")

        CELLS = [
            (f"#{appt.get('appointment_id',0):04d}", 45,  TEXT_SECONDARY, "normal"),
            (appt.get("patient_name","—"),           200, TEXT_PRIMARY,   "bold"),
            (time_str,                               130, TEXT_SECONDARY, "normal"),
            (appt.get("visit_type","—"),             120, TEXT_SECONDARY, "normal"),
            ((appt.get("chief_complaint") or "—")[:25], 180, TEXT_SECONDARY, "normal"),
            (None,                                   110, s_fg,           "normal"),  # badge
            (f"{appt.get('total_amount',0):,.2f}",    95, ACCENT,         "normal"),
            (None,                                   105, None,           "normal"),  # action
        ]
        for col,(txt,w,color,weight) in enumerate(CELLS):
            if col == 5:  # status badge
                cell = ctk.CTkFrame(row, fg_color=s_bg, corner_radius=6)
                cell.grid(row=0, column=col, padx=(6,4), pady=10, sticky="w")
                cell.bind("<Button-1>",click)
                bl = ctk.CTkLabel(cell, text=status,
                                   font=ctk.CTkFont(FONT,10,"bold"),
                                   text_color=s_fg)
                bl.pack(padx=8, pady=3)
                bl.bind("<Button-1>",click)
            elif col == 7:  # action button
                if status in ("Scheduled","Pending"):
                    ctk.CTkButton(row, text="🟢 Arrived", width=95, height=32,
                                  font=ctk.CTkFont(FONT,10,"bold"),
                                  fg_color=TEAL, hover_color="#0F766E",
                                  corner_radius=6,
                                  command=lambda a=appt: self._mark_arrived(a)
                                  ).grid(row=0, column=col, padx=(4,10))
                elif status == "Waiting":
                    ctk.CTkButton(row, text="▶ Start", width=95, height=32,
                                  font=ctk.CTkFont(FONT,10,"bold"),
                                  fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                  corner_radius=6,
                                  command=lambda a=appt: self._mark_status(a,"In Progress")
                                  ).grid(row=0, column=col, padx=(4,10))
                elif status == "In Progress":
                    ctk.CTkButton(row, text="✅ Done", width=95, height=32,
                                  font=ctk.CTkFont(FONT,10,"bold"),
                                  fg_color=SUCCESS, hover_color="#15803D",
                                  corner_radius=6,
                                  command=lambda a=appt: self._mark_status(a,"Completed")
                                  ).grid(row=0, column=col, padx=(4,10))
                else:
                    ctk.CTkFrame(row, fg_color="transparent", width=95
                                 ).grid(row=0, column=col, padx=(4,10))
            else:
                lbl = ctk.CTkLabel(row, text=txt,
                                    font=ctk.CTkFont(FONT,12,weight=weight),
                                    text_color=color, width=w, anchor="w")
                lbl.grid(row=0, column=col,
                         padx=(12 if col==0 else 6,4), sticky="w")
                lbl.bind("<Enter>",enter)
                lbl.bind("<Leave>",leave)
                lbl.bind("<Button-1>",click)

    def _mark_arrived(self, appt):
        try:
            self.controller.on_update_appointment_status(
                appt["appointment_id"],"Waiting",None,None)
        except Exception:
            pass
        Toast.show(self._content,
                   f"🟢 {appt.get('patient_name','')} is now in the waiting room",
                   kind="info")
        self._load_queue()

    def _mark_status(self, appt, new_status):
        try:
            self.controller.on_update_appointment_status(
                appt["appointment_id"],new_status,None,None)
        except Exception:
            pass
        self._load_queue()

    def _open_new_appt(self):
        NewAppointmentWindow(parent_view=self, controller=self.controller,
                             on_saved=self._load_queue)

    def _open_detail(self, appt):
        self._selected_appt_id = appt["appointment_id"]
        win = AppointmentDetailWindow(parent_view=self, controller=self.controller,
                                       appt=appt, on_refresh=self._load_queue)
        self._detail_window = win

    def render_queue(self, appointments: list):
        self._queue = appointments
        for w in self._table_scroll.winfo_children():
            w.destroy()
        n = len(appointments)
        self._count_lbl.configure(
            text=f"{n} appointment{'s' if n!=1 else ''} today")
        waiting_n = sum(1 for a in appointments if a.get("status")=="Waiting")
        self._waiting_badge.configure(
            text=f"🟢 {waiting_n} waiting" if waiting_n else "")
        if not appointments:
            ctk.CTkLabel(self._table_scroll,
                         text="No appointments scheduled for today.",
                         font=ctk.CTkFont(FONT,13),
                         text_color=TEXT_SECONDARY
                         ).grid(row=0, column=0, pady=60)
        else:
            for idx,appt in enumerate(appointments):
                self._render_row(appt, idx)

    def clear_cart(self):
        if self._detail_window and self._detail_window.winfo_exists():
            self._detail_window.clear_cart()

    def add_cart_row(self, item):
        if self._detail_window and self._detail_window.winfo_exists():
            self._detail_window.add_cart_row(item)

    def set_total(self, text):
        if self._detail_window and self._detail_window.winfo_exists():
            self._detail_window.set_total(text)

    def show_form_message(self, message, success=True):
        try: Toast.show(self._content, message, success=success)
        except Exception: pass

    def show_feedback(self, message, success=True):
        self.show_form_message(message, success)

    def show_loading(self, state): pass