"""Config subpackage (compat wrappers)."""

from . import config_micro_scalping_pro as _cfg

# Exports explicites (évite les limites de __all__ dans le module source)
Config = _cfg.Config
config = getattr(_cfg, "config", None)
config_manager = _cfg.config_manager

INTELLIGENT_EXIT_CONFIG = _cfg.INTELLIGENT_EXIT_CONFIG
GUARDIAN_SYSTEM_CONFIG = _cfg.GUARDIAN_SYSTEM_CONFIG

# Exposer aussi les paramètres courants utilisés ailleurs
MICRO_SCALPING_CONFIG = _cfg.MICRO_SCALPING_CONFIG
VOLATILITE_CONFIG = _cfg.VOLATILITE_CONFIG
INDICATEURS_CONFIG = _cfg.INDICATEURS_CONFIG
AI_ADAPTIVE_CONFIG = _cfg.AI_ADAPTIVE_CONFIG
SECURITY_CONFIG = _cfg.SECURITY_CONFIG
SYMBOLS_CONFIG = _cfg.SYMBOLS_CONFIG
TIMEFRAMES_CONFIG = _cfg.TIMEFRAMES_CONFIG
TRADING_SESSIONS = _cfg.TRADING_SESSIONS

__all__ = [
	"Config",
	"config",
	"config_manager",
	"INTELLIGENT_EXIT_CONFIG",
	"GUARDIAN_SYSTEM_CONFIG",
	"MICRO_SCALPING_CONFIG",
	"VOLATILITE_CONFIG",
	"INDICATEURS_CONFIG",
	"AI_ADAPTIVE_CONFIG",
	"SECURITY_CONFIG",
	"SYMBOLS_CONFIG",
	"TIMEFRAMES_CONFIG",
	"TRADING_SESSIONS",
]
