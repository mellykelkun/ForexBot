# ForexBot SaaS — Système de Trading IA Multi-Provider (Groq / OpenAI / DeepSeek + MT5)

## ⚠️ Avertissement
Ce système exécute des **ordres réels** sur MetaTrader 5. Utilisation à vos risques et périls. Testez d'abord sur un compte démo.

---

## Vue d'ensemble
ForexBot est un **système complet de trading algorithmique** MT5 piloté par une **IA distante multi-provider** (Groq, OpenAI GPT, DeepSeek) avec switching en temps réel depuis le dashboard.

### Composants
- **Bot de trading** — scalping multi-symboles (8 paires) en mode réel
- **Moteur IA multi-provider** — décisions d'entrée/sortie via API HTTP
- **Lanceur intelligent** — gestion des processus, redémarrage automatique, cleanup mémoire
- **Dashboard web sécurisé** — surveillance, contrôle, sélection provider IA en temps réel
- **Système de sécurité** — authentification, risk guardian, journal hashé, kill switch

### Paires tradées
BTCUSD, GOLD, USDZAR, EURUSD, USDJPY, GBPUSD, AUDUSD, NZDUSD

---

## Architecture

```
MT5 (marché)
    │
    ▼
Bot (analyse multi-TF) ──payload──▶ AI Engine (port 5003)
    │                                    │
    │  ◀──décision JSON──────────────────┘
    │       (BUY/SELL/HOLD + SL/TP + confidence)
    │
    ▼
Risk Guardian ──▶ validation ──▶ MT5 (ordre)
    │
    ▼
Trade Journal (hashé) ──▶ Dashboard (port 5004)
```

### Flux détaillé
1. **lanceur_automatique.py** démarre dans l'ordre : AI Engine → Dashboard → Bot
2. Le bot collecte les données multi-timeframes (M1, M5, H1, H4, D1) + historique trades
3. **Smart Payload** compresse et envoie à l'IA via `POST /api/decision`
4. L'IA (provider actif) analyse et retourne `{action, confidence, sl_price, tp_price, reason}`
5. **RiskGuardian** valide : position sizing ATR, stops distance, drawdown, kill switch
6. Le bot exécute l'ordre via MT5 si toutes les conditions sont remplies
7. Tout est journalisé dans `trade_journal.jsonl` (chaîne de hash SHA-256)

---

## Stack technique
```
Windows + Python 3.10.11
│
├─ MetaTrader5 (API Python) ──────▶ exécution ordres réels
├─ Requests / HTTP ────────────────▶ communication IA multi-provider
├─ Flask + Waitress ───────────────▶ Dashboard (5004) + AI Engine (5003)
├─ Authentification ───────────────▶ SHA-256 access key + API token
├─ Logging (rotation + JSON) ──────▶ logs structurés + journal hashé
└─ .env / dotenv ──────────────────▶ configuration runtime
```

---

## Fonctionnalités

### Trading & IA
- ✅ **Trading réel MT5** — 8 paires, multi-symboles simultanés
- ✅ **IA Multi-Provider** — Groq (LLaMA 3.3 70B), OpenAI GPT (GPT-4o-mini), DeepSeek
- ✅ **Switching provider en temps réel** — depuis le dashboard ou l'API
- ✅ **Même SYSTEM_PROMPT** partagé par tous les providers (règles identiques)
- ✅ **Payload multi-timeframes** — M1, M5, H1, H4, D1 avec 15+ indicateurs
- ✅ **Auto-évaluation IA** — l'IA voit son historique de trades et s'auto-corrige
- ✅ **Confidence scoring** — seuil minimum configurable (défaut : 0.90)
- ✅ **Position sizing ATR** — calcul basé sur `tick_value` réel MT5

### Sécurité & Risk Management
- ✅ **RiskGuardian** — drawdown global, kill switch, limites fréquence
- ✅ **Stop level validation** — vérification distance SL/TP vs broker
- ✅ **Authentification dashboard** — clé d'accès 64 chars, SHA-256
- ✅ **API token** — communication bot ↔ moteur IA sécurisée
- ✅ **Journal hashé** — chaîne de hash SHA-256 pour traçabilité
- ✅ **Filtre spread** — blocage au-dessus du seuil configuré
- ✅ **Hard-stop journalier** — arrêt si perte max atteinte
- ✅ **Watchdog IA** — cooldown automatique après erreurs consécutives

### Infrastructure
- ✅ **Lanceur intelligent** — redémarrage auto, retry avec backoff
- ✅ **Dashboard web** — statut, marchés, journal, logs, payload, maintenance
- ✅ **Sélecteur provider IA** — boutons dans le dashboard avec statut temps réel
- ✅ **Purge auto/manuelle des logs** — backup avant purge
- ✅ **Cleanup mémoire** — garbage collection périodique
- ✅ **Position Monitor** — surveillance continue des positions ouvertes

---

## Démarrage rapide

```bash
# 1. Activer l'environnement virtuel
env\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer .env (copier depuis .env.example)
copy .env.example .env
# → Remplir MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, GROQ_API_KEY

# 4. Générer la clé d'accès dashboard
python generate_access_key.py

# 5. Lancer le système complet
python lanceur_automatique.py
```

### Démarrage séparé (debug)
```bash
python -m backend.ai.adaptive_engine     # IA Engine (port 5003)
python -m backend.dashboard_app          # Dashboard (port 5004)
python main.py --mode REAL --strategy MICRO --ai-engine --risk 0.5
```

### Accès
- **Dashboard** : http://localhost:5004 (clé d'accès requise)
- **AI Engine** : http://localhost:5003 (token API requis)

---

## Configuration (.env)

Copier `.env.example` en `.env` et remplir les valeurs. Variables principales :

### Connexion MT5
| Variable | Description | Défaut |
|----------|-------------|--------|
| `MT5_LOGIN` | Numéro de compte MT5 | — |
| `MT5_PASSWORD` | Mot de passe MT5 | — |
| `MT5_SERVER` | Serveur broker | — |

### Providers IA (multi-provider)
| Variable | Description | Défaut |
|----------|-------------|--------|
| `GROQ_API_KEY` | Clé API Groq | — |
| `GROQ_MODEL` | Modèle Groq | `llama-3.3-70b-versatile` |
| `OPENAI_API_KEY` | Clé API OpenAI | — |
| `OPENAI_MODEL` | Modèle OpenAI | `gpt-4o-mini` |
| `DEEPSEEK_API_KEY` | Clé API DeepSeek | — |
| `DEEPSEEK_MODEL` | Modèle DeepSeek | `deepseek-chat` |
| `ACTIVE_AI_PROVIDER` | Provider actif | `groq` |

### Trading & Risque
| Variable | Description | Défaut |
|----------|-------------|--------|
| `RISK_PER_TRADE` | Risque par trade (%) | `0.5` |
| `REQUIRED_CONFIDENCE` | Confidence IA minimum | `0.90` |
| `MAX_DAILY_LOSS_PCT` | Perte max journalière (%) | `2.0` |
| `MAX_TRADES_PER_HOUR` | Trades max par heure | `6` |
| `MAX_TRADES_PER_DAY` | Trades max par jour | `60` |
| `MIN_SECONDS_BETWEEN_TRADES` | Cooldown entre trades (s) | `15` |
| `MAX_SPREAD_POINTS` | Spread max autorisé | `100` |
| `MAX_SLIPPAGE_POINTS` | Slippage max (pts) | `25` |

### Sécurité
| Variable | Description |
|----------|-------------|
| `ACCESS_KEY_HASH` | Hash SHA-256 de la clé dashboard |
| `API_SECRET_TOKEN` | Token API interne (bot ↔ IA) |
| `FLASK_SECRET_KEY` | Clé secrète Flask (sessions) |
| `DASHBOARD_SECRET` | Secret dashboard |

---

## Modules (arborescence)

### Racine
| Fichier | Rôle |
|---------|------|
| `main.py` | Point d'entrée bot — init MT5, lance la stratégie |
| `lanceur_automatique.py` | Lanceur intelligent — start/stop/restart, monitoring, cleanup |
| `generate_access_key.py` | Génère la clé d'accès dashboard |
| `.env` / `.env.example` | Configuration secrets/paramètres |

### Backend — IA (`backend/ai/`)
| Fichier | Rôle |
|---------|------|
| `base_provider.py` | Classe abstraite `BaseAIProvider` — interface commune |
| `groq_service.py` | Provider Groq (hérite de BaseAIProvider) |
| `openai_service.py` | Provider OpenAI GPT |
| `deepseek_service.py` | Provider DeepSeek |
| `provider_manager.py` | Gestionnaire multi-provider — switching thread-safe |
| `adaptive_engine.py` | Serveur Flask IA — SYSTEM_PROMPT, endpoints, décision |

### Backend — Bot (`backend/bots/`)
| Fichier | Rôle |
|---------|------|
| `bot_btcusd_ultra_scalper_v8_clean.py` | Bot principal — analyse, payload, exécution, journal |

### Backend — Core (`backend/core/`)
| Fichier | Rôle |
|---------|------|
| `indicators.py` | 15+ indicateurs techniques (RSI, EMA, MACD, BB, ATR…) |
| `risk_guardian.py` | Gestion risque — position sizing ATR, stop validation, kill switch |
| `smart_payload.py` | Compression sémantique du payload IA |
| `position_monitor.py` | Surveillance continue des positions ouvertes |
| `engine.py` | Initialisation moteur |

### Backend — Sécurité (`backend/security/`)
| Fichier | Rôle |
|---------|------|
| `auth.py` | Authentification — `verify_key()`, `require_api_token`, `require_dashboard_auth` |

### Backend — Config (`backend/config/`)
| Fichier | Rôle |
|---------|------|
| `config_micro_scalping_pro.py` | SYMBOLS_CONFIG (8 paires), timeframes, spreads, lots |

### Dashboard
| Fichier | Rôle |
|---------|------|
| `backend/dashboard_app.py` | API dashboard Flask — status, journal, logs, provider switching |
| `templates/dashboard.html` | Interface web — grille, marchés, sélecteur provider IA |
| `templates/login.html` | Page de connexion sécurisée |

---

## Endpoints API

### AI Engine (port 5003)
| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/health` | Non | État du service |
| `GET` | `/api/providers` | Non | Liste providers + statut |
| `POST` | `/api/decision` | Token | Décision IA (JSON payload) |
| `POST` | `/api/switch-provider` | Token | Changer de provider actif |

### Dashboard (port 5004)
| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/` | Session | Dashboard principal |
| `GET` | `/api/status` | Session | Status global système |
| `GET` | `/api/journal` | Session | Journal trading |
| `GET` | `/api/ai` | Session | Décisions IA récentes |
| `GET` | `/api/logs` | Session | Logs lanceur |
| `GET` | `/api/markets` | Session | État par marché |
| `GET` | `/api/symbols` | Session | Symboles configurés |
| `GET` | `/api/ai-provider` | Session | Statut providers IA |
| `POST` | `/api/ai-provider` | Session | Changer provider IA |
| `POST` | `/api/purge-logs` | Session | Purge manuelle des logs |
| `GET` | `/api/maintenance` | Session | Tailles logs + dernière purge |

### Contrôleur (port 5010)
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/status` | Métriques système |
| `POST` | `/start` | Démarrer le système |
| `POST` | `/stop` | Arrêter le système |
| `POST` | `/restart` | Redémarrer le système |

---

## IA — Fonctionnement détaillé

### SYSTEM_PROMPT (partagé par tous les providers)
L'IA reçoit un prompt structuré avec :
- **ACCOUNTABILITY** — l'IA est responsable de chaque trade
- **PAYLOAD STRUCTURE** — description des données reçues
- **DECISION RULES** — 7 conditions obligatoires pour BUY/SELL (défaut = HOLD)
- **SELF-CORRECTION** — ajustements basés sur l'historique de performance
- **HARD CONSTRAINTS** — règles non dérogeables (cooldown, limites, risk)
- **CONFIDENCE SCORING** — calcul systématique 0.0–1.0 (min requis : 0.90)
- **SL/TP RULES** — SL = 2.0× ATR, TP = R:R 2.0:1 minimum

### Auto-évaluation
L'IA reçoit dans chaque payload son propre historique via `my_trade_history` :
- 5 derniers trades fermés (profit, raison de clôture, type, volume)
- Statistiques : win_rate, net_pnl, avg_win/loss, SL/TP hit counts, streak
- Après 2+ pertes consécutives → restrictions automatiques
- Après 3+ pertes → HOLD forcé

### Scoring de confiance
```
Base = 0.50
+ 0.10 si alignment multi-TF
+ 0.05 par TF avec confluence ≥ 75 (max +0.25)
+ 0.10 si trending sur 3+ TFs
- 0.20 si squeeze détecté
- 0.10 si spread > 20 pts
- 0.10 par perte consécutive
- 0.15 si win_rate < 50%
Maximum théorique ≈ 0.95
```

### Indicateurs envoyés
Par timeframe (M1, M5, H1, H4, D1) :
- **Trend** : direction, force, EMA alignment
- **Volatilité** : ATR%, BB width, squeeze detection
- **Momentum** : RSI, MACD histogram/direction, Stochastic K/D, MFI
- **Confluence** : bias, score, signaux bull/bear
- **Key levels** : pivots, Fibonacci
- **Candle patterns** : doji, pin bar, engulfing, hammer, shooting star, inside bar, marubozu, harami
- **Market regime** : TRENDING_UP/DOWN, RANGING

---

## Journalisation
Fichier : `logs/trade_journal.jsonl` — chaque ligne est un événement JSON avec hash SHA-256.

Types d'événements :
- `decision` — décision IA (action, confidence, raison)
- `order_filled` — ordre exécuté
- `order_rejected` — ordre rejeté par MT5
- `blocked` — trade bloqué par risk guardian
- `slippage_alert` — glissement détecté
- `hard_stop` — kill switch activé

---

## Dépannage

| Problème | Solution |
|----------|----------|
| IA indisponible | Vérifier `GROQ_API_KEY` / `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` et réseau |
| Ordres rejetés | Volume min MT5, marché fermé, symbole non visible |
| Dashboard vide | Vérifier services sur ports 5003 / 5004 / 5010 |
| Bot crashe au démarrage | Vérifier `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` dans `.env` |
| Confidence toujours trop basse | Normal avec REQUIRED_CONFIDENCE=0.90 — le bot est très sélectif |
| Spread trop élevé | Ajuster `MAX_SPREAD_POINTS` ou trader pendant les heures liquides |
| RAM haute | Vérifier logs + purge auto + fréquence IA |

---

## Bibliothèques

### Core
- Python 3.10, MetaTrader5, requests, python-dotenv

### Web / API
- Flask, Waitress

### Data
- numpy, pandas, h5py

### Utilitaires
- psutil, colorama
