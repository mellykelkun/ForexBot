"""Type stubs for MetaTrader5 package."""
from typing import Any, Optional, Tuple
import numpy as np
from numpy.typing import NDArray

# --- Timeframes ---
TIMEFRAME_M1: int
TIMEFRAME_M5: int
TIMEFRAME_M15: int
TIMEFRAME_M30: int
TIMEFRAME_H1: int
TIMEFRAME_H4: int
TIMEFRAME_D1: int
TIMEFRAME_W1: int
TIMEFRAME_MN1: int

# --- Trade actions ---
TRADE_ACTION_DEAL: int
TRADE_ACTION_SLTP: int
TRADE_ACTION_PENDING: int
TRADE_ACTION_MODIFY: int
TRADE_ACTION_REMOVE: int

# --- Order types ---
ORDER_TYPE_BUY: int
ORDER_TYPE_SELL: int
ORDER_TYPE_BUY_LIMIT: int
ORDER_TYPE_SELL_LIMIT: int
ORDER_TYPE_BUY_STOP: int
ORDER_TYPE_SELL_STOP: int

# --- Order filling ---
ORDER_FILLING_FOK: int
ORDER_FILLING_IOC: int
ORDER_FILLING_RETURN: int

# --- Order time ---
ORDER_TIME_GTC: int
ORDER_TIME_DAY: int
ORDER_TIME_SPECIFIED: int

# --- Retcodes ---
TRADE_RETCODE_DONE: int
TRADE_RETCODE_REQUOTE: int

# --- Info classes ---
class AccountInfo:
    login: int
    server: str
    balance: float
    equity: float
    margin: float
    margin_free: float
    profit: float
    currency: str
    leverage: int
    name: str

class SymbolInfo:
    name: str
    point: float
    digits: int
    spread: int
    trade_tick_value: float
    trade_tick_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    trade_stops_level: int
    trade_contract_size: float
    visible: bool
    path: str

class Tick:
    time: int
    bid: float
    ask: float
    last: float
    volume: int

class TerminalInfo:
    connected: bool
    path: str
    company: str
    name: str

class TradePosition:
    ticket: int
    time: int
    type: int
    symbol: str
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    swap: float
    comment: str
    magic: int
    point: float
    digits: int

class TradeDeal:
    ticket: int
    order: int
    time: int
    type: int
    entry: int
    reason: int
    symbol: str
    volume: float
    price: float
    profit: float
    swap: float
    commission: float
    comment: str
    magic: int

class OrderSendResult:
    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    comment: str

# --- Functions ---
def initialize(path: str = ..., login: int = ..., password: str = ..., server: str = ..., timeout: int = ..., portable: bool = ...) -> bool: ...
def shutdown() -> None: ...
def login(login: int, password: str = ..., server: str = ..., timeout: int = ...) -> bool: ...
def last_error() -> Tuple[int, str]: ...
def account_info() -> Optional[AccountInfo]: ...
def terminal_info() -> Optional[TerminalInfo]: ...
def symbol_info(symbol: str) -> Optional[SymbolInfo]: ...
def symbol_info_tick(symbol: str) -> Optional[Tick]: ...
def symbol_select(symbol: str, enable: bool = ...) -> bool: ...
def copy_rates_from_pos(symbol: str, timeframe: int, start_pos: int, count: int) -> Optional[NDArray[Any]]: ...
def order_send(request: dict[str, Any]) -> Optional[OrderSendResult]: ...
def positions_get(symbol: str = ..., group: str = ..., ticket: int = ...) -> Optional[Tuple[TradePosition, ...]]: ...
def history_deals_get(date_from: Any = ..., date_to: Any = ..., group: str = ...) -> Optional[Tuple[TradeDeal, ...]]: ...
