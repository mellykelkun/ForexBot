"""Core subpackage — moteur, indicateurs, risque, payload, monitoring."""

from .engine import (
    AdvancedMT5Engine,
    initialize_engine,
    OrderType,
    OrderStatus,
    TradeResult,
    PositionInfo,
)

# Nouveaux modules
from . import indicators
from .risk_guardian import RiskGuardian
from .smart_payload import build_smart_payload
from .position_monitor import PositionMonitor

__all__ = [
    "AdvancedMT5Engine",
    "initialize_engine",
    "OrderType",
    "OrderStatus",
    "TradeResult",
    "PositionInfo",
    "indicators",
    "RiskGuardian",
    "build_smart_payload",
    "PositionMonitor",
]
