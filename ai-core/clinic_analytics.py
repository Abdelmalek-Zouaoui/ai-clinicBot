"""
ai-core/clinic_analytics.py
----------------------------
Pure-Python analytics engine for the clinic database.

Runs targeted SQL queries and returns structured metrics that can be
forwarded to the LLM for natural-language insight generation.

NO dependency on Groq / LLM — this module is deterministic.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
import calendar
from typing import Any


class ClinicAnalytics:
    """Collect and compute clinic KPIs from the SQLite database."""

    def __init__(self, db_manager: Any):
        self.db = db_manager

    # ══════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════

    def collect_all_metrics(self) -> dict:
        """Run every analysis and return a single metrics snapshot."""
        return {
            "attendance":   self._analyze_attendance(),
            "services":     self._analyze_services(),
            "followup":     self._find_lost_followup(),
            "revenue":      self._analyze_revenue(),
            "scheduling":   self._analyze_scheduling(),
            "new_patients": self._analyze_new_patients(),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

    # ══════════════════════════════════════════════════════════════════
    # ATTENDANCE — month-over-month visit count + no-show rate
    # ══════════════════════════════════════════════════════════════════

    def _analyze_attendance(self) -> dict:
        today = date.today()
        this_start, this_end = self._month_range(today.year, today.month)

        prev = self._prev_month(today.year, today.month)
        prev_start, prev_end = self._month_range(*prev)

        this_total = self._count_appointments(this_start, this_end)
        prev_total = self._count_appointments(prev_start, prev_end)

        # No-show count this month
        no_show = self._scalar(
            "SELECT COUNT(*) FROM appointments "
            "WHERE DATE(appointment_date) BETWEEN ? AND ? "
            "AND status = 'No Show'",
            (this_start, this_end),
        )

        change_pct = self._pct_change(prev_total, this_total)
        no_show_rate = round(no_show / this_total, 2) if this_total else 0.0

        return {
            "this_month": this_total,
            "last_month": prev_total,
            "change_pct": change_pct,
            "no_show_count": no_show,
            "no_show_rate": no_show_rate,
        }

    # ══════════════════════════════════════════════════════════════════
    # SERVICES — most/least requested visit types
    # ══════════════════════════════════════════════════════════════════

    def _analyze_services(self) -> dict:
        today = date.today()
        start, end = self._month_range(today.year, today.month)

        rows = self.db.fetch_all(
            "SELECT visit_type, COUNT(*) AS cnt "
            "FROM appointments "
            "WHERE DATE(appointment_date) BETWEEN ? AND ? "
            "AND status NOT IN ('Cancelled') "
            "GROUP BY visit_type "
            "ORDER BY cnt DESC",
            (start, end),
        ) or []

        total = sum(r[1] for r in rows) or 1
        services = [
            {
                "name": r[0] or "Non spécifié",
                "count": r[1],
                "pct": round(r[1] / total * 100, 1),
            }
            for r in rows
        ]

        # Also check appointment_services for billed-service popularity
        billed = self.db.fetch_all(
            "SELECT s.name, COUNT(*) AS cnt, SUM(aps.quantity * aps.unit_price) AS rev "
            "FROM appointment_services aps "
            "JOIN services s ON aps.service_id = s.service_id "
            "JOIN appointments a ON aps.appointment_id = a.appointment_id "
            "WHERE DATE(a.appointment_date) BETWEEN ? AND ? "
            "GROUP BY s.name "
            "ORDER BY cnt DESC",
            (start, end),
        ) or []

        billed_services = [
            {"name": r[0], "count": r[1], "revenue": float(r[2] or 0)}
            for r in billed
        ]

        return {
            "by_visit_type": services,
            "by_billed_service": billed_services,
        }

    # ══════════════════════════════════════════════════════════════════
    # LOST FOLLOW-UP — patients whose last visit was > 2 months ago
    # ══════════════════════════════════════════════════════════════════

    def _find_lost_followup(self) -> dict:
        cutoff = (date.today() - timedelta(days=60)).isoformat()

        rows = self.db.fetch_all(
            "SELECT p.patient_id, p.full_name, MAX(a.appointment_date) AS last_visit "
            "FROM patients p "
            "JOIN appointments a ON p.patient_id = a.patient_id "
            "WHERE a.status = 'Completed' "
            "GROUP BY p.patient_id "
            "HAVING MAX(DATE(a.appointment_date)) < ? "
            "ORDER BY last_visit ASC "
            "LIMIT 20",
            (cutoff,),
        ) or []

        patients = [
            {
                "patient_id": r[0],
                "name": r[1] or "",
                "last_visit": r[2] or "",
            }
            for r in rows
        ]

        return {
            "count": len(patients),
            "cutoff_days": 60,
            "patients": patients,
        }

    # ══════════════════════════════════════════════════════════════════
    # REVENUE — month-over-month, per-day trend
    # ══════════════════════════════════════════════════════════════════

    def _analyze_revenue(self) -> dict:
        today = date.today()
        this_start, this_end = self._month_range(today.year, today.month)
        prev = self._prev_month(today.year, today.month)
        prev_start, prev_end = self._month_range(*prev)

        this_rev = self._scalar(
            "SELECT COALESCE(SUM(total_amount), 0) FROM appointments "
            "WHERE status = 'Completed' "
            "AND DATE(appointment_date) BETWEEN ? AND ?",
            (this_start, this_end),
        )

        prev_rev = self._scalar(
            "SELECT COALESCE(SUM(total_amount), 0) FROM appointments "
            "WHERE status = 'Completed' "
            "AND DATE(appointment_date) BETWEEN ? AND ?",
            (prev_start, prev_end),
        )

        avg_ticket = 0.0
        completed = self._scalar(
            "SELECT COUNT(*) FROM appointments "
            "WHERE status = 'Completed' "
            "AND DATE(appointment_date) BETWEEN ? AND ?",
            (this_start, this_end),
        )
        if completed:
            avg_ticket = round(this_rev / completed, 2)

        return {
            "this_month": round(float(this_rev), 2),
            "last_month": round(float(prev_rev), 2),
            "change_pct": self._pct_change(prev_rev, this_rev),
            "avg_ticket": avg_ticket,
            "completed_count": completed,
        }

    # ══════════════════════════════════════════════════════════════════
    # SCHEDULING — peak hours, busiest day of week
    # ══════════════════════════════════════════════════════════════════

    def _analyze_scheduling(self) -> dict:
        today = date.today()
        start, end = self._month_range(today.year, today.month)

        # Peak hours
        hour_rows = self.db.fetch_all(
            "SELECT CAST(strftime('%H', appointment_date) AS INTEGER) AS hr, "
            "COUNT(*) AS cnt "
            "FROM appointments "
            "WHERE DATE(appointment_date) BETWEEN ? AND ? "
            "AND status NOT IN ('Cancelled') "
            "GROUP BY hr "
            "ORDER BY cnt DESC",
            (start, end),
        ) or []

        peak_hours = [
            {"hour": f"{r[0]:02d}:00", "count": r[1]}
            for r in hour_rows[:5]
        ]

        # Busiest day of week (0=Sunday … 6=Saturday in SQLite %w)
        day_rows = self.db.fetch_all(
            "SELECT CAST(strftime('%w', appointment_date) AS INTEGER) AS dow, "
            "COUNT(*) AS cnt "
            "FROM appointments "
            "WHERE DATE(appointment_date) BETWEEN ? AND ? "
            "AND status NOT IN ('Cancelled') "
            "GROUP BY dow "
            "ORDER BY cnt DESC",
            (start, end),
        ) or []

        day_names = {
            0: "Dimanche", 1: "Lundi", 2: "Mardi", 3: "Mercredi",
            4: "Jeudi", 5: "Vendredi", 6: "Samedi",
        }
        busiest_days = [
            {"day": day_names.get(r[0], "?"), "count": r[1]}
            for r in day_rows[:3]
        ]

        return {
            "peak_hours": peak_hours,
            "busiest_days": busiest_days,
        }

    # ══════════════════════════════════════════════════════════════════
    # NEW PATIENTS — month-over-month registration
    # ══════════════════════════════════════════════════════════════════

    def _analyze_new_patients(self) -> dict:
        today = date.today()
        this_start, this_end = self._month_range(today.year, today.month)
        prev = self._prev_month(today.year, today.month)
        prev_start, prev_end = self._month_range(*prev)

        this_new = self._scalar(
            "SELECT COUNT(*) FROM patients "
            "WHERE DATE(created_at) BETWEEN ? AND ?",
            (this_start, this_end),
        )

        prev_new = self._scalar(
            "SELECT COUNT(*) FROM patients "
            "WHERE DATE(created_at) BETWEEN ? AND ?",
            (prev_start, prev_end),
        )

        total = self._scalar("SELECT COUNT(*) FROM patients", ())

        return {
            "this_month": this_new,
            "last_month": prev_new,
            "change_pct": self._pct_change(prev_new, this_new),
            "total": total,
        }

    # ══════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════

    def _count_appointments(self, start: str, end: str) -> int:
        return self._scalar(
            "SELECT COUNT(*) FROM appointments "
            "WHERE DATE(appointment_date) BETWEEN ? AND ? "
            "AND status NOT IN ('Cancelled')",
            (start, end),
        )

    def _scalar(self, query: str, params: tuple) -> int | float:
        """Return a single scalar value from a query, defaulting to 0."""
        row = self.db.fetch_one(query, params)
        return row[0] if row and row[0] is not None else 0

    @staticmethod
    def _month_range(year: int, month: int) -> tuple[str, str]:
        """Return (first_day, last_day) as ISO strings for the given month."""
        last_day = calendar.monthrange(year, month)[1]
        return (
            f"{year}-{month:02d}-01",
            f"{year}-{month:02d}-{last_day:02d}",
        )

    @staticmethod
    def _prev_month(year: int, month: int) -> tuple[int, int]:
        """Return (year, month) for the previous month."""
        if month == 1:
            return year - 1, 12
        return year, month - 1

    @staticmethod
    def _pct_change(old: int | float, new: int | float) -> float:
        """Percentage change from old to new, rounded to 1 decimal."""
        if old == 0:
            return 100.0 if new > 0 else 0.0
        return round((new - old) / old * 100, 1)
