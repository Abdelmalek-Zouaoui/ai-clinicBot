"""
main.py
-------
Clinic Management System — Main Application Controller.
Refactored from Pharmacy Management System.

Entity mapping:
  Medicine     → Service (medical services / consultations)
  Supplier     → Patient
  Sales/POS    → Appointments / Visits
  Sale items   → Appointment services + Prescriptions
"""

import sys
import os

# ── Fix sys.path BEFORE any other imports ─────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
import threading
from datetime import datetime

# ── Dependency Check for Reportlab ────────────────────────────────────
try:
    from reportlab.lib.pagesizes import letter, A5
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas as rl_canvas
except ImportError:
    # Need temporary root tk to show messagebox before mainapp spins up
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependency",
        "ReportLab is not installed.\n"
        "Please run: pip install reportlab"
    )
    sys.exit(1)

# ── Model imports ──────────────────────────────────────────────────────
from model.db_manager       import DBManager
from model.user_model       import UserModel
from model.service_model    import ServiceModel
from model.patient_model    import PatientModel
from model.appointment_model import AppointmentModel
from model.prescription_model import PrescriptionModel

# ── View imports ───────────────────────────────────────────────────────
from view.login_view                 import LoginView
from view.admin.dashboard           import DashboardView
from view.admin.service_list        import ServiceListView, AddServiceView
from view.admin.patient_view        import PatientView
from view.admin.appointment_view    import AppointmentView
from view.admin.waiting_room_view   import WaitingRoomView
from view.admin.export_view         import ExportView
from view.admin.prescription_view   import PrescriptionView
from view.admin.settings_view       import SettingsView, UserMgmtView

# ── Utilities ──────────────────────────────────────────────────────────
from backup_manager import BackupManager
from localization   import t, LANG_CODES




# ══════════════════════════════════════════════════════════════════════
class ClinicApp(ctk.CTk):
    """
    Root application controller for the Clinic Management System.

    Responsibilities
    ----------------
    • Bootstrap all models and the DB connection
    • Own all navigation (navigate / show_* methods)
    • Own all business-logic callbacks invoked by Views
    • Run auto-backup on exit
    """

    def __init__(self):
        super().__init__()

        # ── Appearance ────────────────────────────────────────────────
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.geometry("1280x850")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self._frames = {}

        # ── Backup manager ────────────────────────────────────────────
        from backup_manager import BackupManager
        import sqlite3
        
        _db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "database", "clinic.db"
        )
        self.backup_mgr = BackupManager(db_path=_db_path)
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)

        # ── Database & Integrity Check ────────────────────────────────
        try:
            self.db = DBManager(_db_path)
            integrity = self.db.fetch_one("PRAGMA integrity_check")
            if not integrity or integrity[0].lower() != "ok":
                raise sqlite3.DatabaseError(f"Integrity check failed: {integrity[0] if integrity else 'Unknown'}")
        except sqlite3.DatabaseError as e:
            logging.error(f"[{datetime.now()}] Database corruption detected: {e}")
            messagebox.showwarning(
                "Database Corruption",
                "The database file appears to be corrupted.\nAttempting to restore from the latest backup..."
            )
            success, msg = self.backup_mgr.restore_latest_backup()
            if success:
                messagebox.showinfo("Restore Success", "Database restored successfully. Starting app...")
                self.db = DBManager(_db_path)
            else:
                messagebox.showerror("Restore Failed", f"Failed to restore database: {msg}\nPlease contact support.")
                sys.exit(1)

        # ── Models ────────────────────────────────────────────────────
        self.user_model   = UserModel(self.db)
        self.service_model = ServiceModel(self.db)
        self.patient_model = PatientModel(self.db)
        self.appt_model    = AppointmentModel(self.db)
        self.rx_model      = PrescriptionModel(self.db)

        # ── App-level state ───────────────────────────────────────────
        self._selected_image_path = None
        self._edit_mode           = False
        self._editing_service_id  = None
        self.current_lang         = "en"
        self.current_user: dict   = {}   # keys: user_id, username, role
        self.current_view         = None
        self._dashboard_debounce_timer = None

        # ── Appointment session ───────────────────────────────────────
        # Mirrors the old _cart pattern — current appointment being built.
        self._active_appointment_id: int | None = None
        self._appt_services: dict = {}   # service_id → {name, price, qty}

        # ── Bootstrap ─────────────────────────────────────────────────
        self._ensure_default_admin()
        self.title(f"🏥  {self.get_app_name()}  —  Clinic Management System")
        self.show_login_page()

    # ══════════════════════ BOOTSTRAP HELPERS ═════════════════════════

    def _ensure_default_admin(self):
        """Create a default admin account if none exists."""
        if not self.db.fetch_one(
                "SELECT 1 FROM users WHERE username=?", ("admin",)):
            self.user_model.add_user("admin", "admin123", "admin",
                                     full_name="System Administrator")

    # ══════════════════════ APP IDENTITY ══════════════════════════════

    def get_app_name(self) -> str:
        return self.db.get_setting("app_name", "CLINIC MANAGER")

    def get_all_identity_settings(self) -> dict:
        return {
            "app_name":     self.db.get_setting("app_name",     "CLINIC MANAGER"),
            "app_subtitle": self.db.get_setting("app_subtitle", "Medical Clinic — Algeria"),
            "app_address":  self.db.get_setting("app_address",  ""),
            "app_phone":    self.db.get_setting("app_phone",    ""),
        }

    def on_save_app_identity(self, data: dict):
        """Validate and persist all four clinic identity fields."""
        name = data.get("app_name", "").strip()
        if not name:
            if hasattr(self.current_view, "show_identity_message"):
                self.current_view.show_identity_message(
                    "App name cannot be empty.", success=False)
            return

        errors = []
        for key in ("app_name", "app_subtitle", "app_address", "app_phone"):
            if not self.db.set_setting(key, data.get(key, "").strip()):
                errors.append(key)

        if errors:
            if hasattr(self.current_view, "show_identity_message"):
                self.current_view.show_identity_message(
                    f"Failed to save: {', '.join(errors)}", success=False)
            return

        self.title(f"🏥  {name}  —  Clinic Management System")
        if hasattr(self.current_view, "show_identity_message"):
            self.current_view.show_identity_message(
                f"Saved!  Clinic name is now '{name}'", success=True)

    # ══════════════════════ SCREEN HELPERS ════════════════════════════

    def clear_screen(self):
        if hasattr(self, "current_view") and hasattr(self.current_view, "cleanup"):
            self.current_view.cleanup()
            
        if hasattr(self, "container"):
            for widget in self.container.winfo_children():
                if widget not in self._frames.values():
                    widget.destroy()
        else:
            for widget in self.winfo_children():
                widget.destroy()

    def show_frame(self, frame):
        self.update_idletasks()
        frame.grid(row=0, column=0, sticky="nsew")
        frame.lift()
        self.current_view = frame

    # ══════════════════════ NAVIGATION ════════════════════════════════

    # Pages that require admin role
    _ADMIN_ONLY_PAGES = {
        "dashboard", "services", "add_service",
        "patients", "prescriptions",
        "low_stock", "expiring",
        "users", "suppliers", "settings",
    }

    def navigate(self, page_key: str):
        """
        Central router with role-based access control.
          admin      → all pages
          others     → appointments + prescriptions + logout only
        """
        if page_key in self._ADMIN_ONLY_PAGES and not self._is_admin():
            messagebox.showwarning(
                "Access Denied",
                "⛔  Admin privileges required.\n\n"
                f"Your role ({self.current_user.get('role', 'employee')}) "
                "does not have access to this page."
            )
            return

        routes = {
            "dashboard":    self.show_dashboard,
            "services":     self.show_service_list,
            "add_service":  self.show_add_service,
            "appointments": self.show_appointments,
            "waiting_room": self.show_waiting_room,
            "export":       self.show_export,
            "prescriptions":self.show_prescriptions,
            "low_stock":    self.show_low_stock,
            "expiring":     self.show_expiring,
            "patients":     self.show_patients,
            "users":        self.show_users,
            "suppliers":    self.show_patients,   # alias for sidebar compat
            "settings":     self.show_settings,
            "logout":       self.show_login_page,
        }
        handler = routes.get(page_key)
        if handler:
            handler()

    # ── Individual page show methods ──────────────────────────────────

    def show_login_page(self):
        self.clear_screen()
        self.current_user = {}
        self._active_appointment_id = None
        self._appt_services = {}
        frame = LoginView(parent=self.container if hasattr(self, "container") else self, controller=self)
        self.show_frame(frame)

    def show_dashboard(self):
        self.clear_screen()
        frame = DashboardView(
            parent=self.container if hasattr(self, "container") else self, controller=self,
            lang=self.current_lang,
            role=self.current_user.get("role", "admin"),
            username=self.current_user.get("username", "Admin"),
        )
        self.show_frame(frame)
        self.refresh_dashboard_data()

    def show_service_list(self):
        self.clear_screen()
        frame = ServiceListView(parent=self.container if hasattr(self, "container") else self, controller=self)
        self.show_frame(frame)
        self.current_view.render_services(self.service_model.get_all_services())

    def show_add_service(self):
        self.clear_screen()
        self._edit_mode = False
        self._editing_service_id = None
        if "add_service" not in self._frames:
            self._frames["add_service"] = AddServiceView(parent=self.container if hasattr(self, "container") else self, controller=self)
        frame = self._frames["add_service"]
        self.show_frame(frame)

    def open_edit_service(self, service_data: dict):
        """Open AddServiceView pre-filled with an existing service's data."""
        self.clear_screen()
        self._edit_mode = True
        self._editing_service_id = service_data.get("service_id")
        if "add_service" not in self._frames:
            self._frames["add_service"] = AddServiceView(parent=self.container if hasattr(self, "container") else self, controller=self)
        frame = self._frames["add_service"]
        self.show_frame(frame)
        self.current_view.set_edit_mode(True)
        self.current_view.populate_form(service_data)

    def show_appointments(self):
        self.clear_screen()
        frame = AppointmentView(parent=self.container if hasattr(self, "container") else self, controller=self)
        self.show_frame(frame)
        self._refresh_appointment_view()

    def show_waiting_room(self):
        self.clear_screen()
        frame = WaitingRoomView(parent=self.container if hasattr(self, "container") else self, controller=self)
        self.show_frame(frame)

    def show_export(self):
        self.clear_screen()
        frame = ExportView(parent=self.container if hasattr(self, "container") else self, controller=self)
        self.show_frame(frame)

    def _refresh_appointment_view(self):
        if hasattr(self.current_view, "render_queue"):
            self.current_view.render_queue(self.appt_model.get_today_queue())
        if hasattr(self.current_view, "render_patients"):
            self.current_view.render_patients(
                self.patient_model.get_all_patients())

    def show_prescriptions(self):
        self.clear_screen()
        frame = PrescriptionView(parent=self.container if hasattr(self, "container") else self, controller=self)
        self.show_frame(frame)
        if hasattr(self.current_view, "render_patients"):
            self.current_view.render_patients(
                self.patient_model.get_all_patients())

    def show_patients(self):
        self.clear_screen()
        frame = PatientView(parent=self.container if hasattr(self, "container") else self, controller=self)
        self.show_frame(frame)
        self._refresh_patient_roster()

    def _refresh_patient_roster(self):
        if hasattr(self.current_view, "render_patients"):
            self.current_view.render_patients(
                self.patient_model.get_all_patients())

    def show_low_stock(self):
        """Redirect to services view — inactive services shown there."""
        self.show_service_list()

    def show_expiring(self):
        """Redirect to appointments view — cancelled appointments shown there."""
        self.show_appointments()

    def show_users(self):
        self.clear_screen()
        frame = UserMgmtView(parent=self.container if hasattr(self, "container") else self, controller=self)
        self.show_frame(frame)
        self.current_view.render(self.user_model.get_all_users())

    def show_settings(self):
        self.clear_screen()
        if "settings" not in self._frames:
            self._frames["settings"] = SettingsView(parent=self.container if hasattr(self, "container") else self, controller=self)
        frame = self._frames["settings"]
        self.show_frame(frame)
        if hasattr(self.current_view, "set_identity_fields"):
            self.current_view.set_identity_fields(
                self.get_all_identity_settings())
        self._refresh_settings_view()

    def _refresh_settings_view(self):
        if hasattr(self.current_view, "refresh"):
            self.current_view.refresh(
                self.backup_mgr.get_backup_stats(),
                self.backup_mgr.get_backup_list()
            )

    # ══════════════════════ LANGUAGE ══════════════════════════════════

    def switch_language(self, lang_code: str):
        self.current_lang = lang_code
        if hasattr(self.current_view, "apply_lang"):
            self.current_view.apply_lang(lang_code)

    # ══════════════════════ AUTHENTICATION ════════════════════════════

    def on_login(self):
        u, p = self.current_view.get_credentials()
        result = self.user_model.authenticate(u, p)
        if not result:
            self.current_view.show_error(
                t("msg_invalid_login", self.current_lang))
            return
        user_id, username, role = result
        self.current_user = {
            "user_id": user_id, "username": username, "role": role}
        if self._is_admin():
            self.show_dashboard()
        else:
            # Non-admin staff land on appointments page
            self.show_appointments()

    def _is_admin(self) -> bool:
        return self.current_user.get("role") == "admin"

    # ══════════════════════ DASHBOARD DATA ════════════════════════════

    def refresh_dashboard_data(self):
        """Debounced request to fetch today's clinic stats."""
        if self._dashboard_debounce_timer:
            self.after_cancel(self._dashboard_debounce_timer)
        self._dashboard_debounce_timer = self.after(300, self._execute_refresh_dashboard_data)

    def _execute_refresh_dashboard_data(self):
        """Fetch today's clinic stats and push them to the dashboard view.
        Safe to call from any view — all calls are guarded with hasattr."""
        try:
            stats    = self.appt_model.get_today_stats()
            patients = len(self.patient_model.get_all_patients())
        except Exception:
            return

        if hasattr(self.current_view, "update_stat_cards"):
            self.current_view.update_stat_cards(
                total    = str(patients),
                low      = str(stats["waiting"]),
                expiring = str(stats["completed"]),
                sales    = f"{stats['revenue']:,.2f} DA",
            )

        if hasattr(self.current_view, "update_waiting_list"):
            self.current_view.update_waiting_list(
                self.appt_model.get_waiting())

        if hasattr(self.current_view, "update_chart"):
            try:
                self.current_view.update_chart(
                    self.appt_model.get_monthly_revenue())
            except Exception as e:
                print(f"[chart] update_chart error (non-fatal): {e}")

    def get_monthly_sales_data(self) -> dict:
        """Alias used by DashboardView.update_chart — delegates to appt_model."""
        return self.appt_model.get_monthly_revenue()

    # ══════════════════════ SERVICE MANAGEMENT ════════════════════════

    def on_save_service(self):
        """Validate form data and create or update a service."""
        data = self.current_view.get_form_data()
        name  = data.get("name", "").strip()
        code  = data.get("barcode", "").strip()   # reuses barcode field name

        if not name:
            self.current_view.show_bar_message(
                "Service name is required.", success=False)
            return

        try:
            price        = float(data.get("selling_price") or data.get("price") or 0)
            duration_min = int(data.get("quantity") or 30)
        except ValueError:
            self.current_view.show_bar_message(
                "Invalid price or duration.", success=False)
            return

        if self._edit_mode:
            ok = self.service_model.update_service(
                self._editing_service_id,
                name         = name,
                category     = data.get("category", ""),
                price        = price,
                duration_min = duration_min,
                description  = data.get("notes", ""),
            )
            if ok:
                self._edit_mode = False
                self.current_view.show_bar_message(
                    "Service updated successfully!", success=True)
                self.current_view.set_edit_mode(False)
            else:
                self.current_view.show_bar_message(
                    "Error: update failed.", success=False)
        else:
            if code and self.service_model.service_exists(code):
                self.current_view.show_bar_message(
                    "Service code already exists.", success=False)
                return
            ok = self.service_model.add_service(
                code         = code,
                name         = name,
                category     = data.get("category", "Consultation"),
                price        = price,
                duration_min = duration_min,
                description  = data.get("notes", ""),
            )
            if ok:
                self.current_view.show_bar_message(
                    "Service saved successfully!", success=True)
                self.current_view.clear_form()
            else:
                self.current_view.show_bar_message(
                    "Error: could not save.", success=False)

    def on_search(self, query: str):
        """Live search — dispatched to whichever list view is active."""
        if hasattr(self.current_view, "render_services"):
            self.current_view.render_services(
                self.service_model.search_service(query))
        elif hasattr(self.current_view, "render_patients"):
            self.current_view.render_patients(
                self.patient_model.search_patient(query))

    def on_delete_medicine(self, service_id):
        """Adapter — old name kept for AlertListView compatibility."""
        self.on_delete_service(service_id)

    def on_delete_service(self, service_id):
        if self.service_model.delete_service(service_id):
            self.show_service_list()

    # ── Image browsing (reused by AddServiceView) ─────────────────────

    def on_browse_image(self):
        from PIL import Image
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp")]
        )
        if not path:
            return
        try:
            img = Image.open(path)
            self._selected_image_path = path
            self.current_view.set_image_preview(img, os.path.basename(path))
        except Exception as e:
            self.current_view.show_bar_message(
                f"Could not open image: {e}", success=False)

    def on_remove_image(self):
        self._selected_image_path = None

    # ══════════════════════ PATIENT MANAGEMENT ════════════════════════

    def on_save_patient(self, data: dict):
        """Validate and save a new patient record."""
        try:
            name = data.get("name", "").strip()
            if not name or len(name) < 2:
                self.current_view.show_form_message(
                    "Patient full name is required (min 2 chars).", success=False)
                return

            phone = data.get("phone", "").strip()
            if phone:
                if not phone.isdigit() or len(phone) < 9 or len(phone) > 15:
                    self.current_view.show_form_message(
                        "Phone must be digits only and 9-15 characters long.", success=False)
                    return
                if self.patient_model.patient_exists_by_phone(phone):
                    self.current_view.show_form_message(
                        f"A patient with phone '{phone}' already exists.", success=False)
                    return

            dob = data.get("date_of_birth", "").strip()
            if dob:
                try:
                    dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
                    if dob_date > datetime.now().date():
                        self.current_view.show_form_message(
                            "Date of birth cannot be in the future.", success=False)
                        return
                except ValueError:
                    self.current_view.show_form_message(
                        "Date of birth must be in YYYY-MM-DD format.", success=False)
                    return

            email = data.get("email", "").strip()
            if email:
                import re
                if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    self.current_view.show_form_message(
                        "Invalid email address format.", success=False)
                    return

            blood_type = data.get("blood_type", "").strip().upper()
            valid_blood_types = {"", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
            if blood_type not in valid_blood_types:
                self.current_view.show_form_message(
                    "Invalid blood type.", success=False)
                return

            pid = self.patient_model.add_patient(
                full_name       = name,
                date_of_birth   = dob,
                gender          = data.get("gender", "Other"),
                phone           = phone,
                email           = email,
                address         = data.get("address", ""),
                wilaya          = data.get("wilaya", ""),
                blood_type      = blood_type,
                allergies       = data.get("allergies", ""),
                medical_history = data.get("medical_history", ""),
                notes           = data.get("notes", ""),
            )
            if pid:
                self.current_view.show_form_message(
                    f"Patient '{name}' registered successfully!", success=True)
                if hasattr(self.current_view, "clear_patient_form"):
                    self.current_view.clear_patient_form()
                self._refresh_patient_roster()
            else:
                self.current_view.show_form_message(
                    "Failed to save patient.", success=False)
        except Exception as e:
            logging.error(f"Error in on_save_patient: {e}", exc_info=True)
            self.current_view.show_form_message(f"Registration failed: {str(e)}", success=False)

    def on_update_patient(self, patient_id: int, data: dict):
        """Validate and update an existing patient record."""
        name = data.get("name", "").strip()
        if not name or len(name) < 2:
            self.current_view.show_form_message(
                "Patient full name is required (min 2 chars).", success=False)
            return

        phone = data.get("phone", "").strip()
        if phone:
            if not phone.isdigit() or len(phone) < 9 or len(phone) > 15:
                self.current_view.show_form_message(
                    "Phone must be digits only and 9-15 characters long.", success=False)
                return

        dob = data.get("date_of_birth", "").strip()
        if dob:
            try:
                dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
                if dob_date > datetime.now().date():
                    self.current_view.show_form_message(
                        "Date of birth cannot be in the future.", success=False)
                    return
            except ValueError:
                self.current_view.show_form_message(
                    "Date of birth must be in YYYY-MM-DD format.", success=False)
                return

        email = data.get("email", "").strip()
        if email:
            import re
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                self.current_view.show_form_message(
                    "Invalid email address format.", success=False)
                return

        blood_type = data.get("blood_type", "").strip().upper()
        valid_blood_types = {"", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
        if blood_type not in valid_blood_types:
            self.current_view.show_form_message(
                "Invalid blood type.", success=False)
            return

        ok = self.patient_model.update_patient(
            patient_id,
            full_name       = name,
            date_of_birth   = dob,
            gender          = data.get("gender", "Other"),
            phone           = phone,
            email           = email,
            address         = data.get("address", ""),
            wilaya          = data.get("wilaya", ""),
            blood_type      = blood_type,
            allergies       = data.get("allergies", ""),
            medical_history = data.get("medical_history", ""),
            notes           = data.get("notes", ""),
        )
        if ok:
            self.current_view.show_form_message(
                f"Patient '{name}' updated successfully!", success=True)
            self._refresh_patient_roster()
        else:
            self.current_view.show_form_message(
                "Failed to update patient.", success=False)

    def on_delete_patient(self, patient_id: int, name: str):
        ok = self.patient_model.delete_patient(patient_id)
        if ok:
            self.current_view.show_form_message(
                f"'{name}' removed.", success=True)
            self._refresh_patient_roster()
        else:
            self.current_view.show_form_message(
                "Delete failed.", success=False)

    def on_select_patient(self, patient_id: int):
        """Load a patient's appointment history into the detail panel."""
        patient = self.patient_model.get_patient(patient_id)
        history = self.db.fetch_all(
            """SELECT appointment_id, appointment_date, status,
                      visit_type, diagnosis, total_amount
               FROM appointments WHERE patient_id=?
               ORDER BY appointment_date DESC LIMIT 20""",
            (patient_id,)
        )
        if hasattr(self.current_view, "render_patient_history"):
            self.current_view.render_patient_history(
                patient or {}, history or [])

    # ══════════════════════ APPOINTMENT MANAGEMENT ════════════════════

    def on_create_appointment(self, data: dict):
        """
        Validate and create a new appointment.
        data keys: patient_id, visit_type, chief_complaint
        """
        try:
            patient_id = data.get("patient_id")
            if not patient_id:
                if hasattr(self.current_view, "show_form_message"):
                    self.current_view.show_form_message(
                        "Select a patient first.", success=False)
                return

            appt_id = self.appt_model.create_appointment(
                patient_id        = patient_id,
                doctor_id         = self.current_user.get("user_id"),
                visit_type        = data.get("visit_type", "Consultation"),
                chief_complaint   = data.get("chief_complaint", ""),
                appointment_date  = data.get("appointment_date", None),
            )
            if appt_id:
                self._active_appointment_id = appt_id
                if hasattr(self.current_view, "show_form_message"):
                    self.current_view.show_form_message(
                        "Appointment created!", success=True)
                self._refresh_appointment_view()
                self.refresh_dashboard_data()
            else:
                if hasattr(self.current_view, "show_form_message"):
                    self.current_view.show_form_message(
                        "Failed to create appointment.", success=False)
        except Exception as e:
            logging.error(f"Error in on_create_appointment: {e}", exc_info=True)
            if hasattr(self.current_view, "show_form_message"):
                self.current_view.show_form_message(f"Appointment failed: {str(e)}", success=False)

    def on_update_appointment_status(self, appointment_id: int,
                                      status: str,
                                      diagnosis: str = "",
                                      notes: str = ""):
        """Called from the appointment queue view."""
        ok = self.appt_model.update_status(
            appointment_id, status, diagnosis, notes)
        if ok:
            self._refresh_appointment_view()
            self.refresh_dashboard_data()

    def on_add_service_to_appointment(self, barcode: str):
        """
        Adapter used by AppointmentView (mirrors old on_add_to_cart).
        Looks up a service by code and adds it to the active appointment session.
        """
        if not self._active_appointment_id:
            self.current_view.show_feedback(
                "Create an appointment first.", success=False)
            return

        results = self.service_model.search_service(barcode)
        if not results:
            self.current_view.show_feedback(
                "Service not found!", success=False)
            return

        svc = results[0]
        sid   = svc["service_id"]
        name  = svc["name"]
        price = float(svc.get("price", 0))

        if sid in self._appt_services:
            self._appt_services[sid]["qty"] += 1
        else:
            self._appt_services[sid] = {
                "service_id": sid, "name": name,
                "price": price, "qty": 1,
            }

        self._update_appointment_ui()
        self.current_view.show_feedback(
            f"Added: {name}", success=True)

    def on_remove_from_appointment(self, service_id: int):
        if service_id in self._appt_services:
            del self._appt_services[service_id]
        self._update_appointment_ui()

    def on_qty_change(self, service_id: int, delta: int):
        if service_id not in self._appt_services:
            return
        self._appt_services[service_id]["qty"] += delta
        if self._appt_services[service_id]["qty"] <= 0:
            del self._appt_services[service_id]
        self._update_appointment_ui()

    def on_clear_cart(self):
        self._appt_services = {}
        if hasattr(self.current_view, "clear_cart"):
            self.current_view.clear_cart()
        if hasattr(self.current_view, "set_total"):
            self.current_view.set_total("0.00 DA")

    def _update_appointment_ui(self):
        """Push the current service list to the appointment view."""
        if not hasattr(self.current_view, "clear_cart"):
            return
        self.current_view.clear_cart()
        total = 0.0
        for sid, item in self._appt_services.items():
            subtotal = item["price"] * item["qty"]
            total += subtotal
            self.current_view.add_cart_row({
                "barcode":  sid,
                "name":     item["name"],
                "price":    f"{item['price']:.2f}",
                "qty":      item["qty"],
                "subtotal": f"{subtotal:.2f}",
            })
        self.current_view.set_total(f"{total:.2f} DA")

    def on_checkout(self):
        """Finalise the appointment — record services, update total, print receipt."""
        if not self._appt_services or not self._active_appointment_id:
            return
        if hasattr(self.current_view, "show_loading"):
            self.current_view.show_loading(True)

        grand_total = 0.0
        for sid, item in self._appt_services.items():
            subtotal = item["price"] * item["qty"]
            grand_total += subtotal
            self.appt_model.add_service_to_appointment(
                appointment_id = self._active_appointment_id,
                service_id     = sid,
                unit_price     = item["price"],
                quantity       = item["qty"],
            )

        self.appt_model.update_total(self._active_appointment_id, grand_total)
        self.appt_model.update_status(
            self._active_appointment_id, "Completed")

        threading.Thread(target=self._finalize_checkout_thread, daemon=True).start()

    def _finalize_checkout_thread(self):
        """Runs in background to generate PDF, preventing UI freeze."""
        self._generate_pdf_receipt()
        self.after(0, self._on_checkout_complete)

    def _on_checkout_complete(self):
        """Safely updates UI from the main thread after PDF is generated."""
        if hasattr(self.current_view, "show_loading"):
            self.current_view.show_loading(False)
        if hasattr(self.current_view, "clear_cart"):
            self.current_view.clear_cart()

        completed_id = self._active_appointment_id
        self._active_appointment_id = None
        self._appt_services = {}

        self.refresh_dashboard_data()
        messagebox.showinfo("Visit Complete",
                            "✅  Visit completed and receipt generated!")

    # ══════════════════════ PRESCRIPTION MANAGEMENT ═══════════════════

    def on_create_prescription(self, data: dict):
        """
        Create a prescription record and generate a PDF.
        data keys: patient_id, appointment_id (optional), notes, items[]
          item keys: medicine_name, dosage, frequency, duration, instructions
        """
        try:
            patient_id = data.get("patient_id")
            if not patient_id:
                if hasattr(self.current_view, "show_form_message"):
                    self.current_view.show_form_message(
                        "Select a patient first.", success=False)
                return

            items = data.get("items", [])
            if not items:
                if hasattr(self.current_view, "show_form_message"):
                    self.current_view.show_form_message(
                        "Add at least one medicine.", success=False)
                return

            rx_id = self.rx_model.create_prescription(
                patient_id     = patient_id,
                appointment_id = data.get("appointment_id"),
                doctor_id      = self.current_user.get("user_id"),
                notes          = data.get("notes", ""),
            )
            if not rx_id:
                if hasattr(self.current_view, "show_form_message"):
                    self.current_view.show_form_message(
                        "Failed to create prescription.", success=False)
                return

            for item in items:
                self.rx_model.add_item(
                    rx_id,
                    medicine_name = item.get("medicine_name", ""),
                    dosage        = item.get("dosage", ""),
                    frequency     = item.get("frequency", ""),
                    duration      = item.get("duration", ""),
                    instructions  = item.get("instructions", ""),
                )

            self._generate_prescription_pdf(rx_id)
            if hasattr(self.current_view, "show_form_message"):
                self.current_view.show_form_message(
                    "Prescription saved and printed!", success=True)
            if hasattr(self.current_view, "clear_prescription_form"):
                self.current_view.clear_prescription_form()
        except Exception as e:
            logging.error(f"Error in on_create_prescription: {e}", exc_info=True)
            if hasattr(self.current_view, "show_form_message"):
                self.current_view.show_form_message(f"Prescription failed: {str(e)}", success=False)

    # ══════════════════════ PDF GENERATION ════════════════════════════

    def _generate_pdf_receipt(self):
        """
        Generate an 80 mm thermal receipt for the completed visit.
        Same layout logic as the original pharmacy invoice.
        """
        if not self._appt_services and not self._active_appointment_id:
            # Build from last completed appointment's services
            pass  # services already cleared — use snapshot if available

        base_dir     = os.path.dirname(os.path.abspath(__file__))
        receipts_dir = os.path.join(base_dir, "receipts")
        os.makedirs(receipts_dir, exist_ok=True)

        receipt_no = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path  = os.path.join(receipts_dir, f"receipt_{receipt_no}.pdf")

        MM     = 2.834645669
        W      = 80 * MM
        MARGIN = 4 * MM
        USABLE = W - 2 * MARGIN

        clinic_name = self.get_app_name()
        clinic_sub  = self.db.get_setting("app_subtitle", "Medical Clinic — Algeria")
        clinic_addr = self.db.get_setting("app_address", "")
        clinic_tel  = self.db.get_setting("app_phone", "")

        _extra = (10 if clinic_addr else 0) + (10 if clinic_tel else 0)
        HEADER_H = 90 + _extra
        n_items  = len(self._appt_services) if self._appt_services else 1
        PAGE_H   = HEADER_H + 28 + (n_items * 18) + 55 + 20

        c = rl_canvas.Canvas(file_path, pagesize=(W, PAGE_H))
        y = PAGE_H - 10

        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(W / 2, y, clinic_name.upper())
        y -= 14
        c.setFont("Helvetica", 7)
        c.drawCentredString(W / 2, y, clinic_sub)
        y -= 10
        if clinic_addr:
            c.drawCentredString(W / 2, y, clinic_addr)
            y -= 10
        if clinic_tel:
            c.drawCentredString(W / 2, y, f"Tél: {clinic_tel}")
            y -= 10

        c.setLineWidth(0.5)
        c.line(MARGIN, y, W - MARGIN, y)
        y -= 10
        c.setFont("Helvetica", 7)
        c.drawString(MARGIN, y,
                     f"Date:    {datetime.now().strftime('%d/%m/%Y  %H:%M')}")
        y -= 10
        c.drawString(MARGIN, y, f"Receipt: #{receipt_no[-6:]}")
        y -= 10
        c.setLineWidth(1)
        c.line(MARGIN, y, W - MARGIN, y)
        y -= 14

        X_NAME  = MARGIN
        X_QTY   = MARGIN + 112
        X_PRICE = MARGIN + 145
        X_SUB   = MARGIN + USABLE

        c.setFont("Helvetica-Bold", 7)
        c.drawString(X_NAME, y, "Service")
        c.drawRightString(X_QTY,   y, "Qty")
        c.drawRightString(X_PRICE, y, "Price")
        c.drawRightString(X_SUB,   y, "Total")
        y -= 4
        c.setLineWidth(0.5)
        c.line(MARGIN, y, W - MARGIN, y)
        y -= 12

        grand_total = 0.0
        c.setFont("Helvetica", 7)
        services_to_print = (
            self._appt_services.items()
            if self._appt_services
            else []
        )
        for sid, item in services_to_print:
            subtotal     = item["price"] * item["qty"]
            grand_total += subtotal
            name = str(item["name"])
            if len(name) > 18:
                name = name[:17] + "…"
            c.drawString(X_NAME,  y, name)
            c.drawRightString(X_QTY,   y, str(item["qty"]))
            c.drawRightString(X_PRICE, y, f"{item['price']:.2f}")
            c.drawRightString(X_SUB,   y, f"{subtotal:.2f}")
            y -= 18

        c.setLineWidth(1)
        c.line(MARGIN, y, W - MARGIN, y)
        y -= 14
        c.setFont("Helvetica-Bold", 9)
        c.drawString(MARGIN, y, "TOTAL")
        c.drawRightString(X_SUB, y, f"{grand_total:.2f} DA")
        y -= 18
        c.setLineWidth(0.5)
        c.line(MARGIN, y, W - MARGIN, y)
        y -= 12
        c.setFont("Helvetica", 7)
        c.drawCentredString(W / 2, y, "Thank you for your visit!")

        c.save()
        try:
            os.startfile(file_path)
        except Exception:
            pass   # non-Windows: silently skip auto-open

    def _generate_prescription_pdf(self, rx_id: int):
        """Generate a clean A5 prescription PDF and open it."""
        rx = self.rx_model.get_prescription(rx_id)
        if not rx:
            return

        base_dir  = os.path.dirname(os.path.abspath(__file__))
        rx_dir    = os.path.join(base_dir, "prescriptions")
        os.makedirs(rx_dir, exist_ok=True)
        file_path = os.path.join(rx_dir, f"rx_{rx_id:04d}.pdf")

        W, H = A5
        c = rl_canvas.Canvas(file_path, pagesize=A5)

        # ── Clinic header background ──────────────────────────────────────
        c.setFillColorRGB(0.09, 0.58, 0.53)   # teal #0D9488
        c.rect(0, H - 3.2*cm, W, 3.2*cm, fill=1, stroke=0)

        # Clinic name
        clinic_name     = self.get_app_name()
        clinic_subtitle = self.db.get_setting("app_subtitle",
                                               "Medical Clinic")
        clinic_phone    = self.db.get_setting("app_phone", "")
        clinic_address  = self.db.get_setting("app_address", "")

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 15)
        c.drawString(1.5*cm, H - 1.3*cm, clinic_name.upper())
        c.setFont("Helvetica", 9)
        c.drawString(1.5*cm, H - 1.9*cm, clinic_subtitle)
        info_parts = []
        if clinic_phone:   info_parts.append(f"📞 {clinic_phone}")
        if clinic_address: info_parts.append(f"📍 {clinic_address}")
        if info_parts:
            c.drawString(1.5*cm, H - 2.5*cm, "  ·  ".join(info_parts))

        # Rx badge top-right
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawRightString(W - 1.5*cm, H - 1.8*cm, "℞")

        # ── Patient info band ─────────────────────────────────────────────
        c.setFillColorRGB(0.93, 1.0, 0.98)    # very light teal
        c.rect(0, H - 5.0*cm, W, 1.6*cm, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#1A202C"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1.5*cm, H - 3.8*cm,
                     f"Patient:  {rx['patient_name']}")
        issued = rx.get("issued_date","")[:10] or \
                 datetime.now().strftime("%Y-%m-%d")
        c.setFont("Helvetica", 9)
        c.drawString(1.5*cm, H - 4.35*cm,
                     f"Date: {issued}     Ref: Rx-{rx_id:04d}")

        # ── Divider ───────────────────────────────────────────────────────
        y = H - 5.3*cm
        c.setStrokeColorRGB(0.09, 0.58, 0.53)
        c.setLineWidth(1.5)
        c.line(1.5*cm, y, W - 1.5*cm, y)

        # ── Rx symbol ─────────────────────────────────────────────────────
        y -= 0.7*cm
        c.setFillColorRGB(0.09, 0.58, 0.53)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(1.5*cm, y, "℞")
        y -= 0.6*cm

        # ── Medicine items ────────────────────────────────────────────────
        c.setFillColor(colors.HexColor("#1A202C"))
        for i, item in enumerate(rx.get("items", []), 1):
            # Medicine name + dosage
            med_line = f"{i}.  {item['medicine_name']}"
            if item.get("dosage"):
                med_line += f"   —   {item['dosage']}"
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.HexColor("#1A202C"))
            c.drawString(1.8*cm, y, med_line)
            y -= 0.45*cm

            # Frequency / Duration / Instructions
            details = []
            if item.get("frequency"):    details.append(item["frequency"])
            if item.get("duration"):     details.append(item["duration"])
            if item.get("instructions"): details.append(item["instructions"])
            if details:
                c.setFont("Helvetica", 9)
                c.setFillColor(colors.HexColor("#64748B"))
                c.drawString(2.4*cm, y, "  ·  ".join(details))
                y -= 0.4*cm

            y -= 0.15*cm

            # Stop if running off page
            if y < 3.5*cm:
                c.setFont("Helvetica-Oblique", 8)
                c.setFillColor(colors.HexColor("#64748B"))
                c.drawString(1.5*cm, y, "(continued on next page…)")
                break

        # ── Notes ─────────────────────────────────────────────────────────
        if rx.get("notes") and y > 3.5*cm:
            y -= 0.3*cm
            c.setStrokeColorRGB(0.09, 0.58, 0.53)
            c.setLineWidth(0.5)
            c.line(1.5*cm, y, W - 1.5*cm, y)
            y -= 0.5*cm
            c.setFont("Helvetica-BoldOblique", 9)
            c.setFillColor(colors.HexColor("#1A202C"))
            c.drawString(1.5*cm, y, "Notes:")
            y -= 0.4*cm
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(colors.HexColor("#64748B"))
            # Word-wrap notes
            words = rx["notes"].split()
            line  = ""
            for word in words:
                test = f"{line} {word}".strip()
                if c.stringWidth(test, "Helvetica-Oblique", 9) < (W - 3.5*cm):
                    line = test
                else:
                    c.drawString(1.5*cm, y, line)
                    y -= 0.4*cm
                    line = word
                    if y < 3.5*cm:
                        break
            if line and y >= 3.5*cm:
                c.drawString(1.5*cm, y, line)

        # ── Signature line ────────────────────────────────────────────────
        sig_y = 2.2*cm
        c.setStrokeColor(colors.HexColor("#1A202C"))
        c.setLineWidth(0.5)
        c.line(W - 6*cm, sig_y, W - 1.5*cm, sig_y)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#64748B"))
        c.drawCentredString(W - 3.75*cm, sig_y - 0.4*cm,
                             "Doctor's Signature")

        # ── Footer ────────────────────────────────────────────────────────
        c.setFillColorRGB(0.09, 0.58, 0.53)
        c.rect(0, 0, W, 1.2*cm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 7)
        c.drawCentredString(W/2, 0.45*cm,
                             f"{clinic_name}  ·  This prescription is valid for 3 months")

        c.save()

        # Open the PDF
        try:
            os.startfile(file_path)          # Windows
        except AttributeError:
            try:
                import subprocess
                subprocess.Popen(["xdg-open", file_path])  # Linux
            except Exception:
                pass
        except Exception:
            pass

        return file_path

    def reprint_prescription_pdf(self, rx_id: int):
        """Re-generate and open an already-saved prescription PDF."""
        path = self._generate_prescription_pdf(rx_id)
        if path:
            if hasattr(self.current_view, "show_form_message"):
                self.current_view.show_form_message(
                    f"PDF opened: rx_{rx_id:04d}.pdf", success=True)

    # ══════════════════════ USER / EMPLOYEE MANAGEMENT ════════════════

    def on_create_employee(self, data: dict):
        username         = data.get("username", "").strip()
        password         = data.get("password", "")
        confirm_password = data.get("confirm_password", "")
        full_name        = data.get("full_name", "").strip()
        phone            = data.get("phone", "").strip()
        role             = data.get("role", "employee")
        notes            = data.get("notes", "").strip()

        if not username:
            self.current_view.show_form_message(
                "Username is required.", success=False); return
        if len(username) < 3:
            self.current_view.show_form_message(
                "Username must be at least 3 characters.", success=False); return
        if not password:
            self.current_view.show_form_message(
                "Password is required.", success=False); return
        if len(password) < 6:
            self.current_view.show_form_message(
                "Password must be at least 6 characters.", success=False); return
        if password != confirm_password:
            self.current_view.show_form_message(
                "Passwords do not match.", success=False); return
        if self.user_model.user_exists(username):
            self.current_view.show_form_message(
                f"Username '{username}' is already taken.", success=False); return

        ok = self.user_model.add_user(
            username, password, role,
            full_name=full_name, phone=phone, notes=notes)
        if ok:
            self.current_view.show_form_message(
                f"Account @{username} created successfully!", success=True)
            self.current_view.clear_form()
            self.current_view.render(self.user_model.get_all_users())
        else:
            self.current_view.show_form_message(
                "Error: could not create account.", success=False)

    def on_delete_employee(self, user_id: int, username: str):
        ok = self.user_model.delete_user(user_id)
        if ok:
            self.current_view.render(self.user_model.get_all_users())
        else:
            messagebox.showerror(
                "Cannot Delete",
                f"Could not delete @{username}.\n"
                "You cannot remove the last admin account."
            )

    # ══════════════════════ SUPPLIER ALIAS (settings compat) ══════════

    # Settings view + AlertListView may call these — kept as aliases
    def on_save_supplier(self, data: dict):
        self.on_save_patient(data)

    def on_delete_supplier(self, supplier_id: int, name: str):
        self.on_delete_patient(supplier_id, name)

    def on_delete_patient(self, patient_id: int, name: str):
        ok = self.patient_model.delete_patient(patient_id)
        msg = f"'{name}' removed." if ok else "Delete failed."
        if hasattr(self.current_view, "show_form_message"):
            self.current_view.show_form_message(msg, success=ok)
        if ok:
            self._refresh_patient_roster()

    def on_select_supplier(self, supplier_id: int):
        self.on_select_patient(supplier_id)

    def on_add_supplier_medicine(self, data: dict):
        pass   # not used in clinic context

    def on_delete_supplier_medicine(self, row_id: int, supplier_id: int):
        pass   # not used in clinic context

    # ══════════════════════ BACKUP / SETTINGS ═════════════════════════

    def get_backup_stats(self) -> dict:
        return self.backup_mgr.get_backup_stats()

    def get_backup_list(self) -> list:
        return self.backup_mgr.get_backup_list()

    def on_manual_backup_here(self):
        ok, msg = self.backup_mgr.auto_backup()
        if ok:
            self.current_view.show_backup_message(
                f"Backup saved: {os.path.basename(msg)}", success=True)
        else:
            self.current_view.show_backup_message(
                f"Backup failed: {msg}", success=False)
        self._refresh_settings_view()

    def on_manual_backup_choose(self):
        dest = filedialog.askdirectory(
            title="Choose backup destination folder", mustexist=True)
        if not dest:
            return
        ok, msg = self.backup_mgr.manual_backup(dest)
        if ok:
            self.current_view.show_backup_message(
                f"Saved to: {os.path.basename(msg)}", success=True)
        else:
            self.current_view.show_backup_message(
                f"Failed: {msg}", success=False)

    def on_delete_old_backups(self):
        confirm = messagebox.askyesno(
            "Delete Old Backups",
            "This will permanently delete all automatic backup files\n"
            "older than 30 days from the backup folder.\n\nAre you sure?",
            icon="warning"
        )
        if not confirm:
            return
        removed = self.backup_mgr.purge_old_backups()
        msg = (f"Deleted {removed} old backup file(s)." if removed
               else "No backups older than 30 days found.")
        self.current_view.show_backup_message(msg, success=True)
        self._refresh_settings_view()

    # ══════════════════════ APP LIFECYCLE ═════════════════════════════

    def _on_app_close(self):
        logging.info("App closing — running auto-backup…")
        try:
            ok, msg = self.backup_mgr.auto_backup()
            if ok:
                logging.info(f"Auto-backup on exit: {msg}")
            else:
                logging.warning(f"Auto-backup failed on exit: {msg}")
        except Exception as e:
            logging.error(f"Unexpected backup error on exit: {e}")
        finally:
            self.destroy()


# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = ClinicApp()
    app.mainloop()