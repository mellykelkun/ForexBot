import re
import sys
from pathlib import Path

root = Path(r"C:/Users/melly/ForexBot")
py_files = [p for p in root.rglob("*.py") if "venv" not in p.parts and "env" not in p.parts]
imports = set()
pattern = re.compile(r"^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)")
for path in py_files:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = pattern.match(line)
            if m:
                imports.add(m.group(1).split(".")[0])
    except Exception:
        pass

stdlib = set(getattr(sys, "stdlib_module_names", []))
local = {"backend", "frontend"}
third_party = sorted(m for m in imports if m not in stdlib and m not in local)

req_path = root / "requirements.txt"
reqs = set()
if req_path.exists():
    for line in req_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[=<>]", line)[0].strip()
        if name:
            reqs.add(name)

import_to_pkg = {
    "dotenv": "python-dotenv",
    "flask_socketio": "flask-socketio",
    "flask_cors": "flask-cors",
    "sklearn": "scikit-learn",
    "talib": "ta-lib",
    "jwt": "pyjwt",
}

missing = [mod for mod in third_party if import_to_pkg.get(mod, mod) not in reqs]

print("Third-party imports:", ", ".join(third_party))
print("Missing in requirements.txt:", ", ".join(missing) or "(none)")
