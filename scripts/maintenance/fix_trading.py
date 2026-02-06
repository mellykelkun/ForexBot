# CORRECTIONS IMMÉDIATES POUR ACTIVER LE TRADING RÉEL

# 1. Modifiez le seuil de confiance AI
def get_ai_signal_fixed(self, symbol: str, tick_data: Dict) -> Optional[TradingSignal]:
    try:
        # ... code existant ...
        
        confidence_threshold = 0.4  # ← BAISSÉ de 0.6 à 0.4
        
        if ai_signal.confidence >= confidence_threshold:
            logging.info(f"🎯 Signal AI reçu: {ai_signal.direction.value} | Confiance: {ai_signal.confidence:.1%}")
            return ai_signal
        
        return None
        
    except Exception as e:
        logging.error(f"❌ Erreur récupération signal AI: {e}")
        return None

# 2. Augmentez les limites de spread
def verifier_spread_acceptable_multi_fixed(self, symbol: str, tick_data: Dict) -> bool:
    if not tick_data:
        return False

    spread_actuel = tick_data['spread']
    
    # Limites plus réalistes pour BTCUSD
    if spread_actuel > 200.0:  # 200 points max = 20 pips
        logging.warning(f"🛑 {symbol} SPREAD TROP ÉLEVÉ: {spread_actuel:.2f} points")
        return False
    elif spread_actuel > 100.0:  # 100-200 points - Warning mais accepté
        logging.warning(f"⚠️ {symbol} Spread élevé: {spread_actuel:.2f} points")
        return True  # ← IMPORTANT: retourne True même si élevé
    
    return True

# 3. Activez le logging des décisions
def analyser_symbol_debug(self, symbol: str):
    """Version debug de analyser_symbol"""
    try:
        print(f"🔍 ANALYSE {symbol} en cours...")
        
        tick_data = self.get_symbol_tick_data(symbol)
        if not tick_data:
            print(f"❌ {symbol}: Données tick non disponibles")
            return None
            
        spread = tick_data['spread']
        print(f"📊 {symbol}: Spread = {spread:.2f} points")
        
        # Test acceptation spread
        spread_ok = self.verifier_spread_acceptable_multi_fixed(symbol, tick_data)
        print(f"✅ {symbol}: Spread acceptable = {spread_ok}")
        
        # ... reste de l'analyse ...
        
    except Exception as e:
        print(f"💥 Erreur analyse {symbol}: {e}")
        return None