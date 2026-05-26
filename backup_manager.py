# backup_manager.py
"""
BackupManager — Automatic and manual SQLite database backup utility.

Features:
  • auto_backup()        : copy DB to ./backups/ with timestamp filename
  • manual_backup(dest) : copy DB to a user-chosen folder
  • get_backup_stats()  : total count, auto count, last backup date
  • get_backup_list()   : list of backup files with name + size
  • purge_old_backups() : delete auto-backups older than 30 days
"""

import os
import shutil
import logging
from datetime import datetime, timedelta


class BackupManager:

    BACKUP_SUBDIR = "backups"
    AUTO_PREFIX   = "auto_backup_"
    MAX_AGE_DAYS  = 30

    def __init__(self, db_path: str):
        self.db_path    = db_path
        self.backup_dir = os.path.join(
            os.path.dirname(os.path.abspath(db_path)),
            self.BACKUP_SUBDIR
        )
        os.makedirs(self.backup_dir, exist_ok=True)

    # ══════════════════════════════════════════════════════════════════════
    # BACKUP OPERATIONS
    # ══════════════════════════════════════════════════════════════════════

    def auto_backup(self) -> tuple[bool, str]:
        """
        Save a timestamped backup to the default backup folder.
        Returns (success: bool, message: str).
        """
        if not os.path.exists(self.db_path):
            return False, "Database file not found."

        stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.AUTO_PREFIX}{stamp}.db"
        dest     = os.path.join(self.backup_dir, filename)

        try:
            shutil.copy2(self.db_path, dest)
            logging.info(f"[Backup] Auto backup saved: {dest}")
            return True, dest
        except Exception as e:
            logging.error(f"[Backup] Auto backup failed: {e}")
            return False, str(e)

    def manual_backup(self, dest_folder: str) -> tuple[bool, str]:
        """
        Save a backup to a user-chosen folder.
        Returns (success: bool, message: str).
        """
        if not os.path.exists(self.db_path):
            return False, "Database file not found."
        if not os.path.isdir(dest_folder):
            return False, "Destination folder does not exist."

        stamp    = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"clinic_backup_{stamp}.db"
        dest     = os.path.join(dest_folder, filename)

        try:
            shutil.copy2(self.db_path, dest)
            logging.info(f"[Backup] Manual backup saved: {dest}")
            return True, dest
        except Exception as e:
            logging.error(f"[Backup] Manual backup failed: {e}")
            return False, str(e)

    # ══════════════════════════════════════════════════════════════════════
    # RESTORE
    # ══════════════════════════════════════════════════════════════════════
    
    def restore_latest_backup(self) -> tuple[bool, str]:
        """
        Restore the most recent backup over the current database.
        Returns (success: bool, message: str).
        """
        backups = self.get_backup_list()
        if not backups:
            return False, "No backups found."
        
        latest_file = backups[0]["filename"]
        src = os.path.join(self.backup_dir, latest_file)
        
        # Optionally make a copy of the corrupted file before overwrite
        corrupt_backup = self.db_path + ".corrupted"
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, corrupt_backup)
            shutil.copy2(src, self.db_path)
            logging.info(f"[Backup] Restored from {latest_file}")
            return True, f"Successfully restored {latest_file}"
        except Exception as e:
            logging.error(f"[Backup] Restore failed: {e}")
            return False, str(e)

    # ══════════════════════════════════════════════════════════════════════
    # STATS & LISTING
    # ══════════════════════════════════════════════════════════════════════

    def get_backup_list(self) -> list[dict]:
        """
        Return a list of backup files sorted newest-first.
        Each entry: {filename, size, modified}
        """
        if not os.path.isdir(self.backup_dir):
            return []

        files = []
        for fname in os.listdir(self.backup_dir):
            if not fname.endswith(".db"):
                continue
            fpath = os.path.join(self.backup_dir, fname)
            try:
                stat = os.stat(fpath)
                size_kb = stat.st_size / 1024
                modified = datetime.fromtimestamp(
                    stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                files.append({
                    "filename": fname,
                    "name":     fname,          # alias for UI
                    "size":     f"{size_kb:.1f} KB",
                    "modified": modified,
                })
            except Exception:
                continue

        files.sort(key=lambda x: x["modified"], reverse=True)
        return files

    def get_backup_stats(self) -> dict:
        """
        Return summary statistics about the backup folder.
        Keys: total, auto, manual, last_backup
        """
        all_files  = self.get_backup_list()
        total      = len(all_files)
        auto_count = sum(
            1 for f in all_files
            if f["filename"].startswith(self.AUTO_PREFIX)
        )
        last = all_files[0]["modified"] if all_files else "—"

        return {
            "total":       total,
            "auto":        auto_count,
            "manual":      total - auto_count,
            "last_backup": last,
        }

    # ══════════════════════════════════════════════════════════════════════
    # MAINTENANCE
    # ══════════════════════════════════════════════════════════════════════

    def purge_old_backups(self, max_age_days: int = None) -> int:
        """
        Delete auto-backup files older than max_age_days (default 30).
        Returns the number of files deleted.
        """
        max_age_days = max_age_days or self.MAX_AGE_DAYS
        cutoff       = datetime.now() - timedelta(days=max_age_days)
        removed      = 0

        if not os.path.isdir(self.backup_dir):
            return 0

        for fname in os.listdir(self.backup_dir):
            if not fname.startswith(self.AUTO_PREFIX):
                continue
            fpath = os.path.join(self.backup_dir, fname)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                if mtime < cutoff:
                    os.remove(fpath)
                    removed += 1
                    logging.info(f"[Backup] Purged old backup: {fname}")
            except Exception as e:
                logging.warning(f"[Backup] Could not purge {fname}: {e}")

        return removed