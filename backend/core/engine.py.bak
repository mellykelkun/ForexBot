# core/engine.py
"""
MOTEUR CENTRAL PROFESSIONNEL - BTCUSD MICRO SCALPER V8
Gestion MT5 avancée avec reconnection intelligente
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import threading
from dataclasses import dataclass
from enum import Enum

class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"

class OrderStatus(Enum):
    PLACED = "PLACED"
    EXECUTED = "EXECUTED"
    PARTIAL = "PARTIAL"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

@dataclass
class TradeResult:
    """Résultat d'une opération de trading"""
    success: bool
    ticket: Optional[int] = None
    price: Optional[float] = None
    volume: Optional[float] = None
    profit: Optional[float] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

@dataclass
class PositionInfo:
    """Informations sur une position"""
    ticket: int
    symbol: str
    type: OrderType
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    swap: float
    commission: float
    open_time: datetime
    magic: int
    comment: str

class AdvancedMT5Engine:
    """Moteur MT5 avancé avec gestion robuste"""
    
    def __init__(self, 
                 account: int,
                 password: str,
                 server: str,
                 symbol: str = "BTCUSD",
                 magic_number: int = 88880001,
                 max_reconnect_attempts: int = 5,
                 reconnect_delay: int = 5):
        
        self.account = account
        self.password = password
        self.server = server
        self.symbol = symbol
        self.magic_number = magic_number
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        
        self.connected = False
        self.last_connection_check = None
        self.connection_attempts = 0
        self.reconnect_lock = threading.Lock()
        
        # Métriques de performance
        self.performance_metrics = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'avg_execution_time': 0,
            'last_order_time': None,
            'connection_uptime': None
        }
        
        # Configuration logging
        self.setup_logging()
        
        # Initialisation
        self.initialize_mt5()
        
    def setup_logging(self):
        """Configuration du logging avancé"""
        self.logger = logging.getLogger('MT5Engine')
        if not self.logger.handlers:
            handler = logging.FileHandler('mt5_engine.log', encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def initialize_mt5(self) -> bool:
        """Initialise et connecte à MT5"""
        try:
            if not mt5.initialize():
                self.logger.error(f"❌ Échec initialisation MT5: {mt5.last_error()}")
                return False
            
            # Configuration terminal
            mt5.set_timeout(5000)  # 5 secondes timeout
            
            # Connexion au compte
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.info(f"🔗 Connexion au compte {self.account}...")
                
                if not mt5.login(self.account, password=self.password, server=self.server):
                    self.logger.error(f"❌ Échec connexion MT5: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
            
            self.connected = True
            self.connection_attempts = 0
            self.performance_metrics['connection_uptime'] = datetime.now()
            
            account_info = mt5.account_info()
            self.logger.info(f"✅ Connecté avec succès au compte {account_info.login}")
            self.logger.info(f"💰 Broker: {account_info.server} | Balance: {account_info.balance}")
            self.logger.info(f"💼 Devise: {account_info.currency} | Levier: 1:{account_info.leverage}")
            
            # Vérification du symbole
            if not self.verify_symbol():
                self.logger.error(f"❌ Symbole {self.symbol} non disponible")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"💥 Erreur initialisation MT5: {e}")
            return False
    
    def verify_symbol(self) -> bool:
        """Vérifie la disponibilité du symbole"""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                self.logger.error(f"❌ Symbole {self.symbol} non trouvé")
                return False
            
            if not symbol_info.visible:
                self.logger.info(f"🔧 Activation du symbole {self.symbol}...")
                if not mt5.symbol_select(self.symbol, True):
                    self.logger.error(f"❌ Impossible d'activer {self.symbol}")
                    return False
            
            self.logger.info(f"✅ Symbole {self.symbol} disponible:")
            self.logger.info(f"   📊 Spread: {symbol_info.spread} | Digits: {symbol_info.digits}")
            self.logger.info(f"   📈 Volume min: {symbol_info.volume_min} | Volume max: {symbol_info.volume_max}")
            self.logger.info(f"   💰 Tick size: {symbol_info.trade_tick_size} | Tick value: {symbol_info.trade_tick_value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erreur vérification symbole: {e}")
            return False
    
    def ensure_connection(self) -> bool:
        """Vérifie et maintient la connexion"""
        with self.reconnect_lock:
            if self.connected:
                # Vérification rapide
                if self.last_connection_check and (datetime.now() - self.last_connection_check).seconds < 30:
                    return True
                
                try:
                    account_info = mt5.account_info()
                    if account_info is not None:
                        self.last_connection_check = datetime.now()
                        return True
                except:
                    pass
            
            # Reconnexion nécessaire
            self.connected = False
            self.logger.warning("🔌 Reconnexion à MT5...")
            
            for attempt in range(self.max_reconnect_attempts):
                try:
                    mt5.shutdown()
                    time.sleep(self.reconnect_delay)
                    
                    if self.initialize_mt5():
                        self.logger.info("✅ Reconnexion réussie")
                        return True
                    
                except Exception as e:
                    self.logger.error(f"❌ Tentative {attempt + 1} échouée: {e}")
                    time.sleep(self.reconnect_delay * (attempt + 1))
            
            self.logger.error("💥 Échec reconnexion après tous les essais")
            return False
    
    def get_market_data(self) -> Optional[Dict[str, Any]]:
        """Récupère les données marché complètes"""
        try:
            if not self.ensure_connection():
                return None
            
            # Prix actuel
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                self.logger.error(f"❌ Impossible de récupérer le tick pour {self.symbol}")
                return None
            
            # Données symboles
            symbol_info = mt5.symbol_info(self.symbol)
            
            # RSI et indicateurs (simulés pour l'exemple)
            rsi = self.calculate_rsi()
            volatility = self.calculate_volatility()
            
            return {
                'symbol': self.symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': (tick.ask - tick.bid) * (10 ** symbol_info.digits),
                'spread_pips': (tick.ask - tick.bid) / symbol_info.point,
                'volume': tick.volume,
                'time': tick.time,
                'rsi': rsi,
                'volatility': volatility,
                'digits': symbol_info.digits,
                'point': symbol_info.point,
                'tick_size': symbol_info.trade_tick_size,
                'tick_value': symbol_info.trade_tick_value
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur données marché: {e}")
            return None
    
    def calculate_rsi(self, period: int = 14) -> float:
        """Calcule le RSI (simulé pour l'exemple)"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M5, 0, period + 1)
            if rates is None or len(rates) < period + 1:
                return 50.0
            
            closes = [rate['close'] for rate in rates]
            deltas = np.diff(closes)
            
            gains = [delta for delta in deltas if delta > 0]
            losses = [-delta for delta in deltas if delta < 0]
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 50.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul RSI: {e}")
            return 50.0
    
    def calculate_volatility(self, period: int = 20) -> float:
        """Calcule la volatilité (ATR simulé)"""
        try:
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M5, 0, period)
            if rates is None or len(rates) < period:
                return 0.01
            
            highs = [rate['high'] for rate in rates]
            lows = [rate['low'] for rate in rates]
            
            tr_values = []
            for i in range(1, len(rates)):
                high_low = highs[i] - lows[i]
                high_close = abs(highs[i] - rates[i-1]['close'])
                low_close = abs(lows[i] - rates[i-1]['close'])
                true_range = max(high_low, high_close, low_close)
                tr_values.append(true_range)
            
            atr = np.mean(tr_values) if tr_values else 0
            return round(atr, 5)
            
        except Exception as e:
            self.logger.error(f"❌ Erreur calcul volatilité: {e}")
            return 0.01
    
    def place_order(self, 
                   order_type: OrderType,
                   volume: float,
                   sl_price: float = 0.0,
                   tp_price: float = 0.0,
                   deviation: int = 5,
                   comment: str = "") -> TradeResult:
        """Place un ordre de trading"""
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return TradeResult(
                    success=False,
                    error_message="Non connecté à MT5",
                    execution_time=time.time() - start_time
                )
            
            # Vérification volume
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                return TradeResult(
                    success=False,
                    error_message=f"Symbole {self.symbol} non disponible",
                    execution_time=time.time() - start_time
                )
            
            volume = max(symbol_info.volume_min, min(volume, symbol_info.volume_max))
            volume = round(volume, 2)
            
            # Préparation de la requête
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": volume,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": deviation,
                "magic": self.magic_number,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Détermination du type d'ordre
            if order_type == OrderType.BUY:
                request["type"] = mt5.ORDER_TYPE_BUY
                request["price"] = mt5.symbol_info_tick(self.symbol).ask
            elif order_type == OrderType.SELL:
                request["type"] = mt5.ORDER_TYPE_SELL
                request["price"] = mt5.symbol_info_tick(self.symbol).bid
            else:
                return TradeResult(
                    success=False,
                    error_message=f"Type d'ordre non supporté: {order_type}",
                    execution_time=time.time() - start_time
                )
            
            # Envoi de l'ordre
            result = mt5.order_send(request)
            execution_time = time.time() - start_time
            
            if result is None:
                return TradeResult(
                    success=False,
                    error_message="Aucune réponse de MT5",
                    execution_time=execution_time
                )
            
            # Analyse du résultat
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"❌ Erreur ordre: {result.retcode} - {self.get_error_description(result.retcode)}")
                
                self.performance_metrics['failed_orders'] += 1
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=self.get_error_description(result.retcode),
                    execution_time=execution_time
                )
            
            # Succès
            self.performance_metrics['total_orders'] += 1
            self.performance_metrics['successful_orders'] += 1
            self.performance_metrics['last_order_time'] = datetime.now()
            
            # Mise à jour temps d'exécution moyen
            total_time = self.performance_metrics['avg_execution_time'] * (self.performance_metrics['successful_orders'] - 1)
            self.performance_metrics['avg_execution_time'] = (total_time + execution_time) / self.performance_metrics['successful_orders']
            
            self.logger.info(f"✅ Ordre exécuté: {order_type.value} {volume} {self.symbol} "
                           f"| Ticket: {result.order} | Prix: {result.price} | Temps: {execution_time:.3f}s")
            
            return TradeResult(
                success=True,
                ticket=result.order,
                price=result.price,
                volume=volume,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"💥 Erreur placement ordre: {e}")
            
            self.performance_metrics['failed_orders'] += 1
            return TradeResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def close_position(self, ticket: int, deviation: int = 5) -> TradeResult:
        """Ferme une position"""
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return TradeResult(
                    success=False,
                    error_message="Non connecté à MT5",
                    execution_time=time.time() - start_time
                )
            
            # Récupération de la position
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return TradeResult(
                    success=False,
                    error_message=f"Position {ticket} non trouvée",
                    execution_time=time.time() - start_time
                )
            
            position = positions[0]
            
            # Préparation de la requête de fermeture
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": position.symbol,
                "volume": position.volume,
                "deviation": deviation,
                "magic": self.magic_number,
                "comment": f"CLOSE_{position.comment}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Détermination du type pour fermeture
            if position.type == mt5.ORDER_TYPE_BUY:
                request["type"] = mt5.ORDER_TYPE_SELL
                request["price"] = mt5.symbol_info_tick(position.symbol).bid
            else:
                request["type"] = mt5.ORDER_TYPE_BUY
                request["price"] = mt5.symbol_info_tick(position.symbol).ask
            
            # Envoi de la requête
            result = mt5.order_send(request)
            execution_time = time.time() - start_time
            
            if result is None:
                return TradeResult(
                    success=False,
                    error_message="Aucune réponse de MT5 pour fermeture",
                    execution_time=execution_time
                )
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"❌ Erreur fermeture: {result.retcode}")
                return TradeResult(
                    success=False,
                    error_code=result.retcode,
                    error_message=self.get_error_description(result.retcode),
                    execution_time=execution_time
                )
            
            # Calcul du profit
            profit = position.profit + position.swap + position.commission
            
            self.logger.info(f"✅ Position fermée: {ticket} | Profit: {profit:.2f} | "
                           f"Durée: {datetime.now() - position.time_open}")
            
            return TradeResult(
                success=True,
                ticket=result.order,
                price=result.price,
                volume=position.volume,
                profit=profit,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"💥 Erreur fermeture position: {e}")
            return TradeResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time
            )
    
    def get_open_positions(self, symbol: str = None) -> List[PositionInfo]:
        """Récupère les positions ouvertes"""
        try:
            if not self.ensure_connection():
                return []
            
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            result = []
            for position in positions:
                if position.magic == self.magic_number:
                    # Conversion du type MT5 vers notre enum
                    if position.type == mt5.ORDER_TYPE_BUY:
                        order_type = OrderType.BUY
                    else:
                        order_type = OrderType.SELL
                    
                    # Prix actuel
                    tick = mt5.symbol_info_tick(position.symbol)
                    current_price = tick.ask if position.type == mt5.ORDER_TYPE_BUY else tick.bid
                    
                    result.append(PositionInfo(
                        ticket=position.ticket,
                        symbol=position.symbol,
                        type=order_type,
                        volume=position.volume,
                        open_price=position.price_open,
                        current_price=current_price,
                        sl=position.sl,
                        tp=position.tp,
                        profit=position.profit,
                        swap=position.swap,
                        commission=position.commission,
                        open_time=position.time_open,
                        magic=position.magic,
                        comment=position.comment
                    ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erreur récupération positions: {e}")
            return []
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Récupère les informations du compte"""
        try:
            if not self.ensure_connection():
                return None
            
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return {
                'login': account_info.login,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'leverage': account_info.leverage,
                'currency': account_info.currency,
                'server': account_info.server,
                'profit': account_info.profit,
                'margin_level': account_info.margin_level
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erreur informations compte: {e}")
            return None
    
    def get_error_description(self, error_code: int) -> str:
        """Retourne la description d'une erreur MT5"""
        error_descriptions = {
            10004: "Requête échangée",
            10006: "Requête en cours de traitement",
            10007: "Ordre exécuté",
            10008: "Ordre annulé",
            10009: "Ordre modifié",
            10010: "Ordre activé",
            10011: "Ordre expiré",
            10012: "Ordre partiel",
            10013: "Erreur de traitement",
            10014: "Requête invalide",
            10015: "Version invalide",
            10016: "Clé invalide",
            10017: "Compte invalide",
            10018: "Symbole invalide",
            10019: "Volume invalide",
            10020: "Prix invalide",
            10021: "Stop invalide",
            10022: "Take invalide",
            10023: "Commentaire invalide",
            10024: "Position invalide",
            10025: "Ordre invalide",
            10026: "Deviation invalide",
            10027: "Type de trading invalide",
            10028: "Type d'ordre invalide",
            10029: "Type de remplissage invalide",
            10030: "Type de temps invalide",
            10031: "Type de prix invalide",
            10032: "Client invalide",
            10033: "Overbuy limite dépassée",
            10034: "Limite de marge dépassée",
            10035: "Limite de position dépassée",
            10036: "Limite d'ordre dépassée",
            10037: "Limite de volume dépassée",
            10038: "Non autorisé",
            10039: "Trop de requêtes",
            10040: "Changement non autorisé",
            10041: "Ordre verrouillé",
            10042: "Fonds insuffisants",
            10043: "Connexion marché fermée",
            10044: "Connexion marché indisponible",
            10045: "Requête timeout",
            10046: "Version obsolète",
            10047: "Ordre déjà en cours",
            10048: "Action non autorisée",
            10049: "Trading désactivé",
            10050: "Symbole désactivé",
            10051: "Courtier occupé",
            10052: "Requête rejetée",
            10053: "Limite de requête dépassée",
            10054: "Limite d'exécution dépassée",
            10055: "Limite d'annulation dépassée",
            10056: "Limite de modification dépassée",
            10057: "Session de trading fermée",
            10058: "Marché fermé",
            10059: "Instrument fermé",
            10060: "Mode hedging interdit",
            10061: "Limite de profit/stop dépassée",
            10062: "Limite de prix dépassée",
            10063: "Limite de volume dépassée",
            10064: "Limite de position dépassée",
            10065: "Limite d'ordre dépassée",
            10066: "Limite de marge dépassée",
            10067: "Limite de perte dépassée",
            10068: "Limite de profit dépassée",
            10069: "Limite de volume dépassée",
            10070: "Limite de compte dépassée",
            10071: "Limite de client dépassée",
            10072: "Limite d'actif dépassée",
            10073: "Limite de stratégie dépassée",
            10074: "Limite de sous-compte dépassée",
            10075: "Limite de groupe dépassée",
            10076: "Limite de sécurité dépassée",
            10077: "Limite de courtier dépassée",
            10078: "Limite de symbole dépassée",
            10079: "Limite de session dépassée",
            10080: "Limite de système dépassée",
            10081: "Limite de temps dépassée",
            10082: "Limite de risque dépassée",
            10083: "Limite de capital dépassée",
            10084: "Limite de drawdown dépassée",
            10085: "Limite de marge initiale dépassée",
            10086: "Limite de maintenance dépassée",
            10087: "Limite de liquidité dépassée",
            10088: "Limite de volatilité dépassée",
            10089: "Limite de corrélation dépassée",
            10090: "Limite de diversification dépassée",
            10091: "Limite de concentration dépassée",
            10092: "Limite de levier dépassée",
            10093: "Limite de volume dépassée",
            10094: "Limite de position dépassée",
            10095: "Limite d'ordre dépassée",
            10096: "Limite de trade dépassée",
            10097: "Limite de profit dépassée",
            10098: "Limite de perte dépassée",
            10099: "Limite de marge dépassée",
            10100: "Limite de compte dépassée",
            10101: "Limite de client dépassée",
            10102: "Limite d'actif dépassée",
            10103: "Limite de stratégie dépassée",
            10104: "Limite de sous-compte dépassée",
            10105: "Limite de groupe dépassée",
            10106: "Limite de sécurité dépassée",
            10107: "Limite de courtier dépassée",
            10108: "Limite de symbole dépassée",
            10109: "Limite de session dépassée",
            10110: "Limite de système dépassée",
            10111: "Limite de temps dépassée",
            10112: "Limite de risque dépassée",
            10113: "Limite de capital dépassée",
            10114: "Limite de drawdown dépassée",
            10115: "Limite de marge initiale dépassée",
            10116: "Limite de maintenance dépassée",
            10117: "Limite de liquidité dépassée",
            10118: "Limite de volatilité dépassée",
            10119: "Limite de corrélation dépassée",
            10120: "Limite de diversification dépassée",
            10121: "Limite de concentration dépassée",
            10122: "Limite de levier dépassée"
        }
        
        return error_descriptions.get(error_code, f"Erreur inconnue: {error_code}")
    
    def shutdown(self):
        """Arrêt gracieux du moteur"""
        try:
            if self.connected:
                mt5.shutdown()
                self.connected = False
                self.logger.info("✅ Moteur MT5 arrêté")
        except Exception as e:
            self.logger.error(f"❌ Erreur arrêt moteur: {e}")

# Instance globale pour faciliter l'utilisation
mt5_engine = None

def initialize_engine(account: int, password: str, server: str, symbol: str = "BTCUSD") -> AdvancedMT5Engine:
    """Initialise le moteur MT5 global"""
    global mt5_engine
    mt5_engine = AdvancedMT5Engine(account, password, server, symbol)
    return mt5_engine

def get_engine() -> AdvancedMT5Engine:
    """Retourne l'instance du moteur"""
    global mt5_engine
    if mt5_engine is None:
        raise RuntimeError("Moteur MT5 non initialisé")
    return mt5_engine