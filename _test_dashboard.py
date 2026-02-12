"""Test rapide des endpoints du dashboard"""
import requests

print("=== TEST DASHBOARD ENDPOINTS ===")

# 1. Login page (GET)
r = requests.get("http://127.0.0.1:5004/login", timeout=5)
print(f"GET /login => {r.status_code} (len={len(r.text)})")
assert r.status_code == 200, "Login page should return 200"

# 2. Index (protégé - devrait rediriger vers login)
r = requests.get("http://127.0.0.1:5004/", timeout=5, allow_redirects=False)
print(f"GET / (no auth) => {r.status_code} redirect={r.headers.get('Location', 'none')}")
assert r.status_code == 302, "Protected route should redirect"

# 3. Login avec mauvaise clé
r = requests.post("http://127.0.0.1:5004/login", data={"access_key": "bad_key"}, timeout=5)
print(f"POST /login (bad key) => {r.status_code}")
assert "invalide" in r.text.lower() or "incorrect" in r.text.lower() or r.status_code == 200

# 4. Login avec bonne clé
good_key = "SSYstvhD9xiH5pzmzv_ErMa7BxAVZQZYbUSOIIlByrrNP1fOL6ME6i5mSmSOYT0C"
s = requests.Session()
r = s.post("http://127.0.0.1:5004/login", data={"access_key": good_key}, timeout=5, allow_redirects=False)
print(f"POST /login (good key) => {r.status_code} redirect={r.headers.get('Location', 'none')}")
assert r.status_code == 302, "Good key should redirect to dashboard"

# 5. Accès dashboard avec session authentifiée
r = s.get("http://127.0.0.1:5004/", timeout=5)
print(f"GET / (authenticated) => {r.status_code} (len={len(r.text)})")
assert r.status_code == 200, "Authenticated request should work"

# 6. API protégée avec session
r = s.get("http://127.0.0.1:5004/api/symbols", timeout=5)
print(f"GET /api/symbols (authenticated) => {r.status_code}")

# 7. Logout
r = s.get("http://127.0.0.1:5004/logout", timeout=5, allow_redirects=False)
print(f"GET /logout => {r.status_code} redirect={r.headers.get('Location', 'none')}")

# 8. Vérifier que après logout on ne peut plus accéder
r = s.get("http://127.0.0.1:5004/", timeout=5, allow_redirects=False)
print(f"GET / (after logout) => {r.status_code}")
assert r.status_code == 302, "After logout should redirect to login"

print("\n=== TOUS LES TESTS DASHBOARD OK ===")
