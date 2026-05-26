# model/db_manager.py
"""
DBManager — SQLite database manager for the Clinic Management System.

Responsibilities:
  • Open / create the database file
  • Create all tables on first run (safe to call every startup)
  • Provide execute_query, fetch_one, fetch_all helpers
  • Provide get_setting / set_setting for the key-value settings table
"""

import sqlite3
import os
import logging


class DBManager:

    def __init__(self, db_path: str = None):
        if db_path is None:
            base = os.path.dirname(os.path.abspath(__file__))
            db_dir = os.path.join(base, "..", "database")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "clinic.db")

        self.db_path = db_path
        self.conn    = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=10000")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.cursor  = self.conn.cursor()

        self._create_base_tables()
        self.create_clinic_tables()

    # ══════════════════════════════════════════════════════════════════════
    # TABLE CREATION
    # ══════════════════════════════════════════════════════════════════════

    def _create_base_tables(self):
        """Create the users and settings tables used by the base app."""

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER  PRIMARY KEY AUTOINCREMENT,
                username   TEXT     NOT NULL UNIQUE,
                password   TEXT     NOT NULL,
                role       TEXT     DEFAULT 'employee',
                full_name  TEXT     DEFAULT '',
                phone      TEXT     DEFAULT '',
                notes      TEXT     DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT DEFAULT ''
            )
        ''')

        self.conn.commit()

    def create_clinic_tables(self):
        """Creates all clinic-specific tables. Safe to call on every startup."""

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                service_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                code         TEXT    UNIQUE,
                name         TEXT    NOT NULL,
                category     TEXT    DEFAULT 'Consultation',
                duration_min INTEGER DEFAULT 30,
                price        REAL    NOT NULL DEFAULT 0,
                description  TEXT    DEFAULT '',
                is_active    INTEGER DEFAULT 1
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id      INTEGER  PRIMARY KEY AUTOINCREMENT,
                full_name       TEXT     NOT NULL,
                date_of_birth   TEXT     DEFAULT '',
                gender          TEXT     DEFAULT 'Other',
                phone           TEXT     DEFAULT '',
                email           TEXT     DEFAULT '',
                address         TEXT     DEFAULT '',
                wilaya          TEXT     DEFAULT '',
                blood_type      TEXT     DEFAULT '',
                allergies       TEXT     DEFAULT '',
                medical_history TEXT     DEFAULT '',
                notes           TEXT     DEFAULT '',
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                appointment_id   INTEGER  PRIMARY KEY AUTOINCREMENT,
                patient_id       INTEGER  NOT NULL,
                doctor_id        INTEGER,
                appointment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status           TEXT     DEFAULT 'Pending',
                visit_type       TEXT     DEFAULT 'Consultation',
                chief_complaint  TEXT     DEFAULT '',
                diagnosis        TEXT     DEFAULT '',
                notes            TEXT     DEFAULT '',
                total_amount     REAL     DEFAULT 0,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
                FOREIGN KEY (doctor_id)  REFERENCES users (user_id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointment_services (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER NOT NULL,
                service_id     INTEGER NOT NULL,
                quantity       INTEGER DEFAULT 1,
                unit_price     REAL    NOT NULL,
                notes          TEXT    DEFAULT '',
                FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
                FOREIGN KEY (service_id)     REFERENCES services(service_id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescriptions (
                rx_id          INTEGER  PRIMARY KEY AUTOINCREMENT,
                appointment_id INTEGER,
                patient_id     INTEGER  NOT NULL,
                doctor_id      INTEGER,
                issued_date    DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes          TEXT     DEFAULT '',
                FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
                FOREIGN KEY (patient_id)     REFERENCES patients(patient_id),
                FOREIGN KEY (doctor_id)      REFERENCES users(user_id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS prescription_items (
                item_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                rx_id         INTEGER NOT NULL,
                medicine_name TEXT    NOT NULL,
                dosage        TEXT    DEFAULT '',
                frequency     TEXT    DEFAULT '',
                duration      TEXT    DEFAULT '',
                instructions  TEXT    DEFAULT '',
                FOREIGN KEY (rx_id) REFERENCES prescriptions(rx_id)
            )
        ''')

        # Add indexes for often-queried columns
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_appt_patient_id ON appointments(patient_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_appt_date ON appointments(appointment_date)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_appt_status ON appointments(status)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_patient_phone ON patients(phone)')

        # Seed default clinic identity settings
        clinic_defaults = [
            ("app_name",     "CLINIC MANAGER"),
            ("app_subtitle", "Medical Clinic — Algeria"),
            ("app_address",  ""),
            ("app_phone",    ""),
        ]
        self.cursor.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            clinic_defaults
        )
        self.conn.commit()

    # ══════════════════════════════════════════════════════════════════════
    # QUERY HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def execute_query(self, query: str, params: tuple = ()) -> bool:
        """Execute an INSERT / UPDATE / DELETE. Returns True on success."""
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"[DB] execute_query error: {e}\nQuery: {query}")
            return False

    def fetch_one(self, query: str, params: tuple = ()):
        """Return the first row or None."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            logging.error(f"[DB] fetch_one error: {e}\nQuery: {query}")
            return None

    def fetch_all(self, query: str, params: tuple = ()):
        """Return all rows as a list, or an empty list on error."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"[DB] fetch_all error: {e}\nQuery: {query}")
            return []

    # ══════════════════════════════════════════════════════════════════════
    # SETTINGS  (key-value store)
    # ══════════════════════════════════════════════════════════════════════

    def get_setting(self, key: str, default: str = "") -> str:
        row = self.fetch_one(
            "SELECT value FROM settings WHERE key=?", (key,))
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> bool:
        return self.execute_query(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )

    # ══════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ══════════════════════════════════════════════════════════════════════

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

    def __del__(self):
        self.close()