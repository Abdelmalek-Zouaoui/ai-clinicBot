# model/user_model.py
"""
UserModel — Staff / user account management.

Table: users
  user_id, username, password, role, full_name, phone, notes, created_at
"""

import hashlib
import logging


class UserModel:

    def __init__(self, db_manager):
        self.db = db_manager

    # ══════════════════════════════════════════════════════════════════════
    # PASSWORD HASHING
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _hash(password: str) -> str:
        """SHA-256 hash of the password."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # ══════════════════════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════════════════════

    def add_user(self, username: str, password: str,
                 role: str = "employee",
                 full_name: str = "",
                 phone: str = "",
                 notes: str = "") -> bool:
        """Create a new user account. Returns True on success."""
        return bool(self.db.execute_query(
            """INSERT INTO users
               (username, password, role, full_name, phone, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username.strip(),
             self._hash(password),
             role, full_name, phone, notes)
        ))

    def authenticate(self, username: str,
                     password: str) -> tuple | None:
        """
        Verify credentials.
        Returns (user_id, username, role) on success, None on failure.
        """
        row = self.db.fetch_one(
            """SELECT user_id, username, role
               FROM users
               WHERE username=? AND password=?""",
            (username.strip(), self._hash(password))
        )
        return (row[0], row[1], row[2]) if row else None

    def get_all_users(self) -> list[dict]:
        rows = self.db.fetch_all(
            """SELECT user_id, username, role,
                      full_name, phone, notes, created_at
               FROM users ORDER BY username"""
        )
        return [self._row(r) for r in (rows or [])]

    def get_user(self, user_id: int) -> dict | None:
        row = self.db.fetch_one(
            """SELECT user_id, username, role,
                      full_name, phone, notes, created_at
               FROM users WHERE user_id=?""",
            (user_id,)
        )
        return self._row(row) if row else None

    def user_exists(self, username: str) -> bool:
        row = self.db.fetch_one(
            "SELECT 1 FROM users WHERE username=?",
            (username.strip(),)
        )
        return row is not None

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user account.
        Refuses to delete if it would leave zero admin accounts.
        """
        # Guard: must keep at least one admin
        row = self.db.fetch_one(
            "SELECT role FROM users WHERE user_id=?", (user_id,))
        if row and row[0] == "admin":
            count = self.db.fetch_one(
                "SELECT COUNT(*) FROM users WHERE role='admin'")
            if count and count[0] <= 1:
                logging.warning(
                    "Refused to delete last admin account.")
                return False

        return bool(self.db.execute_query(
            "DELETE FROM users WHERE user_id=?", (user_id,)))

    def change_password(self, user_id: int,
                        new_password: str) -> bool:
        return bool(self.db.execute_query(
            "UPDATE users SET password=? WHERE user_id=?",
            (self._hash(new_password), user_id)
        ))

    def update_user(self, user_id: int, full_name: str = "",
                    phone: str = "", role: str = "",
                    notes: str = "") -> bool:
        return bool(self.db.execute_query(
            """UPDATE users
               SET full_name=?, phone=?, role=?, notes=?
               WHERE user_id=?""",
            (full_name, phone, role, notes, user_id)
        ))

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _row(r) -> dict:
        return {
            "user_id":    r[0],
            "username":   r[1] or "",
            "role":       r[2] or "employee",
            "full_name":  r[3] or "",
            "phone":      r[4] or "",
            "notes":      r[5] or "",
            "created_at": r[6] or "",
        }