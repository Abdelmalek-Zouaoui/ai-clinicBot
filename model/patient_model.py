# patient_model.py
class PatientModel:
    def __init__(self, db_manager):
        self.db = db_manager

    def add_patient(self, full_name, date_of_birth="", gender="Other",
                    phone="", email="", address="", wilaya="",
                    blood_type="", allergies="",
                    medical_history="", notes=""):
        ok = self.db.execute_query(
            """INSERT INTO patients
               (full_name, date_of_birth, gender, phone, email,
                address, wilaya, blood_type, allergies,
                medical_history, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (full_name, date_of_birth, gender, phone, email,
             address, wilaya, blood_type, allergies,
             medical_history, notes)
        )
        if not ok:
            return None
        row = self.db.fetch_one(
            "SELECT MAX(patient_id) FROM patients", ())
        return row[0] if row else None

    def get_all_patients(self) -> list[dict]:
        rows = self.db.fetch_all(
            """SELECT patient_id, full_name, date_of_birth, gender,
                      phone, email, address, wilaya, blood_type,
                      allergies, medical_history, notes, created_at
               FROM patients ORDER BY full_name""", ()
        )
        return [self._row(r) for r in (rows or [])]

    def get_patient(self, patient_id) -> dict | None:
        row = self.db.fetch_one(
            """SELECT patient_id, full_name, date_of_birth, gender,
                      phone, email, address, wilaya, blood_type,
                      allergies, medical_history, notes, created_at
               FROM patients WHERE patient_id=?""", (patient_id,)
        )
        return self._row(row) if row else None

    def search_patient(self, term) -> list[dict]:
        like = f"%{term}%"
        rows = self.db.fetch_all(
            """SELECT patient_id, full_name, date_of_birth, gender,
                      phone, email, address, wilaya, blood_type,
                      allergies, medical_history, notes, created_at
               FROM patients
               WHERE full_name LIKE ? OR phone LIKE ? OR email LIKE ?""",
            (like, like, like)
        )
        return [self._row(r) for r in (rows or [])]

    def update_patient(self, patient_id, full_name, date_of_birth,
                       gender, phone, email, address, wilaya,
                       blood_type, allergies, medical_history, notes):
        return bool(self.db.execute_query(
            """UPDATE patients SET full_name=?, date_of_birth=?,
               gender=?, phone=?, email=?, address=?, wilaya=?,
               blood_type=?, allergies=?, medical_history=?, notes=?
               WHERE patient_id=?""",
            (full_name, date_of_birth, gender, phone, email,
             address, wilaya, blood_type, allergies,
             medical_history, notes, patient_id)
        ))

    def delete_patient(self, patient_id) -> bool:
        return bool(self.db.execute_query(
            "DELETE FROM patients WHERE patient_id=?", (patient_id,)))

    def patient_exists_by_phone(self, phone: str) -> bool:
        row = self.db.fetch_one(
            "SELECT 1 FROM patients WHERE phone=?", (phone,))
        return row is not None

    def get_age(self, patient_id: int) -> int | None:
        """Calculate age from date_of_birth stored as YYYY-MM-DD."""
        from datetime import date
        row = self.db.fetch_one(
            "SELECT date_of_birth FROM patients WHERE patient_id=?",
            (patient_id,))
        if not row or not row[0]:
            return None
        try:
            dob   = date.fromisoformat(row[0])
            today = date.today()
            return today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day))
        except Exception:
            return None

    @staticmethod
    def _row(r) -> dict:
        return {
            "patient_id":     r[0],  "full_name":      r[1]  or "",
            "date_of_birth":  r[2]  or "",
            "gender":         r[3]  or "Other",
            "phone":          r[4]  or "",  "email":   r[5]  or "",
            "address":        r[6]  or "",  "wilaya":  r[7]  or "",
            "blood_type":     r[8]  or "",
            "allergies":      r[9]  or "",
            "medical_history":r[10] or "",
            "notes":          r[11] or "",
            "created_at":     r[12] or "",
        }