# service_model.py
class ServiceModel:
    def __init__(self, db_manager):
        self.db = db_manager

    def add_service(self, code, name, category, price,
                    duration_min=30, description=""):
        query = """INSERT INTO services
                   (code, name, category, price, duration_min, description)
                   VALUES (?, ?, ?, ?, ?, ?)"""
        return self.db.execute_query(
            query, (code, name, category, price, duration_min, description))

    def get_all_services(self):
        rows = self.db.fetch_all(
            "SELECT service_id, code, name, category, price, "
            "duration_min, description, is_active FROM services"
        )
        return [self._row(r) for r in (rows or [])]

    def search_service(self, term):
        like = f"%{term}%"
        rows = self.db.fetch_all(
            "SELECT service_id, code, name, category, price, "
            "duration_min, description, is_active FROM services "
            "WHERE name LIKE ? OR category LIKE ? OR code = ?",
            (like, like, term)
        )
        return [self._row(r) for r in (rows or [])]

    def update_service(self, service_id, name, category,
                       price, duration_min, description):
        return self.db.execute_query(
            """UPDATE services SET name=?, category=?, price=?,
               duration_min=?, description=? WHERE service_id=?""",
            (name, category, price, duration_min, description, service_id)
        )

    def delete_service(self, service_id):
        return self.db.execute_query(
            "DELETE FROM services WHERE service_id=?", (service_id,))

    def service_exists(self, code) -> bool:
        return self.db.fetch_one(
            "SELECT 1 FROM services WHERE code=?", (code,)) is not None

    def get_today_revenue(self) -> float:
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(total_amount),0) FROM appointments "
            "WHERE DATE(appointment_date)=DATE('now') "
            "AND status='Completed'"
        )
        return float(row[0]) if row else 0.0

    @staticmethod
    def _row(r) -> dict:
        return {
            "service_id":   r[0], "code":        r[1] or "",
            "name":         r[2], "category":    r[3] or "",
            "price":        float(r[4] or 0),
            "duration_min": int(r[5] or 30),
            "description":  r[6] or "",
            "is_active":    bool(r[7]),
        }