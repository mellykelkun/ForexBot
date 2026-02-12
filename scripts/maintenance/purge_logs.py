"""Purge manuelle de tous les logs (truncate) — avec backup préalable."""

import os
import shutil
from datetime import datetime


LOG_DIR = "logs"
ROOT_LOGS = ["process_manager.log", "bot_micro_scalper_v8_pro.log"]
ALLOWED_SUFFIXES = (".log", ".json", ".jsonl")


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

    return {
        "timestamp": datetime.now().isoformat(),
        "purged": purged,
        "failed": failed,
    }


if __name__ == "__main__":
    result = purge_all_logs()
    print("Purge terminée")
    print("Purgés:")
    for p in result["purged"]:
        print(" -", p)
    if result["failed"]:
        print("Échecs:")
        for p in result["failed"]:
            print(" -", p)
