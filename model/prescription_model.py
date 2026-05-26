# prescription_model.py
class PrescriptionModel:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_prescription(self, patient_id: int,
                            appointment_id: int = None,
                            doctor_id: int = None,
                            notes: str = "") -> int | None:
        return self.db.execute_insert(
            """INSERT INTO prescriptions
               (patient_id, appointment_id, doctor_id, notes)
               VALUES (?,?,?,?)""",
            (patient_id, appointment_id, doctor_id, notes)
        )

    def add_item(self, rx_id: int, medicine_name: str,
                 dosage: str = "", frequency: str = "",
                 duration: str = "", instructions: str = "") -> bool:
        return bool(self.db.execute_query(
            """INSERT INTO prescription_items
               (rx_id, medicine_name, dosage, frequency,
                duration, instructions)
               VALUES (?,?,?,?,?,?)""",
            (rx_id, medicine_name, dosage,
             frequency, duration, instructions)
        ))

    def get_prescription(self, rx_id: int) -> dict | None:
        row = self.db.fetch_one(
            """SELECT rx.rx_id, rx.patient_id, p.full_name,
                      rx.doctor_id, rx.issued_date, rx.notes
               FROM prescriptions rx
               JOIN patients p ON rx.patient_id = p.patient_id
               WHERE rx.rx_id=?""", (rx_id,)
        )
        if not row:
            return None
        items = self.get_items(rx_id)
        return {
            "rx_id": row[0], "patient_id": row[1],
            "patient_name": row[2], "doctor_id": row[3],
            "issued_date": row[4], "notes": row[5],
            "items": items
        }

    def get_items(self, rx_id: int) -> list[dict]:
        rows = self.db.fetch_all(
            """SELECT item_id, medicine_name, dosage,
                      frequency, duration, instructions
               FROM prescription_items WHERE rx_id=?""", (rx_id,)
        )
        return [
            {"item_id": r[0], "medicine_name": r[1],
             "dosage": r[2], "frequency": r[3],
             "duration": r[4], "instructions": r[5]}
            for r in (rows or [])
        ]

    def get_patient_prescriptions(self, patient_id: int) -> list[dict]:
        rows = self.db.fetch_all(
            """SELECT rx_id, issued_date, notes
               FROM prescriptions WHERE patient_id=?
               ORDER BY issued_date DESC""", (patient_id,)
        )
        return [{"rx_id": r[0], "issued_date": r[1],
                 "notes": r[2]} for r in (rows or [])]