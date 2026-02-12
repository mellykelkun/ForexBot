"""Purge manuelle de tous les logs (truncate) — avec backup préalable
et nettoyage automatique des vieux backups."""

import os
import shutil
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

LOG_DIR = "logs"
BACKUP_DIR = "backups"
ROOT_LOGS = ["process_manager.log", "bot_micro_scalper_v8_pro.log"]
ALLOWED_SUFFIXES = (".log", ".json", ".jsonl")
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))


def _truncate(path: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8"):
            pass
        return True
    except Exception:
        return False


def purge_all_logs() -> dict:
    purged = []
    failed = []

    # Backup avant purge
    try:
        backup_dir = os.path.join("backups", datetime.now().strftime("%Y%m%d"))
        os.makedirs(backup_dir, exist_ok=True)
        if os.path.isdir(LOG_DIR):
            for name in os.listdir(LOG_DIR):
                src = os.path.join(LOG_DIR, name)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(backup_dir, name))
        for name in ROOT_LOGS:
            if os.path.isfile(name):
                shutil.copy2(name, os.path.join(backup_dir, os.path.basename(name)))
    except Exception:
        pass

    if os.path.isdir(LOG_DIR):
        for name in os.listdir(LOG_DIR):
            if not name.lower().endswith(ALLOWED_SUFFIXES):
                continue
            path = os.path.join(LOG_DIR, name)
            if os.path.isfile(path):
                if _truncate(path):
                    purged.append(path)
                else:
                    failed.append(path)

    for name in ROOT_LOGS:
        if os.path.isfile(name):
            if _truncate(name):
                purged.append(name)
            else:
                failed.append(name)

    # Nettoyage des vieux backups
    old_backups = cleanup_old_backups()

    return {
        "timestamp": datetime.now().isoformat(),
        "purged": purged,
        "failed": failed,
        "old_backups_removed": old_backups,
    }


def cleanup_old_backups(retention_days: int = None) -> list:
    """Supprime les dossiers de backup plus vieux que retention_days."""
    if retention_days is None:
        retention_days = BACKUP_RETENTION_DAYS

    removed = []
    if not os.path.isdir(BACKUP_DIR):
        return removed

    cutoff = datetime.now() - timedelta(days=retention_days)
    cutoff_str = cutoff.strftime("%Y%m%d")

    for name in sorted(os.listdir(BACKUP_DIR)):
        folder_path = os.path.join(BACKUP_DIR, name)
        if not os.path.isdir(folder_path):
            continue
        # Les dossiers sont nommés YYYYMMDD
        if len(name) == 8 and name.isdigit() and name < cutoff_str:
            try:
                shutil.rmtree(folder_path)
                removed.append(name)
            except Exception:
                pass

    return removed


if __name__ == "__main__":
    result = purge_all_logs()
    print("Purge terminée")
    print(f"Rétention backups : {BACKUP_RETENTION_DAYS} jours")
    print("Purgés:")
    for p in result["purged"]:
        print(" -", p)
    if result["failed"]:
        print("Échecs:")
        for p in result["failed"]:
            print(" -", p)
    if result["old_backups_removed"]:
        print("Vieux backups supprimés:")
        for b in result["old_backups_removed"]:
            print(" -", b)
    else:
        print("Aucun vieux backup à supprimer.")
