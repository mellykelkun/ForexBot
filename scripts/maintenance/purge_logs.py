"""Purge manuelle de tous les logs (truncate)."""

import os
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
