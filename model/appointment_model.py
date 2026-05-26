# appointment_model.py
from datetime import date

class AppointmentModel:
    def __init__(self, db_manager):
        self.db = db_manager

    STATUSES = ["Pending", "In Progress", "Completed", "Cancelled", "No Show"]

    # ── CRUD ────────────────────────────────────────────────────────

    def create_appointment(self, patient_id: int, doctor_id: int = None,
                           visit_type: str = "Consultation",
                           chief_complaint: str = "",
                           appointment_date: str = None) -> int | None:
        dt = appointment_date or date.today().isoformat()
        return self.db.execute_insert(
            """INSERT INTO appointments
               (patient_id, doctor_id, appointment_date,
                status, visit_type, chief_complaint)
               VALUES (?,?,?,?,?,?)""",
            (patient_id, doctor_id, dt,
             "Pending", visit_type, chief_complaint)
        )

    def update_status(self, appointment_id: int,
                      status: str, diagnosis: str = None,
                      notes: str = None) -> bool:
        query = "UPDATE appointments SET status=?"
        params = [status]
        if diagnosis is not None:
            query += ", diagnosis=?"
            params.append(diagnosis)
        if notes is not None:
            query += ", notes=?"
            params.append(notes)
        query += " WHERE appointment_id=?"
        params.append(appointment_id)
        return bool(self.db.execute_query(query, tuple(params)))

    def update_total(self, appointment_id: int, total: float) -> bool:
        return bool(self.db.execute_query(
            "UPDATE appointments SET total_amount=? "
            "WHERE appointment_id=?",
            (total, appointment_id)
        ))

    def get_appointment(self, appointment_id: int) -> dict | None:
        row = self.db.fetch_one(
            """SELECT a.appointment_id, a.patient_id, p.full_name,
                      a.doctor_id, a.appointment_date, a.status,
                      a.visit_type, a.chief_complaint,
                      a.diagnosis, a.notes, a.total_amount
               FROM appointments a
               JOIN patients p ON a.patient_id = p.patient_id
               WHERE a.appointment_id=?""", (appointment_id,)
        )
        return self._row(row) if row else None

    # ── Queue queries ─────────────────────────────────────────────

    def get_today_queue(self) -> list[dict]:
        """All non-cancelled appointments for today, ordered by time."""
        rows = self.db.fetch_all(
            """SELECT a.appointment_id, a.patient_id, p.full_name,
                      a.doctor_id, a.appointment_date, a.status,
                      a.visit_type, a.chief_complaint,
                      a.diagnosis, a.notes, a.total_amount
               FROM appointments a
               JOIN patients p ON a.patient_id = p.patient_id
               WHERE DATE(a.appointment_date) = DATE('now')
                 AND a.status NOT IN ('Cancelled','No Show')
               ORDER BY a.appointment_date""", ()
        )
        return [self._row(r) for r in (rows or [])]

    def get_waiting(self) -> list[dict]:
        """Patients currently waiting (status = Pending)."""
        rows = self.db.fetch_all(
            """SELECT a.appointment_id, a.patient_id, p.full_name,
                      a.doctor_id, a.appointment_date, a.status,
                      a.visit_type, a.chief_complaint,
                      a.diagnosis, a.notes, a.total_amount
               FROM appointments a
               JOIN patients p ON a.patient_id = p.patient_id
               WHERE DATE(a.appointment_date) = DATE('now')
                 AND a.status = 'Pending'
               ORDER BY a.appointment_date""", ()
        )
        return [self._row(r) for r in (rows or [])]

    # ── Billing ───────────────────────────────────────────────────

    def add_service_to_appointment(self, appointment_id: int,
                                   service_id: int,
                                   unit_price: float,
                                   quantity: int = 1) -> bool:
        return bool(self.db.execute_query(
            """INSERT INTO appointment_services
               (appointment_id, service_id, quantity, unit_price)
               VALUES (?,?,?,?)""",
            (appointment_id, service_id, quantity, unit_price)
        ))

    def get_appointment_services(self, appointment_id: int) -> list[dict]:
        rows = self.db.fetch_all(
            """SELECT aps.id, aps.service_id, s.name, aps.quantity,
                      aps.unit_price,
                      (aps.quantity * aps.unit_price) AS subtotal
               FROM appointment_services aps
               JOIN services s ON aps.service_id = s.service_id
               WHERE aps.appointment_id=?""", (appointment_id,)
        )
        return [
            {"id": r[0], "service_id": r[1], "name": r[2],
             "quantity": r[3], "unit_price": float(r[4]),
             "subtotal": float(r[5])}
            for r in (rows or [])
        ]

    # ── Stats ─────────────────────────────────────────────────────

    def get_today_stats(self) -> dict:
        row = self.db.fetch_one(
            """SELECT
                COUNT(*)                                         AS total,
                SUM(CASE WHEN status='Pending'     THEN 1 END)  AS waiting,
                SUM(CASE WHEN status='In Progress' THEN 1 END)  AS in_progress,
                SUM(CASE WHEN status='Completed'   THEN 1 END)  AS completed,
                COALESCE(SUM(CASE WHEN status='Completed'
                             THEN total_amount END), 0)          AS revenue
               FROM appointments
               WHERE DATE(appointment_date) = DATE('now')""", ()
        )
        if not row:
            return dict(total=0, waiting=0, in_progress=0,
                        completed=0, revenue=0.0)
        return {
            "total":       int(row[0] or 0),
            "waiting":     int(row[1] or 0),
            "in_progress": int(row[2] or 0),
            "completed":   int(row[3] or 0),
            "revenue":     float(row[4] or 0),
        }

    def get_monthly_revenue(self) -> dict:
        """Same signature as MedicineModel.get_today_sales_total —
           returns {day: revenue} for the current month."""
        import calendar
        today = date.today()
        last  = calendar.monthrange(today.year, today.month)[1]
        first_str = f"{today.year}-{today.month:02d}-01"
        last_str  = f"{today.year}-{today.month:02d}-{last:02d}"
        rows = self.db.fetch_all(
            """SELECT CAST(strftime('%d', appointment_date) AS INTEGER),
                      SUM(total_amount)
               FROM appointments
               WHERE DATE(appointment_date) BETWEEN ? AND ?
                 AND status = 'Completed'
               GROUP BY 1 ORDER BY 1""",
            (first_str, last_str)
        )
        return {int(r[0]): float(r[1]) for r in rows if r[1]}

    @staticmethod
    def _row(r) -> dict:
        return {
            "appointment_id":  r[0], "patient_id":     r[1],
            "patient_name":    r[2] or "",
            "doctor_id":       r[3],
            "appointment_date":r[4] or "",
            "status":          r[5] or "Pending",
            "visit_type":      r[6] or "",
            "chief_complaint": r[7] or "",
            "diagnosis":       r[8] or "",
            "notes":           r[9] or "",
            "total_amount":    float(r[10] or 0),
        }