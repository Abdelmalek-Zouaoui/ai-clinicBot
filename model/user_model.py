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
    def _hash(password: str, salt: str = "") -> str:
        """PBKDF2-HMAC-SHA256 hash of the password with salt. Unsalted SHA-256 fallback."""
        if not salt:
            return hashlib.sha256(password.encode("utf-8")).hexdigest()
        combined_salt = f"clinic_app_salt_{salt.lower()}".encode("utf-8")
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            combined_salt,
            iterations=100000
        ).hex()

    # ══════════════════════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════════════════════

    def add_user(self, username: str, password: str,
                 role: str = "employee",
                 full_name: str = "",
                 phone: str = "",
                 notes: str = "") -> bool:
        """Create a new user account. Returns True on success."""
        username_clean = username.strip()
        return bool(self.db.execute_query(
            """INSERT INTO users
               (username, password, role, full_name, phone, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username_clean,
             self._hash(password, username_clean),
             role, full_name, phone, notes)
        ))

    def authenticate(self, username: str,
                     password: str) -> tuple | None:
        """
        Verify credentials.
        Returns (user_id, username, role) on success, None on failure.
        Allows seamless migration from old SHA-256 to PBKDF2-HMAC-SHA256.
        """
        username_clean = username.strip()
        row = self.db.fetch_one(
            """SELECT user_id, username, role, password
               FROM users
               WHERE username=?""",
            (username_clean,)
        )
        if not row:
            return None
        
        user_id, db_username, role, db_password = row
        new_hash = self._hash(password, username_clean)
        old_hash = self._hash(password)
        
        if db_password == new_hash:
            return (user_id, db_username, role)
        elif db_password == old_hash:
            # Upgrade legacy password hash to PBKDF2
            self.change_password(user_id, password)
            return (user_id, db_username, role)
            
        return None

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
        user = self.get_user(user_id)
        if not user:
            return False
        username = user.get("username", "")
        return bool(self.db.execute_query(
            "UPDATE users SET password=? WHERE user_id=?",
            (self._hash(new_password, username), user_id)
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