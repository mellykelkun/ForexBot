# AUDIT FOREXBOT — PROBLÈMES CRITIQUES DÉTECTÉS
> Date : 12 février 2026  
> Auditeur : GitHub Copilot  
> Version auditée : BTCUSD Micro Scalper V8 Pro  
> Statut : **URGENT — TRADING RÉEL EN COURS**

---

## TABLE DES MATIÈRES
1. [SÉCURITÉ DES FONDS (CRITIQUE)](#1-sécurité-des-fonds-critique)
2. [CALCULS DE MARCHÉ (HAUTE PRIORITÉ)](#2-calculs-de-marché-haute-priorité)
3. [LOGIQUE DE TRADING (HAUTE PRIORITÉ)](#3-logique-de-trading-haute-priorité)
4. [ARCHITECTURE & RÉSEAU (MOYENNE PRIORITÉ)](#4-architecture--réseau-moyenne-priorité)
5. [QUALITÉ DE CODE (MOYENNE PRIORITÉ)](#5-qualité-de-code-moyenne-priorité)
6. [PERFORMANCE & MÉMOIRE (BASSE PRIORITÉ)](#6-performance--mémoire-basse-priorité)
7. [ROADMAP DE CORRECTION](#7-roadmap-de-correction)

---

## 1. SÉCURITÉ DES FONDS (CRITIQUE)

### SEC-01 — Aucune protection SL/TP de secours
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (ligne ~860-880)
- **Problème** : Si l'IA Groq renvoie `sl_price: null` ou `tp_price: null`, l'ordre MT5 est envoyé **sans Stop Loss et sans Take Profit**. La position est complètement nue.
- **Impact** : Perte potentielle **totale du capital** sur un mouvement violent.
- **Correction** : Ajouter un SL/TP de secours calculé automatiquement basé sur l'ATR si l'IA ne les fournit pas.

### SEC-02 — Dashboard sans authentification
- **Fichier** : `backend/dashboard_app.py`
- **Problème** : Le dashboard Flask écoute sur `0.0.0.0:5004` sans aucune authentification. Les endpoints `/api/control/start`, `/api/control/stop`, `/api/purge-logs` sont accessibles par n'importe qui.
- **Impact** : Un attaquant sur le réseau peut **arrêter le bot**, **purger les logs**, ou **relancer le système** à distance.
- **Correction** : Ajouter une authentification JWT ou mot de passe + restriction IP.

### SEC-03 — API IA sans authentification
- **Fichier** : `backend/ai/adaptive_engine.py` (ligne ~90)
- **Problème** : Le serveur IA écoute sur `0.0.0.0:5003`. L'endpoint `/api/decision` accepte n'importe quel POST JSON.
- **Impact** : Un attaquant peut envoyer de fausses décisions `BUY/SELL` au bot.
- **Correction** : Ajouter un token secret dans les headers, restreindre à `127.0.0.1`.

### SEC-04 — Credentials MT5 en clair dans .env
- **Fichier** : `.env` (login, password, server)
- **Problème** : Les identifiants de connexion MT5 (accès au capital réel) sont stockés en texte brut.
- **Impact** : Si le fichier est compromis, accès complet au compte de trading.
- **Correction** : Chiffrement des credentials avec une clé maître ou utilisation d'un gestionnaire de secrets.

### SEC-05 — Pas de max drawdown global (equity)
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (ligne ~685)
- **Problème** : Le hard-stop est **journalier uniquement** (`max_daily_loss_pct = 2%`). Il se réinitialise chaque jour. Ainsi, une perte de 2%/jour pendant 25 jours = perte de 50% sans déclenchement.
- **Impact** : Érosion progressive et invisible du capital.
- **Correction** : Ajouter un max drawdown global sur l'equity totale (ex: 10% du capital initial).

### SEC-06 — Pas de kill switch d'urgence
- **Fichier** : Aucun
- **Problème** : Il n'existe aucun mécanisme pour fermer **toutes les positions ouvertes** immédiatement et bloquer tout nouveau trading.
- **Impact** : En cas de bug ou de marché extrême, impossibilité de tout couper rapidement.
- **Correction** : Implémenter un endpoint `/api/emergency-stop` qui ferme toutes positions + bloque le bot.

### SEC-07 — Volume toujours à min_lot (pas de position sizing)
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (ligne ~838)
- **Problème** : `desired_volume = SYMBOLS_CONFIG.get(symbol, {}).get("min_lot", 0.01)` — le volume est toujours le minimum, sans rapport avec le capital, le risque ou la volatilité.
- **Impact** : Utilisation non optimale du capital. La fonction `calculate_position_size()` existe dans la config mais n'est **jamais appelée**.
- **Correction** : Utiliser `calculate_position_size()` avec le capital actuel, le SL et la volatilité.

### SEC-08 — Script restart_bot.py tue TOUS les processus Python
- **Fichier** : `scripts/ops/restart_bot.py` (ligne 12)
- **Problème** : `os.system("taskkill /f /im python.exe 2>nul")` tue **tous** les processus Python du système, pas seulement ForexBot.
- **Impact** : Destruction de tout travail Python en cours sur la machine.
- **Correction** : Utiliser les PID spécifiques du bot ou un fichier PID.

### SEC-09 — Pas de vérification de la latence réseau avant trading
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py`
- **Problème** : Le bot vérifie la latence **après** l'exécution de l'ordre (ligne ~880), pas avant. L'alerte est un simple warning, pas un blocage.
- **Impact** : Exécution avec slippage élevé non contrôlé.
- **Correction** : Vérifier la latence AVANT l'envoi de l'ordre et bloquer si > seuil.

---

## 2. CALCULS DE MARCHÉ (HAUTE PRIORITÉ)

### CALC-01 — RSI calculé avec SMA au lieu de Wilder (EMA)
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_rsi`, ligne ~186)
- **Problème** : Le RSI utilise une moyenne arithmétique simple (`avg_gain = gains / period`). Le standard RSI de Wilder utilise un lissage exponentiel (EMA). De plus, seules les N premières barres sont calculées, sans smoothing glissant.
- **Impact** : Le RSI est bruyant et ne reflète pas les conditions réelles du marché. Les zones de surachat/survente sont faussées.
- **Correction** : Implémenter le RSI de Wilder avec lissage exponentiel sur toute la série.

### CALC-02 — EMA ne fait qu'un seul passage
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_ema`, ligne ~170)
- **Problème** : La fonction parcourt les closes dans l'ordre `values[0]` → `values[-1]`, mais les données de MT5 sont reçues du plus récent au plus ancien (après le `[::-1]`). L'EMA démarre donc de la valeur la plus récente et calcule vers le passé — l'inverse du calcul standard.
- **Impact** : Toutes les EMA (9, 21, fast MACD, slow MACD) sont incorrectes. Le croisement EMA qui devrait signaler un BUY pourrait signaler un SELL.
- **Correction** : Calcul EMA du passé vers le présent (inverser l'itération ou corriger l'ordre des données).

### CALC-03 — MACD : signal line = macd line (toujours)
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_macd`, ligne ~279)
- **Problème** :
  ```python
  macd_line = ema_fast - ema_slow
  signal_line = macd_line           # ← BUG : devrait être EMA(9) du MACD
  hist = macd_line - signal_line    # ← TOUJOURS 0
  ```
- **Impact** : L'histogramme MACD est **toujours zéro**. Le signal de croisement MACD/Signal est toujours "neutre". L'IA reçoit des données MACD inutiles.
- **Correction** : Calculer une série MACD complète, puis appliquer EMA-9 sur cette série pour obtenir la signal line.

### CALC-04 — ATR : indices inversés dans la boucle
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_atr`, ligne ~261)
- **Problème** :
  ```python
  for i in range(1, period + 1):
      tr = max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), ...)
  ```
  Les données sont triées du plus récent au plus ancien. `closes[i-1]` est le close **plus récent** que `highs[i]`, alors que l'ATR devrait comparer avec le close **précédent** (plus ancien).
- **Impact** : L'ATR est biaisé, ce qui affecte le calcul de la volatilité et potentiellement les SL/TP.
- **Correction** : Corriger le sens des indices pour respecter l'ordre chronologique.

### CALC-05 — Stochastic basique sans %D
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_stochastic`, ligne ~290)
- **Problème** : Seul le %K est calculé. Le %D (moyenne mobile du %K) est absent.
- **Impact** : Pas de confirmation du signal stochastique, signaux plus bruyants.
- **Correction** : Ajouter le calcul du %D (SMA-3 du %K).

### CALC-06 — Bollinger Bands : stddev de population au lieu d'échantillon
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_bollinger`, ligne ~298)
- **Problème** : `variance = sum((v - mean) ** 2 for v in window) / period` — division par N au lieu de N-1.
- **Impact** : Bandes légèrement plus étroites que la réalité, faux signaux de breakout.
- **Correction** : Utiliser `/ (period - 1)` pour l'écart-type d'échantillon.

### CALC-07 — OBV calcul inversé
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_obv`, ligne ~236)
- **Problème** : L'OBV compare `closes[i-1] > closes[i]`, mais avec les données triées du plus récent au plus ancien, `closes[i-1]` est **plus récent** que `closes[i]`. Le sens est inversé par rapport à la convention (si prix monte → ajouter volume).
- **Impact** : L'OBV indique l'inverse de la pression acheteuse/vendeuse réelle.
- **Correction** : Inverser la comparaison ou travailler avec les données dans l'ordre chronologique.

### CALC-08 — MFI (Money Flow Index) indices inversés
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_mfi`, ligne ~248)
- **Problème** : Même souci que l'OBV — les comparaisons `tp_curr > tp_prev` sont inversées à cause de l'order des données.
- **Impact** : MFI indique le contraire de la réalité (surachat ↔ survente).
- **Correction** : Aligner avec l'ordre chronologique des données.

### CALC-09 — ADX simplifié (pas de vrai lissage)
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_adx`, ligne ~255)
- **Problème** : Le calcul utilise une simple somme sur N barres au lieu du lissage exponentiel de Wilder pour le True Range, +DM et -DM. De plus, un seul DX est calculé au lieu d'une moyenne glissante de DX (le vrai ADX).
- **Impact** : L'ADX ne reflète pas la force réelle de la tendance.
- **Correction** : Implémenter le lissage de Wilder et la moyenne glissante du DX.

### CALC-10 — Support/Résistance et Fibonacci jamais implémentés
- **Fichier** : `backend/config/config_micro_scalping_pro.py` (ligne ~633)
- **Problème** : Les configs `SUPPORT_RESISTANCE_CONFIG` et `MULTI_TIMEFRAME_ANALYSIS` sont définies mais **aucun code ne les utilise**.
- **Impact** : L'IA ne reçoit pas les niveaux clés du marché (S&R, Fibonacci, pivot points).
- **Correction** : Implémenter les calculs de S&R dynamiques et les inclure dans le payload IA.

### CALC-11 — RSI calculé différemment dans engine.py vs bot
- **Fichier** : `backend/core/engine.py` (ligne ~240) vs `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py`
- **Problème** : Deux implémentations différentes du RSI existent. `engine.py` utilise `np.diff()` et sépare gains/losses avec une condition, le bot utilise une boucle. Aucune des deux n'est le vrai RSI de Wilder.
- **Impact** : Incohérence des signaux selon quel module est utilisé.
- **Correction** : Une seule implémentation correcte dans un module partagé.

---

## 3. LOGIQUE DE TRADING (HAUTE PRIORITÉ)

### TRADE-01 — Sortie intelligente désactivée dans la config
- **Fichier** : `backend/config/config_micro_scalping_pro.py` (ligne ~345)
- **Problème** : `INTELLIGENT_EXIT_CONFIG["enabled"] = False` et `GUARDIAN_SYSTEM_CONFIG["enabled"] = False`.
- **Impact** : Les systèmes de sortie intelligente et Guardian sont inactifs malgré toute la configuration écrite.
- **Correction** : Activer et implémenter la boucle de monitoring de sortie dans le bot.

### TRADE-02 — Pas de gestion de sortie des positions ouvertes
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py`
- **Problème** : Le bot gère l'entrée via l'IA (`context: "entry"`) mais il n'y a **aucun code** pour surveiller les positions ouvertes et demander à l'IA une décision de sortie (`context: "exit"`).
- **Impact** : Les positions restent ouvertes indéfiniment jusqu'à ce que MT5 touche le SL/TP (si définis) ou que le marché les ferme.
- **Correction** : Implémenter un cycle de monitoring des positions ouvertes avec appel IA en contexte "exit".

### TRADE-03 — Payload IA excessivement volumineux
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (ligne ~146-151)
- **Problème** : `bars_m1 = 1000`, `bars_m5 = 1000`, `bars_h1 = 2000`, `bars_h4 = 2000`, `bars_d1 = 2000`. Le payload envoyé contient des centaines de milliers de données numériques d'indicateurs sur 5 timeframes.
- **Impact** : 
  - Latence IA élevée (traitement token lourd)
  - Coût Groq excessif
  - Le LLM est limité en contexte et ne peut pas réellement analyser 8000 bougies
- **Correction** : Résumer les indicateurs (dernières 3-5 valeurs par timeframe, pas toutes les bougies).

### TRADE-04 — Pas de validation croisée post-IA
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `executer_strategie_micro_ia`)
- **Problème** : La décision IA est acceptée telle quelle si `confidence >= required_confidence`. Pas de double-check avec les indicateurs locaux.
- **Impact** : L'IA peut donner un signal BUY alors que le RSI est à 95 (surachat extrême) — le bot exécute quand même.
- **Correction** : Ajouter un filtre local post-IA (RSI extrême, divergence, volatilité excessive, etc.).

### TRADE-05 — Backtest non fiable
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `run_backtest`, ligne ~948)
- **Problème** :
  - Utilise le close comme bid ET ask (pas de spread réaliste)
  - Sortie systématique à la bougie suivante (pas de logique SL/TP)
  - Appelle réellement l'API IA Groq pour chaque bougie (~500 appels API !)
  - Pas de gestion de position (toujours flat)
- **Impact** : Résultats de backtest non représentatifs du trading réel.
- **Correction** : Backtest local avec simulation bid/ask, SL/TP, et heuristique locale (pas API IA).

### TRADE-06 — Pas de contexte de marché (sessions, news, jours fériés)
- **Fichier** : Payload IA dans `_build_payload`
- **Problème** : Bien que `TRADING_SESSIONS` soit configuré (Asia, London/NY overlap), cette information n'est **jamais envoyée** à l'IA et jamais utilisée pour filtrer.
- **Impact** : L'IA prend des décisions sans savoir si le marché est en session morte ou en overlap actif.
- **Correction** : Inclure la session active et le contexte temporel dans le payload.

### TRADE-07 — Le bot ne vérifie pas les positions déjà ouvertes avant d'en ouvrir une nouvelle
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `executer_trade`)
- **Problème** : Aucune vérification du nombre de positions ouvertes avant d'en ouvrir une nouvelle. `max_concurrent_trades = 3` est configuré mais jamais vérifié.
- **Impact** : Le bot peut ouvrir des positions illimitées, contredisant la gestion du risque.
- **Correction** : Vérifier `mt5.positions_get()` avant chaque ouverture et bloquer si le max est atteint.

---

## 4. ARCHITECTURE & RÉSEAU (MOYENNE PRIORITÉ)

### ARCH-01 — engine.py n'est jamais utilisé par le bot
- **Fichier** : `backend/core/engine.py`
- **Problème** : La classe `AdvancedMT5Engine` (737 lignes) avec gestion reconnexion, métriques, etc. n'est jamais importée par le bot principal. Le bot gère MT5 directement via `import MetaTrader5 as mt5`.
- **Impact** : Code mort de 737 lignes. Fonctionnalités avancées (reconnexion thread-safe, métriques) perdues.
- **Correction** : Intégrer le bot pour utiliser `AdvancedMT5Engine` ou supprimer le code mort.

### ARCH-02 — Serveur de contrôle (port 5010) sans auth
- **Fichier** : `lanceur_automatique.py` (ligne ~785)
- **Problème** : Le serveur HTTP de contrôle sur `127.0.0.1:5010` accepte les commandes POST `/start`, `/stop`, `/restart` sans aucune authentification.
- **Impact** : Tout processus local peut arrêter/redémarrer le système de trading.
- **Correction** : Ajouter un token de sécurité ou restreindre l'accès.

### ARCH-03 — Pas de health check bidirectionnel
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `perform_health_check`)
- **Problème** : Le bot vérifie que l'IA est up (`/health`), mais l'IA ne vérifie jamais que le bot est toujours en vie.
- **Impact** : Si le bot crash, l'IA continue de tourner sans savoir que personne ne consomme ses décisions.
- **Correction** : Implémenter un heartbeat bidirectionnel.

### ARCH-04 — Pas de rate limiting sur les APIs
- **Fichier** : `backend/dashboard_app.py`, `backend/ai/adaptive_engine.py`
- **Problème** : Aucun rate limiting sur les endpoints. Le dashboard poll toutes les 5 secondes sans restriction.
- **Impact** : Vulnérabilité aux attaques DoS, consommation CPU inutile.
- **Correction** : Ajouter Flask-Limiter ou middleware de rate limiting.

### ARCH-05 — Communication HTTP au lieu de WebSocket pour les décisions
- **Fichier** : Bot → IA via `requests.post()`
- **Problème** : Chaque itération fait un POST HTTP complet. Pour du micro-scalping, la latence HTTP overhead est significative.
- **Impact** : Latence supplémentaire de 50-200ms par décision.
- **Correction** : Pas critique immédiatement, mais envisager WebSocket ou gRPC pour le futur.

---

## 5. QUALITÉ DE CODE (MOYENNE PRIORITÉ)

### CODE-01 — CANDLESTICK_CONFIG défini 2 fois
- **Fichier** : `backend/config/config_micro_scalping_pro.py` (ligne ~510 et ~605)
- **Problème** : La variable est déclarée deux fois. La seconde écrase la première.
- **Impact** : Configuration imprévisible.
- **Correction** : Supprimer la première définition ou fusionner.

### CODE-02 — detect_gold_symbol() code dupliqué
- **Fichier** : `backend/config/config_micro_scalping_pro.py` (méthode `Config.detect_gold_symbol`)
- **Problème** : Le corps de la méthode est dupliqué — deux blocs `try/except` identiques l'un après l'autre. Le second est du code mort (jamais atteint).
- **Impact** : Code mort confus.
- **Correction** : Supprimer le second bloc.

### CODE-03 — Fonctions mal indentées dans la classe Config
- **Fichier** : `backend/config/config_micro_scalping_pro.py` (ligne ~803)
- **Problème** : `test_configuration()`, `get_symbol_exit_rules()`, `is_quick_exit_enabled()`, `get_max_position_age()` sont définies **à l'intérieur** de la classe Config mais comme des fonctions normales (pas de `self`). `test_configuration()` est appelée au moment de la **définition de la classe**.
- **Impact** : Ces fonctions s'exécutent au moment de l'import du module et ne sont pas des vraies méthodes de classe.
- **Correction** : Les sortir de la classe ou les faire en `@staticmethod`.

### CODE-04 — Import psutil dupliqué
- **Fichier** : `lanceur_automatique.py` (lignes 11 et 21)
- **Problème** : `import psutil` apparaît deux fois.
- **Impact** : Mineur, mais indicateur de maintenance hasardeuse.
- **Correction** : Supprimer le doublon.

### CODE-05 — Bare except (catch-all sans type)
- **Fichiers** : Multiples fichiers
- **Problème** : De nombreux `except:` sans spécifier le type d'exception (`except Exception as e:` minimum).
- **Impact** : Masque les erreurs critiques comme `SystemExit`, `KeyboardInterrupt`, `MemoryError`.
- **Correction** : Remplacer tous les `except:` par `except Exception as e:` minimum.

### CODE-06 — Pas de type hints sur de nombreuses fonctions critiques
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py`
- **Problème** : Les méthodes de calcul d'indicateurs n'ont pas de type hints de retour ni de documentation sur les contraintes d'entrée.
- **Impact** : Difficulté de maintenance et risque de bugs d'interface.
- **Correction** : Ajouter les type hints et docstrings.

### CODE-07 — `RiskManager.can_trade()` retourne un tuple non typé
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (ligne ~114)
- **Problème** : `def can_trade(...) -> (bool, str):` — la syntaxe `(bool, str)` n'est pas un type hint valide en Python. Il faudrait `Tuple[bool, str]`.
- **Impact** : Pas de vérification de type possible.
- **Correction** : Utiliser `Tuple[bool, str]` depuis `typing`.

---

## 6. PERFORMANCE & MÉMOIRE (BASSE PRIORITÉ)

### PERF-01 — Garbage collection ultra-agressive (10 passes)
- **Fichier** : `lanceur_automatique.py` (méthode `force_garbage_collection`)
- **Problème** : 10 passes de `gc.collect()` avec `time.sleep(0.01)` entre chaque. La plupart des objets sont collectés dès la 1ère ou 2ème passe.
- **Impact** : Gaspillage CPU toutes les 60 secondes.
- **Correction** : 2-3 passes maximum, arrêter dès que `collected == 0`.

### PERF-02 — Nettoyage TensorFlow fantôme
- **Fichier** : `lanceur_automatique.py` (méthode `comprehensive_cleanup`)
- **Problème** : `clear_tensorflow_memory()` est appelée 2 fois mais la méthode est un no-op (retourne `False` avec le commentaire "IA locale supprimée").
- **Impact** : Code mort, confusion.
- **Correction** : Supprimer les appels à `clear_tensorflow_memory()`.

### PERF-03 — Thread de maintenance logger tourne toutes les heures sans possibilité d'arrêt
- **Fichier** : `backend/utils/advanced_logger.py` (méthode `_maintenance_worker`)
- **Problème** : `while True` avec `threading.Event().wait(3600)` — crée un nouvel Event à chaque itération (leak). Pas de moyen de stopper le thread.
- **Impact** : Thread zombie en cas de shutdown.
- **Correction** : Créer l'Event une seule fois et utiliser un flag d'arrêt.

### PERF-04 — cleanup_databases.py supprime tous les processus Python
- **Fichier** : `scripts/maintenance/cleanup_databases.py` (méthode `kill_python_processes`)
- **Problème** : `taskkill /f /im python.exe` — même problème que SEC-08.
- **Impact** : Détruit tout environnement Python actif.
- **Correction** : Ne pas tuer les processus dans un script de nettoyage de base de données.

### PERF-05 — Aucune mise en cache des indicateurs entre timeframes
- **Fichier** : `backend/bots/bot_btcusd_ultra_scalper_v8_clean.py` (méthode `_compute_indicators`)
- **Problème** : Chaque appel `_compute_indicators()` charge les données brutes depuis MT5 et recalcule tout. Pour 8 symboles × 5 timeframes = 40 appels MT5 par cycle.
- **Impact** : Latence excessive et charge CPU.
- **Correction** : Cache les données brutes et ne recalcule que si les données ont changé.

---

## 7. ROADMAP DE CORRECTION

### Phase 1 — URGENCE SÉCURITÉ (semaine 1)
| # | Tâche | Ticket |
|---|-------|--------|
| 1 | SL/TP de secours obligatoires (ATR-based) | SEC-01 |
| 2 | Max drawdown global equity | SEC-05 |
| 3 | Kill switch d'urgence | SEC-06 |
| 4 | Vérifier positions ouvertes avant d'ouvrir | TRADE-07 |
| 5 | Position sizing dynamique | SEC-07 |
| 6 | Authentification Dashboard + API IA | SEC-02, SEC-03 |
| 7 | Restreindre API IA à 127.0.0.1 | SEC-03 |
| 8 | Corriger les scripts kill-all-python | SEC-08 |

### Phase 2 — CALCULS MARCHÉ (semaine 2)
| # | Tâche | Ticket |
|---|-------|--------|
| 9 | Corriger RSI Wilder | CALC-01 |
| 10 | Corriger EMA (sens du calcul) | CALC-02 |
| 11 | Corriger MACD signal line | CALC-03 |
| 12 | Corriger ATR indices | CALC-04 |
| 13 | Corriger OBV et MFI (sens des données) | CALC-07, CALC-08 |
| 14 | Corriger Bollinger stddev | CALC-06 |
| 15 | Ajouter %D au Stochastic | CALC-05 |
| 16 | Implémenter ADX avec lissage Wilder | CALC-09 |

### Phase 3 — LOGIQUE TRADING (semaine 3)
| # | Tâche | Ticket |
|---|-------|--------|
| 17 | Monitoring/sortie des positions ouvertes | TRADE-02 |
| 18 | Réduire la taille des payloads IA | TRADE-03 |
| 19 | Validation croisée post-IA | TRADE-04 |
| 20 | Ajouter session/contexte au payload | TRADE-06 |
| 21 | S&R et Fibonacci dynamiques | CALC-10 |

### Phase 4 — NETTOYAGE CODE (semaine 4)
| # | Tâche | Ticket |
|---|-------|--------|
| 22 | Supprimer/intégrer engine.py | ARCH-01 |
| 23 | Corriger les doublons de code config | CODE-01..06 |
| 24 | Optimiser le garbage collection | PERF-01..02 |
| 25 | Cache indicateurs MT5 | PERF-05 |
| 26 | Backtest local fiable | TRADE-05 |

---

## RÉSUMÉ

| Catégorie | Nombre de problèmes | Sévérité |
|-----------|---------------------|----------|
| Sécurité des fonds | 9 | **CRITIQUE** |
| Calculs de marché | 11 | **HAUTE** |
| Logique de trading | 7 | **HAUTE** |
| Architecture/Réseau | 5 | **MOYENNE** |
| Qualité de code | 7 | **MOYENNE** |
| Performance/Mémoire | 5 | **BASSE** |
| **TOTAL** | **44 problèmes** | |

> **ATTENTION** : Ce système trade en argent réel. Les problèmes de catégorie CRITIQUE et HAUTE doivent être corrigés **avant toute continuation du trading**.
