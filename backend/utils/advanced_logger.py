# utils/advanced_logger.py
"""
LOGGER AVANCÉ PROFESSIONNEL - BTCUSD MICRO SCALPER V8
Système de logging avec rotation, compression et analyse
"""

import logging
import logging.handlers
import os
import sys
import gzip
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading
from pathlib import Path
import colorama
from colorama import Fore, Style

# Initialisation colorama pour Windows
colorama.init()

class LogLevel:
    """Niveaux de log personnalisés"""
    TRACE = 5
    MICRO = 15
    TRADING = 25

# Ajout des niveaux personnalisés
logging.addLevelName(LogLevel.TRACE, "TRACE")
logging.addLevelName(LogLevel.MICRO, "MICRO")
logging.addLevelName(LogLevel.TRADING, "TRADING")

class ColorFormatter(logging.Formatter):
    """Formateur avec couleurs pour la console"""
    
    # Couleurs par niveau
    COLORS = {
        'TRACE': Fore.CYAN,
        'DEBUG': Fore.BLUE,
        'MICRO': Fore.GREEN,
        'TRADING': Fore.MAGENTA,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        """Format le message avec couleurs"""
        # Sauvegarde la couleur originale
        original_color = self.COLORS.get(record.levelname, Fore.WHITE)
        
        # Application de la couleur
        record.levelname = f"{original_color}{record.levelname}{Style.RESET_ALL}"
        record.msg = f"{original_color}{record.msg}{Style.RESET_ALL}"
        
        return super().format(record)

class AdvancedLogger:
    """
    Logger avancé avec fonctionnalités professionnelles:
    - Rotation automatique des fichiers
    - Compression des anciens logs
    - Logging structuré (JSON)
    - Métriques de performance
    - Alertes intelligentes
    """
    
    def __init__(self, 
                 name: str = "BTCUSD_Micro_Scalper",
                 log_dir: str = "logs",
                 max_file_size: int = 50 * 1024 * 1024,  # 50 MB
                 backup_count: int = 10,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_json: bool = True):
        
        self.name = name
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_json = enable_json
        
        # Création du répertoire de logs
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuration du logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Éviter la propagation pour éviter les doublons
        self.logger.propagate = False
        
        # Nettoyage des handlers existants
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Configuration des handlers
        if enable_console:
            self.setup_console_handler()
        
        if enable_file:
            self.setup_file_handlers()
        
        if enable_json:
            self.setup_json_handler()
        
        # Métriques de logging
        self.metrics = {
            'total_logs': 0,
            'logs_by_level': {},
            'last_alert': None,
            'start_time': datetime.now()
        }
        
        # Thread de maintenance
        self.maintenance_thread = threading.Thread(target=self._maintenance_worker, daemon=True)
        self.maintenance_thread.start()
        
        # Premier log
        self.info(f"🚀 Logger avancé initialisé: {name}")
    
    def setup_console_handler(self):
        """Configure le handler console avec couleurs"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        formatter = ColorFormatter(
            fmt='%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def setup_file_handlers(self):
        """Configure les handlers fichiers avec rotation"""
        
        # Handler pour tous les logs
        main_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'trading_system.log',
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        
        main_formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        main_handler.setFormatter(main_formatter)
        self.logger.addHandler(main_handler)
        
        # Handler dédié aux logs de trading
        trading_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'trading_operations.log',
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        trading_handler.setLevel(LogLevel.TRADING)
        
        trading_formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        trading_handler.setFormatter(trading_formatter)
        self.logger.addHandler(trading_handler)
        
        # Handler dédié aux micro-opérations
        micro_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'micro_trades.log',
            maxBytes=self.max_file_size,
            backupCount=self.backup_count * 2,  # Plus de backups pour les trades
            encoding='utf-8'
        )
        micro_handler.setLevel(LogLevel.MICRO)
        
        micro_formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        micro_handler.setFormatter(micro_formatter)
        self.logger.addHandler(micro_handler)
    
    def setup_json_handler(self):
        """Configure le handler JSON pour l'analyse structurée"""
        json_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / 'structured_logs.json',
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.INFO)
        
        # Formatter spécial pour JSON
        json_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(json_handler)
    
    def _update_metrics(self, level: str):
        """Met à jour les métriques de logging"""
        self.metrics['total_logs'] += 1
        self.metrics['logs_by_level'][level] = self.metrics['logs_by_level'].get(level, 0) + 1
    
    def _maintenance_worker(self):
        """Tâche de maintenance en arrière-plan"""
        while True:
            try:
                self._compress_old_logs()
                self._cleanup_old_logs()
                threading.Event().wait(3600)  # Toutes les heures
            except Exception as e:
                self.error(f"Erreur maintenance logs: {e}")
    
    def _compress_old_logs(self):
        """Compresse les anciens fichiers de log"""
        try:
            cutoff_date = datetime.now() - timedelta(days=1)
            
            for log_file in self.log_dir.glob("*.log.*"):  # Fichiers de backup
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    compressed_file = log_file.with_suffix('.log.gz')
                    
                    if not compressed_file.exists():
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_file, 'wb') as f_out:
                                f_out.writelines(f_in)
                        
                        # Supprime le fichier original après compression
                        log_file.unlink()
                        self.trace(f"Fichier compressé: {log_file.name}")
                        
        except Exception as e:
            self.error(f"Erreur compression logs: {e}")
    
    def _cleanup_old_logs(self):
        """Nettoie les anciens fichiers compressés"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)  # Garder 30 jours
            
            for compressed_file in self.log_dir.glob("*.gz"):
                if compressed_file.stat().st_mtime < cutoff_date.timestamp():
                    compressed_file.unlink()
                    self.trace(f"Fichier supprimé: {compressed_file.name}")
                    
        except Exception as e:
            self.error(f"Erreur nettoyage logs: {e}")
    
    # Méthodes de logging personnalisées
    def trace(self, message: str, **kwargs):
        """Log niveau TRACE (très détaillé)"""
        self._update_metrics('TRACE')
        self.logger.log(LogLevel.TRACE, message, extra=kwargs)
    
    def micro(self, message: str, **kwargs):
        """Log niveau MICRO (opérations micro-scalping)"""
        self._update_metrics('MICRO')
        self.logger.log(LogLevel.MICRO, message, extra=kwargs)
    
    def trading(self, message: str, **kwargs):
        """Log niveau TRADING (opérations de trading)"""
        self._update_metrics('TRADING')
        self.logger.log(LogLevel.TRADING, message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log niveau DEBUG"""
        self._update_metrics('DEBUG')
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log niveau INFO"""
        self._update_metrics('INFO')
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log niveau WARNING"""
        self._update_metrics('WARNING')
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log niveau ERROR"""
        self._update_metrics('ERROR')
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log niveau CRITICAL"""
        self._update_metrics('CRITICAL')
        self.logger.critical(message, extra=kwargs)
    
    def trade_signal(self, 
                    symbol: str, 
                    direction: str, 
                    price: float, 
                    volume: float,
                    confidence: float,
                    pattern: str = "",
                    rsi: float = None,
                    volatility: float = None):
        """Log structuré pour les signaux de trading"""
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'TRADE_SIGNAL',
            'symbol': symbol,
            'direction': direction,
            'price': price,
            'volume': volume,
            'confidence': confidence,
            'pattern': pattern,
            'rsi': rsi,
            'volatility': volatility
        }
        
        self.trading(f"SIGNAL | {symbol} {direction} @ {price} | "
                    f"Conf: {confidence:.2f} | Vol: {volume} | Pattern: {pattern}")
        
        # Log JSON structuré
        if self.enable_json:
            self.info("Trade signal generated", extra={'trade_data': trade_data})
    
    def trade_execution(self,
                       ticket: int,
                       symbol: str,
                       direction: str,
                       price: float,
                       volume: float,
                       sl: float,
                       tp: float,
                       profit: float = 0.0,
                       status: str = "EXECUTED"):
        """Log structuré pour l'exécution des trades"""
        execution_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'TRADE_EXECUTION',
            'ticket': ticket,
            'symbol': symbol,
            'direction': direction,
            'price': price,
            'volume': volume,
            'sl': sl,
            'tp': tp,
            'profit': profit,
            'status': status
        }
        
        # Log détaillé pour les micro-trades
        self.micro(f"EXEC | {symbol} {direction} | Ticket: {ticket} | "
                  f"Price: {price} | Vol: {volume} | SL: {sl} | TP: {tp}")
        
        # Log JSON structuré
        if self.enable_json:
            self.info("Trade executed", extra={'execution_data': execution_data})
    
    def performance_metrics(self, metrics: Dict[str, Any]):
        """Log des métriques de performance"""
        metrics_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'PERFORMANCE_METRICS',
            'metrics': metrics
        }
        
        self.info("Performance metrics updated", extra={'performance_data': metrics_data})
    
    def system_alert(self, 
                    alert_type: str, 
                    message: str, 
                    severity: str = "MEDIUM",
                    component: str = "SYSTEM"):
        """Log d'alerte système"""
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'SYSTEM_ALERT',
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'component': component
        }
        
        # Mise à jour métriques alertes
        self.metrics['last_alert'] = datetime.now()
        
        # Log selon la sévérité
        if severity == "LOW":
            self.warning(f"ALERT [{component}] {alert_type}: {message}")
        elif severity == "MEDIUM":
            self.error(f"ALERT [{component}] {alert_type}: {message}")
        else:  # HIGH
            self.critical(f"ALERT [{component}] {alert_type}: {message}")
        
        # Log JSON structuré
        if self.enable_json:
            self.info("System alert triggered", extra={'alert_data': alert_data})
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de logging"""
        uptime = datetime.now() - self.metrics['start_time']
        
        return {
            'name': self.name,
            'uptime': str(uptime),
            'total_logs': self.metrics['total_logs'],
            'logs_by_level': self.metrics['logs_by_level'],
            'last_alert': self.metrics['last_alert'],
            'log_directory': str(self.log_dir.absolute())
        }

class JsonFormatter(logging.Formatter):
    """Formateur JSON pour le logging structuré"""
    
    def format(self, record):
        """Format le message en JSON"""
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Ajout des données extra
        if hasattr(record, 'trade_data'):
            log_entry['trade_data'] = record.trade_data
        if hasattr(record, 'execution_data'):
            log_entry['execution_data'] = record.execution_data
        if hasattr(record, 'performance_data'):
            log_entry['performance_data'] = record.performance_data
        if hasattr(record, 'alert_data'):
            log_entry['alert_data'] = record.alert_data
        
        # Gestion des exceptions
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

# Instance globale pour faciliter l'utilisation
global_logger = None

def setup_global_logger(**kwargs) -> AdvancedLogger:
    """Configure le logger global"""
    global global_logger
    global_logger = AdvancedLogger(**kwargs)
    return global_logger

def get_logger() -> AdvancedLogger:
    """Retourne le logger global"""
    global global_logger
    if global_logger is None:
        global_logger = AdvancedLogger()
    return global_logger

# Fonctions de convenance
def trace(msg: str, **kwargs):
    get_logger().trace(msg, **kwargs)

def micro(msg: str, **kwargs):
    get_logger().micro(msg, **kwargs)

def trading(msg: str, **kwargs):
    get_logger().trading(msg, **kwargs)

def debug(msg: str, **kwargs):
    get_logger().debug(msg, **kwargs)

def info(msg: str, **kwargs):
    get_logger().info(msg, **kwargs)

def warning(msg: str, **kwargs):
    get_logger().warning(msg, **kwargs)

def error(msg: str, **kwargs):
    get_logger().error(msg, **kwargs)

def critical(msg: str, **kwargs):
    get_logger().critical(msg, **kwargs)

def trade_signal(symbol: str, direction: str, price: float, volume: float, 
                confidence: float, **kwargs):
    get_logger().trade_signal(symbol, direction, price, volume, confidence, **kwargs)

def trade_execution(ticket: int, symbol: str, direction: str, price: float, 
                   volume: float, sl: float, tp: float, **kwargs):
    get_logger().trade_execution(ticket, symbol, direction, price, volume, sl, tp, **kwargs)

def system_alert(alert_type: str, message: str, **kwargs):
    get_logger().system_alert(alert_type, message, **kwargs)

if __name__ == "__main__":
    # Test du logger
    logger = AdvancedLogger("TestLogger")
    
    logger.trace("Message TRACE très détaillé")
    logger.debug("Message DEBUG")
    logger.micro("Message MICRO pour scalping")
    logger.trading("Message TRADING pour opérations")
    logger.info("Message INFO standard")
    logger.warning("Message WARNING d'avertissement")
    logger.error("Message ERROR d'erreur")
    logger.critical("Message CRITIQUE")
    
    # Test des fonctions spécialisées
    logger.trade_signal("BTCUSD", "BUY", 45000.0, 0.01, 0.85, "ENGLOBANT_HAUSSIER", 65.5, 0.023)
    logger.trade_execution(123456, "BTCUSD", "BUY", 45000.0, 0.01, 44950.0, 45050.0)
    logger.system_alert("CONNECTION_LOST", "Perte connexion MT5", "HIGH", "MT5_ENGINE")
    
    # Affichage des métriques
    print("\n[data] Métriques du logger:")
    print(json.dumps(logger.get_metrics(), indent=2, default=str))