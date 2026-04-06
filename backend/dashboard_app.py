"""Dashboard trading pro (UI + API) — Sécurisé par clé d'accès."""

import json
import os
import secrets
import shutil
from datetime import datetime
from typing import Any, Dict, List

import requests
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from waitress import serve

from backend.config.config_micro_scalping_pro import SYMBOLS_CONFIG
from backend.security.auth import verify_key, require_dashboard_auth, get_access_key_hash

CONTROL_URL = os.getenv("CONTROL_URL", "http://127.0.0.1:5010")
AI_ENGINE_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:5003")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5004"))

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("DASHBOARD_SECRET") or secrets.token_hex(32)
LOG_DIR = "logs"
ROOT_LOGS = ["process_manager.log", "bot_micro_scalper_v8_pro.log"]
ALLOWED_SUFFIXES = (".log", ".json", ".jsonl")
_last_purge_ts: str | None = None


def _tail_lines(path: str, limit: int = 200) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return [line.rstrip("\n") for line in lines[-limit:]]


def _tail_jsonl(path: str, limit: int = 50) -> List[Dict[str, Any]]:
    lines = _tail_lines(path, limit)
    out: List[Dict[str, Any]] = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _truncate(path: str) -> bool:
    try:
        with open(path, "w", encoding="utf-8"):
            pass
        return True
    except Exception:
        return False


def _purge_all_logs() -> Dict[str, Any]:
    purged: list[str] = []
    failed: list[str] = []

    # Backup rapide avant purge
    try:
        backup_dir = os.path.join("backups", datetime.now().strftime("%Y%m%d"))
        os.makedirs(backup_dir, exist_ok=True)
        if os.path.isdir(LOG_DIR):
            for name in os.listdir(LOG_DIR):
                src = os.path.join(LOG_DIR, name)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(backup_dir, name))
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

    # Purge aussi les rapports temporaires > 10 MB
    if os.path.isdir("reports"):
        for name in os.listdir("reports"):
            path = os.path.join("reports", name)
            if os.path.isfile(path) and os.path.getsize(path) > 10 * 1024 * 1024:
                if _truncate(path):
                    purged.append(path)

    # Nettoyage des vieux backups
    old_backups_removed = []
    try:
        from scripts.maintenance.purge_logs import cleanup_old_backups
        old_backups_removed = cleanup_old_backups()
    except Exception:
        pass

    return {
        "timestamp": datetime.now().isoformat(),
        "purged": purged,
        "failed": failed,
        "old_backups_removed": old_backups_removed,
    }


def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _log_sizes() -> list[Dict[str, Any]]:
    items: list[Dict[str, Any]] = []
    if os.path.isdir(LOG_DIR):
        for name in sorted(os.listdir(LOG_DIR)):
            if not name.lower().endswith(ALLOWED_SUFFIXES):
                continue
            path = os.path.join(LOG_DIR, name)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                items.append({"name": name, "size": size, "size_h": _human_size(size)})
    for name in ROOT_LOGS:
        if os.path.isfile(name):
            size = os.path.getsize(name)
            items.append({"name": name, "size": size, "size_h": _human_size(size)})
    return items


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        key = request.form.get("access_key", "")
        stored_hash = get_access_key_hash()
        if stored_hash and verify_key(key, stored_hash):
            session["authenticated"] = True
            session.permanent = True
            return redirect(url_for("index"))
        elif not stored_hash:
            # Première utilisation — pas de clé configurée
            session["authenticated"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Clé d'accès invalide")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "dashboard"})


@app.route("/api/status")
@require_dashboard_auth
def api_status():
    try:
        resp = requests.get(f"{CONTROL_URL}/status", timeout=3)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e), "metrics": {}, "processes": {}}), 200


@app.route("/api/journal")
@require_dashboard_auth
def api_journal():
    limit = int(request.args.get("limit", "50"))
    data = _tail_jsonl(os.path.join("logs", "trade_journal.jsonl"), limit)
    return jsonify({"items": data})


@app.route("/api/ai")
@require_dashboard_auth
def api_ai():
    limit = int(request.args.get("limit", "30"))
    data = _tail_jsonl(os.path.join("logs", "trade_journal.jsonl"), 200)
    decisions = [d for d in data if d.get("type") == "decision"]
    return jsonify({"items": decisions[-limit:]})


@app.route("/api/logs")
@require_dashboard_auth
def api_logs():
    allowed = {
        "process_manager.log": "process_manager.log",
        "bot.log": os.path.join("logs", "bot_micro_scalper_v8_pro.log"),
    }
    file_key = request.args.get("file", "process_manager.log")
    limit = int(request.args.get("lines", "200"))
    path = allowed.get(file_key)
    if not path:
        return jsonify({"error": "file not allowed"}), 400
    return jsonify({"lines": _tail_lines(path, limit)})


@app.route("/api/payload-volume")
@require_dashboard_auth
def api_payload_volume():
    limit = int(request.args.get("limit", "200"))
    candidates = [
        os.path.join("logs", "trading_system.log"),
        os.path.join("logs", "bot_micro_scalper_v8_pro.log"),
        os.path.join("logs", "structured_logs.json"),
        "bot_micro_scalper_v8_pro.log",
    ]
    payload_lines: list[str] = []
    for path in candidates:
        lines = _tail_lines(path, limit)
        payload_lines.extend([ln for ln in lines if "Payload IA" in ln])
    payload_lines = payload_lines[-limit:]
    return jsonify({"lines": payload_lines})


@app.route("/api/control/<action>", methods=["POST"])
@require_dashboard_auth
def api_control(action: str):
    if action not in {"start", "stop", "restart"}:
        return jsonify({"error": "invalid action"}), 400
    try:
        resp = requests.post(f"{CONTROL_URL}/{action}", timeout=5)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/purge-logs", methods=["POST"])
@require_dashboard_auth
def api_purge_logs():
    global _last_purge_ts
    result = _purge_all_logs()
    _last_purge_ts = result.get("timestamp")
    return jsonify(result)


@app.route("/api/maintenance")
@require_dashboard_auth
def api_maintenance():
    return jsonify({
        "last_purge": _last_purge_ts,
        "log_sizes": _log_sizes(),
    })


@app.route("/api/markets")
@require_dashboard_auth
def api_markets():
    data = _tail_jsonl(os.path.join("logs", "trade_journal.jsonl"), 500)
    by_symbol: dict[str, Dict[str, Any]] = {}
    for item in data:
        symbol = item.get("symbol")
        if not symbol:
            continue
        if symbol not in by_symbol:
            by_symbol[symbol] = {
                "last_action": None,
                "last_confidence": None,
                "last_event": None,
                "last_reason": None,
                "last_price": None,
                "last_ts": None,
            }
        if item.get("type") in {"decision", "order_filled", "order_rejected", "blocked", "slippage_alert"}:
            by_symbol[symbol]["last_event"] = item.get("type")
            by_symbol[symbol]["last_reason"] = item.get("reason")
            by_symbol[symbol]["last_ts"] = item.get("timestamp")
        if item.get("type") == "decision":
            decision: Dict[str, Any] = item.get("decision", {}) if isinstance(item.get("decision"), dict) else {}
            by_symbol[symbol]["last_action"] = decision.get("action")
            by_symbol[symbol]["last_confidence"] = decision.get("confidence")
            by_symbol[symbol]["last_price"] = decision.get("entry_price")
    return jsonify({"symbols": by_symbol})


@app.route("/api/symbols")
@require_dashboard_auth
def api_symbols():
    symbols: list[Dict[str, Any]] = []
    for name, cfg in SYMBOLS_CONFIG.items():
        symbols.append({
            "symbol": name,
            "enabled": bool(cfg.get("enabled")),
        })
    return jsonify({"symbols": symbols})


@app.route("/api/ai-provider")
@require_dashboard_auth
def api_ai_provider_get():
    """Récupère le statut des providers IA depuis l'AI Engine."""
    try:
        token = os.getenv("API_SECRET_TOKEN", "")
        resp = requests.get(
            f"{AI_ENGINE_URL}/api/providers",
            headers={"X-API-Token": token},
            timeout=3,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/ai-provider", methods=["POST"])
@require_dashboard_auth
def api_ai_provider_switch():
    """Change le provider IA actif via l'AI Engine."""
    try:
        data: Dict[str, Any] = request.get_json() or {}
        token = os.getenv("API_SECRET_TOKEN", "")
        resp = requests.post(
            f"{AI_ENGINE_URL}/api/switch-provider",
            json=data,
            headers={"X-API-Token": token, "Content-Type": "application/json"},
            timeout=5,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 503


# ── Kill Switch / Emergency Stop ──────────────────────────────

_risk_guardian_ref = None
_position_monitor_ref = None


def register_risk_guardian(guardian: Any, monitor: Any = None):
    """Appelé au démarrage du bot pour enregistrer les références."""
    global _risk_guardian_ref, _position_monitor_ref
    _risk_guardian_ref = guardian
    _position_monitor_ref = monitor


@app.route("/api/emergency-stop", methods=["POST"])
@require_dashboard_auth
def api_emergency_stop():
    """Kill switch d'urgence : ferme toutes les positions et bloque le trading."""
    _body: Dict[str, Any] = request.get_json() or {}
    reason = _body.get("reason", "Dashboard emergency stop")
    closed = 0

    # Fermer toutes les positions
    if _position_monitor_ref:
        closed = _position_monitor_ref.emergency_close_all(reason=reason)

    # Activer le kill switch
    if _risk_guardian_ref:
        _risk_guardian_ref.activate_kill_switch(reason)

    return jsonify({
        "success": True,
        "positions_closed": closed,
        "kill_switch": True,
        "reason": reason,
    })


@app.route("/api/kill-switch", methods=["POST"])
@require_dashboard_auth
def api_kill_switch_toggle():
    """Active ou désactive le kill switch (sans fermer les positions)."""
    data: Dict[str, Any] = request.get_json() or {}
    activate = data.get("activate", True)

    if not _risk_guardian_ref:
        return jsonify({"error": "RiskGuardian non enregistré"}), 503

    if activate:
        reason = data.get("reason", "Manuel (dashboard)")
        _risk_guardian_ref.activate_kill_switch(reason)
    else:
        _risk_guardian_ref.deactivate_kill_switch()

    return jsonify({
        "kill_switch": _risk_guardian_ref.is_kill_switch_active,
        "reason": _risk_guardian_ref.kill_switch_reason,
    })


@app.route("/")
@require_dashboard_auth
def index():
    return render_template("dashboard.html")


def main():
    serve(app, host="127.0.0.1", port=DASHBOARD_PORT)


if __name__ == "__main__":
    main()
