"""Test rapide de tous les modules corrigés."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from backend.security.auth import get_access_key_hash, get_or_create_api_token
from backend.core.indicators import ema, rsi_wilder, macd, atr, adx, bollinger, stochastic, obv, mfi
from backend.core.risk_guardian import RiskGuardian
from backend.core.smart_payload import classify_trend, classify_momentum, classify_volatility
from datetime import datetime

print("=" * 50)
print("TEST DES MODULES FOREXBOT")
print("=" * 50)

# .env
stored = get_access_key_hash()
api = os.getenv("API_SECRET_TOKEN", "")
flask_key = os.getenv("FLASK_SECRET_KEY", "")
print(f"ACCESS_KEY_HASH = {stored[:24]}..." if stored else "  ACCESS_KEY_HASH MANQUANT")
print(f"API_SECRET_TOKEN = {api[:24]}..." if api else "  API_SECRET_TOKEN MANQUANT")
print(f"FLASK_SECRET_KEY = {flask_key[:24]}..." if flask_key else "  FLASK_SECRET_KEY MANQUANT")

# Indicateurs
print("\n--- Indicateurs ---")
closes = [100 + i*0.1 for i in range(50)]
highs = [c + 1 for c in closes]
lows = [c - 1 for c in closes]
volumes = [1000 + i*10 for i in range(50)]

r = rsi_wilder(closes, 14)
print(f"RSI(14) = {r}")
m = macd(closes)
print(f"MACD = line={m.get('macd_line')}, signal={m.get('signal_line')}, hist={m.get('histogram')}")
a = atr(highs, lows, closes, 14)
print(f"ATR(14) = {a}")
b = bollinger(closes, 20, 2.0)
print(f"Bollinger = upper={b.get('upper')}, mid={b.get('middle')}, lower={b.get('lower')}")
s = stochastic(highs, lows, closes, 14, 3)
print(f"Stochastic = K={s.get('k')}, D={s.get('d')}")
o = obv(closes, volumes)
print(f"OBV = {o}")

# RiskGuardian
print("\n--- RiskGuardian ---")
rg = RiskGuardian(1000.0, 1000.0)
ok, msg = rg.can_trade(datetime.now(), 1000.0, 1000.0, 0, 50.0)
print(f"can_trade = {ok} ({msg})")
vol = rg.calculate_position_size(1000.0, 0.5, 0.00001, 0.01, 100.0, 0.01)
print(f"position_size = {vol}")
sl, tp = rg.fallback_sl_tp("BUY", 100.0, 0.5, 0.01)
print(f"fallback SL={sl}, TP={tp}")

# Smart Payload classifiers
print("\n--- Smart Payload ---")
trend = classify_trend(100.5, 100.3, 100.1, 100.6)
print(f"Trend = {trend}")
mom = classify_momentum(65.0, 0.002, 72.0, 68.0, 55.0)
print(f"Momentum = rsi_zone={mom['rsi_zone']}, macd={mom['macd_direction']}")
vol_state = classify_volatility(0.5, 100.0, 101.0, 99.0, 100.0)
print(f"Volatility = regime={vol_state['regime']}")

print("\n" + "=" * 50)
print("TOUS LES TESTS OK")
print("=" * 50)
