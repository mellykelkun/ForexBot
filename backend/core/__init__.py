"""Core subpackage (compat wrappers)."""

from .engine import (
    AdvancedMT5Engine,
    initialize_engine,
    OrderType,
    OrderStatus,
    TradeResult,
    PositionInfo,
)

__all__ = [
    "AdvancedMT5Engine",
    "initialize_engine",
    "OrderType",
    "OrderStatus",
    "TradeResult",
    "PositionInfo",
]
