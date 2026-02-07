# ForexBot — Système de trading IA (Groq + MT5)

## ⚠️ Avertissement
Ce système peut **exécuter des ordres réels** sur MT5. Utilisation à vos risques. Testez d’abord sur un compte démo.

---

## Vue d’ensemble
ForexBot est un **système complet** de trading algorithmique MT5 piloté par une **IA distante Groq**. Il comprend :
- Un **bot de trading** (scalping) en mode réel.
- Un **moteur IA** (service HTTP) qui prend les décisions d’entrée/sortie.
- Un **lanceur intelligent** qui gère les processus et la stabilité.
- Un **dashboard web** pour surveiller, contrôler et purger les logs.
- Des **garde‑fous** de risque, watchdog IA, journalisation, backups.

---

## Architecture (flux principal)
1. **lanceur_automatique.py** démarre :
   - `backend.ai.adaptive_engine` (IA Groq)
   - `backend.dashboard_app` (dashboard)
   - `main.py` (bot MT5)
2. Le bot envoie un **payload marché** à l’IA via `/api/decision`.
3. L’IA répond `BUY/SELL/HOLD` en JSON.
4. Le bot applique **les règles de risque** puis exécute l’ordre via MT5.
5. Toutes les actions sont **journalisées** et visibles sur le dashboard.

Schéma simplifié :
```
MT5 (marché) -> Bot (payload) -> IA Groq -> décision -> Bot (risk check) -> MT5 (order)
                         \----------------- Dashboard & logs ----------------/
```

---

## Stack & schéma technique
```
Windows + Python 3.10
│
├─ MetaTrader5 (API Python) ──> exécution ordres réels
├─ Requests / HTTP ───────────> IA Groq + contrôle
├─ Flask + Waitress ──────────> Dashboard + API IA
├─ Logging (rotations) ───────> logs + journaux
└─ .env / dotenv ─────────────> configuration runtime
```

---

## Fonctionnalités clés
- ✅ **Trading réel MT5** (pas de simulation)
- ✅ **IA Groq uniquement** (aucune IA locale)
- ✅ **Gestion du risque** (cooldown, limite d’ordres, hard‑stop)
- ✅ **Surveillance IA** (watchdog, heartbeat)
- ✅ **Backups automatiques**
- ✅ **Purge automatique des logs** (paramétrable)
- ✅ **Dashboard** avec contrôle et maintenance

### Ce qui est déjà sécurisé
- Validation MT5 (login/serveur requis)
- Détection IA indisponible + retry/backoff
- Limite d’ordres + filtre spread + seuil de confiance
- Journal hashé pour traçabilité

---

## Démarrage rapide
```bash
# 1) activer l’environnement virtuel
env\Scripts\activate

# 2) installer les dépendances
pip install -r requirements.txt

# 3) lancer le système complet
python lanceur_automatique.py
```

### Démarrage des composants séparément (debug)
```bash
python -m backend.ai.adaptive_engine
python -m backend.dashboard_app
python main.py --mode REAL --strategy MICRO --ai-engine --risk 0.5
```

---

## Configuration (.env)
Fichier requis : **.env** (exemple dans `.env.example`).

Variables principales :
- **MT5_LOGIN, MT5_PASSWORD, MT5_SERVER** : accès MT5
- **GROQ_API_KEY, GROQ_MODEL** : IA Groq
- **DASHBOARD_SECRET, FLASK_DEBUG** : dashboard
- **LOG_PURGE_INTERVAL_MINUTES, LOG_PURGE_MAX_MB** : purge auto logs

Variables de réglages trading (sécu & comportement) :
- **MAX_TRADES_PER_HOUR, MAX_TRADES_PER_DAY**
- **MIN_SECONDS_BETWEEN_TRADES**
- **MAX_DAILY_LOSS_PCT**
- **MAX_SLIPPAGE_POINTS, MAX_LATENCY_MS**
- **COMMISSION_PER_LOT, SIMULATED_SLIPPAGE_POINTS**
- **DECISION_INTERVAL_SECONDS, REQUIRED_CONFIDENCE**
- **MAX_SPREAD_POINTS**

Variables utiles supplémentaires :
- **AI_ENGINE_URL** : URL IA si serveur distant
- **AI_ENGINE_HEALTH_URL** : healthcheck IA
- **DASHBOARD_PORT** : port UI
- **CONTROL_URL** : URL du contrôleur

---

## Modules principaux (rôle de chaque fichier)

### Racine
- **main.py** : point d’entrée du bot, initialise MT5 et lance la stratégie.
- **lanceur_automatique.py** : lanceur intelligent + contrôle (start/stop/restart), monitoring et cleanup mémoire.
- **requirements.txt** : dépendances Python.
- **.env / .env.example** : configuration secrets/paramètres.

### Backend IA
- **backend/ai/adaptive_engine.py** : API IA (Groq). Endpoint `/api/decision`.
- **backend/ai/groq_service.py** : wrapper API Groq (JSON strict, retry/backoff).
- **backend/ai/__init__.py** : paquet IA.

### Bot trading
- **backend/bots/bot_btcusd_ultra_scalper_v8_clean.py** : bot principal (scalping multi‑symboles, risk manager, journal, watchdog, purge logs).

### Config
- **backend/config/config_micro_scalping_pro.py** : configuration trading (symboles, risques, timeframes, spreads, etc.).

### Dashboard
- **backend/dashboard_app.py** : API dashboard + endpoints (status, journal, logs, maintenance, marchés).
- **templates/dashboard.html** : interface web.

### Logs & données
- **logs/** : journaux runtime (trade_journal.jsonl, structured_logs.json, etc.).
- **backups/** : sauvegardes journalières des logs.

### Scripts maintenance
- **scripts/maintenance/purge_logs.py** : purge manuelle complète des logs.
- **scripts/maintenance/cleanup_memory.py / scripts/maintenance/cleanup_databases.py** : outils de maintenance.

---

## Garde‑fous & sécurité
- **Limites de fréquence** : trades/heure, trades/jour, cooldown
- **Hard‑stop journalier** : stop si perte max atteinte
- **Watchdog IA** : pause si erreurs consécutives
- **Filtre spread** : blocage au‑dessus d’un seuil

### Gestion d’erreurs
- IA offline → logs + retry
- MT5 non initialisé → arrêt propre
- Ordres rejetés → journal + logs

---

## Indicateurs envoyés à l’IA
Le bot envoie un payload riche à l’IA :
- **Prix/Spread/Volume** temps réel
- **Multi‑timeframes** : M1 / M5 / H1 / H4
- **Indicateurs** : RSI, EMA, SMA, ATR, MACD, Bollinger, Stoch, ROC, CCI, OBV, MFI, ADX
- **Chandeliers** : corps, mèches, direction, patterns (doji, pin bar, engulfing, hammer, shooting star, inside bar)
- **Contraintes & état des trades** : cooldown, limites, dernier trade, etc.

### Exemple de payload IA (simplifié)
```json
{
   "symbol": "BTCUSD",
   "bid": 66500.12,
   "ask": 66510.55,
   "spread_points": 12.3,
   "indicators": {"m1": {"rsi_14": 54.2, "ema_9": 66480.0}, "h1": {...}},
   "constraints": {"min_seconds_between_trades": 15, "max_trades_per_hour": 6},
   "trade_state": {"trades_last_hour": 3}
}
```

---

## Endpoints principaux
### IA (port 5003)
- `GET /health` : état IA
- `POST /api/decision` : décision IA (JSON)

### Dashboard (port 5004)
- `GET /health` : état dashboard
- `GET /api/status` : status global (depuis le lanceur)
- `GET /api/journal` : journal trading
- `GET /api/ai` : décisions IA récentes
- `GET /api/logs` : logs lanceur
- `POST /api/purge-logs` : purge manuelle
- `GET /api/maintenance` : dernière purge + tailles logs
- `GET /api/markets` : état par marché

### Control (port 5010)
- `POST /start`, `/stop`, `/restart`
- `GET /status`

---

## Dashboard — UX
- Interface moderne
- Scroll auto pour logs/IA/journal
- Bouton purge totale des logs
- Table marchés (action, confiance, dernière action)

---

## Journalisation (trade_journal.jsonl)
Chaque ligne est un événement JSON signé (hash). Types principaux :
- `decision`
- `order_filled`
- `order_rejected`
- `blocked`
- `slippage_alert`
- `hard_stop`

---

## Purge & backups
La purge automatique dépend de `.env` :
- `LOG_PURGE_INTERVAL_MINUTES`
- `LOG_PURGE_MAX_MB`

La purge manuelle se fait via :
- Script : `scripts/maintenance/purge_logs.py`
- Dashboard : bouton « Purger logs »

---

## Ajustements fréquents (pour devs)
1. **Fréquence IA trop élevée**
   - Modifier `min_seconds_between_trades`, `max_trades_per_hour` dans le bot.
2. **Spread/Slippage**
   - Ajuster seuils et logique de filtrage.
3. **Plus d’indicateurs**
   - Ajouter dans `_compute_indicators`.
4. **UI Dashboard**
   - Modifier `templates/dashboard.html`.

---

## Dépannage rapide
**IA indisponible** → vérifier `GROQ_API_KEY` et réseau.
**Ordres rejetés** → volume minimum MT5 / marché fermé / symbole non visible.
**Dashboard vide** → vérifier services 5003 / 5004 / 5010.
**RAM haute** → vérifier logs + fréquence IA.

---

## Conseils production
- Surveiller **slippage** et spreads en réel.
- Garder un œil sur CPU/RAM/disque.
- Ajuster `LOG_PURGE_INTERVAL_MINUTES` si besoin.

---

## Roadmap (idées)
- Export CSV du journal
- Alertes Telegram / Discord
- Tests unitaires des indicateurs

---

## Support
Si tu veux plus d’indicateurs, de patterns ou des dashboards avancés, indique précisément ce que tu veux ajouter.

---

## Bibliothèques utilisées (stack complet)
### Core
- Python 3.10
- MetaTrader5
- requests
- python-dotenv

### Web / API
- Flask
- Flask-Cors
- Flask-SocketIO (installé, non critique)
- Waitress

### Data / Science
- numpy
- pandas
- h5py

### Utilitaires
- psutil
- colorama

### Autres dépendances installées
- certifi, charset-normalizer, idna, urllib3
- click, itsdangerous, blinker, Jinja2, Werkzeug
- typing-extensions

> Note : certaines libs sont présentes via l’environnement mais pas forcément utilisées dans le bot clean.
