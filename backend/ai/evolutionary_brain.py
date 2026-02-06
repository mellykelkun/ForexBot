"""Module désactivé: ancienne logique IA supprimée (Groq uniquement via /api/decision)."""

raise RuntimeError("evolutionary_brain désactivé: utiliser /api/decision")

LEGACY_REMOVED = """

import numpy as np

def get_brain_instance():
    raise RuntimeError("evolutionary_brain désactivé: utiliser /api/decision")


class EvolutionaryBrain:
    def __init__(self):
        raise RuntimeError("EvolutionaryBrain désactivé: utiliser /api/decision")
        """Extrait les features pour la décision de sortie - VERSION CORRIGÉE"""
        try:
            # Calculer le PnL non réalisé en pourcentage
            entry_price = state.get('entry_price', 0)
            current_price = state.get('current_price', 0)
            
            if entry_price > 0:
                if state.get('position_type') == 'BUY':
                    unrealized_pnl_pct = (current_price - entry_price) / entry_price
                else:  # SELL
                    unrealized_pnl_pct = (entry_price - current_price) / entry_price
            else:
                unrealized_pnl_pct = 0
            
            # Âge de la position en minutes
            position_age = state.get('position_age', 0)
            
            # RSI normalisé
            rsi = state.get('rsi', 50) / 100.0
            
            # MACD normalisé
            macd = state.get('macd', 0)
            macd_normalized = np.tanh(macd * 10)  # Normalisation avec tanh
            
            # Volatilité
            volatility = min(state.get('volatility', 0.05) * 10, 1.0)  # Limiter à 1.0
            
            # Momentum normalisé
            momentum = state.get('momentum', 0)
            momentum_normalized = np.tanh(momentum / 10)  # Normalisation
            
            # Type de position (1 pour BUY, 0 pour SELL)
            position_type = 1.0 if state.get('position_type') == 'BUY' else 0.0
            
            # Nombre de patterns de chandeliers
            candle_patterns_count = len(state.get('candle_patterns', [])) / 10.0  # Normaliser
            
            # Spread normalisé
            spread = min(state.get('spread', 0) * 1000, 1.0)  # Normaliser
            
            features = [
                unrealized_pnl_pct * 100,      # PnL en pourcentage
                position_age / 60.0,           # Âge en heures normalisé
                rsi,                           # RSI normalisé
                macd_normalized,               # MACD normalisé
                volatility,                    # Volatilité normalisée
                momentum_normalized,           # Momentum normalisé
                position_type,                 # Type de position
                candle_patterns_count,         # Patterns de chandeliers
                spread                         # Spread normalisé
            ]
            
            # S'assurer qu'on a exactement 9 features
            if len(features) != 9:
                print(f"⚠️ Features incorrectes: {len(features)} au lieu de 9")
                # Compléter ou tronquer si nécessaire
                features = features[:9] if len(features) > 9 else features + [0.0] * (9 - len(features))
            
            return features
            
        except Exception as e:
            print(f"❌ Erreur extraction features sortie: {e}")
            return [0.0] * 9  # Retourner des features neutres

    def basic_exit_probability(self, state: Dict) -> float:
        """Logique basique de probabilité de sortie - VERSION AMÉLIORÉE"""
        try:
            prob = 0.0
            
            # RSI extrême
            rsi = state.get('rsi', 50)
            if rsi > 80 or rsi < 20:
                prob += 0.3
                
            # Profit important à protéger
            entry_price = state.get('entry_price', 0)
            current_price = state.get('current_price', 0)
            
            if entry_price > 0:
                if state.get('position_type') == 'BUY':
                    pnl_pct = (current_price - entry_price) / entry_price
                else:
                    pnl_pct = (entry_price - current_price) / entry_price
                
                # Plus le profit est important, plus on veut protéger
                if pnl_pct > 0.002:  # 0.2% de profit
                    prob += min(0.4, pnl_pct * 100)  # Maximum 40%
                elif pnl_pct < -0.001:  # 0.1% de perte
                    prob += 0.2  # Couper les pertes
                    
            # Position âgée
            position_age = state.get('position_age', 0)  # en minutes
            if position_age > 30:  # 30 minutes
                prob += min(0.3, position_age / 100)  # Maximum 30%
                
            # Volatilité élevée
            volatility = state.get('volatility', 0.05)
            if volatility > 0.1:
                prob += 0.2
                
            # Momentum défavorable
            momentum = state.get('momentum', 0)
            position_type = state.get('position_type')
            if (position_type == 'BUY' and momentum < -0.05) or (position_type == 'SELL' and momentum > 0.05):
                prob += 0.25
                
            return min(0.95, prob)  # Limiter à 95%
            
        except Exception as e:
            print(f"❌ Erreur probabilité sortie basique: {e}")
            return 0.5

    def update_with_reward(self, exit_data: Dict, reward: float):
        """Enregistre l'expérience (pas d'entraînement local)."""
        try:
            state = exit_data.get('market_conditions', {})
            features = self.extract_exit_features(state)

            self.exit_experiences.append({
                'features': features,
                'reward': reward,
                'timestamp': datetime.now(),
                'exit_score': exit_data.get('exit_score', 0),
                'profit': exit_data.get('profit', 0)
            })

            self.exit_memory_size = len(self.exit_experiences)
        except Exception as e:
            print(f"❌ Erreur mise à jour récompense sortie: {e}")

    def train_exit_model(self, batch_size=32):
        """Désactivé (modèle local supprimé)."""
        return
            
            for experience in batch:
                features_batch.append(experience['features'])
                targets_batch.append([experience['target']])
            
            # Entraînement
            features_array = np.array(features_batch, dtype=np.float32)
            targets_array = np.array(targets_batch, dtype=np.float32)
            
            history = self.exit_model.fit(
                features_array, 
                targets_array, 
                epochs=1, 
                verbose=0,
                batch_size=batch_size
            )
            
            loss = history.history['loss'][0] if 'loss' in history.history else 0
            accuracy = history.history['accuracy'][0] if 'accuracy' in history.history else 0
            
            print(f"🎯 Entraînement modèle sortie - Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")
            
        except Exception as e:
            print(f"❌ Erreur entraînement modèle sortie: {e}")

    def save_exit_model(self):
        """Sauvegarde le modèle de sortie"""
        try:
            if hasattr(self, 'exit_model') and self.exit_model:
                self.exit_model.save('exit_model.h5')
                print("💾 Modèle de sortie sauvegardé")
        except Exception as e:
            print(f"❌ Erreur sauvegarde modèle sortie: {e}")

    def load_exit_model(self):
        """Désactivé (modèle local supprimé)."""
        return None
        """Sauvegarde le modèle entraîné"""
        try:
            self.save_model_safe('evolutionary_brain_model.h5')
            print("💾 Modèle sauvegardé avec succès")
        except Exception as e:
            print(f"❌ Erreur sauvegarde modèle: {e}")
            
    def save_model_safe(self, filepath='evolutionary_brain_model.h5'):
        """Désactivé (modèle local supprimé)."""
        return None
    
    def load_model(self):
        """Désactivé (modèle local supprimé)."""
        return None
     
    def _build_model(self):
        """Désactivé (modèle local supprimé)."""
        return None
    
    def remember(self, state, action, reward, next_state, done):
        """Mémorise l'expérience - VERSION CORRIGÉE"""
        try:
            # ✅ CONVERSION EXPLICITE en tuple
            experience = (
                list(state) if isinstance(state, (list, np.ndarray)) else state,
                int(action),
                float(reward),
                list(next_state) if isinstance(next_state, (list, np.ndarray)) else next_state,
                bool(done)
            )
            
            # ✅ AJOUT DIRECT à la mémoire
            self.memory.append(experience)
            
            # ✅ DEBUG
            if len(self.memory) % 5 == 0:  # Log tous les 5 ajouts
                print(f"🧠 MEMORY: +1 expérience → total={len(self.memory)}")
                
            return True
            
        except Exception as e:
            print(f"❌ ERREUR remember(): {e}")
            return False
            
    def force_add_memory(self, count=5):
        """Force l'ajout d'expériences de test en mémoire"""
        for i in range(count):
            test_state = [random.random() for _ in range(50)]
            test_action = random.randint(0, 4)
            test_reward = random.uniform(-1, 1)
            
            self.remember(test_state, test_action, test_reward, test_state, False)
        
        print(f"🧪 {count} expériences de test ajoutées forcément")
        return len(self.memory)

    def reset_memory(self):
        """Vide la mémoire (pour tests)"""
        self.memory.clear()
        self.step_count = 0
        self.epsilon = 1.0
        print("🧹 Mémoire du cerveau réinitialisée")

    def act(self, state):
        """Prend une décision avec exploration/exploitation et nettoyage mémoire"""
        self.cleanup_memory()  # ✅ NETTOYAGE MÉMOIRE
        if np.random.random() <= self.epsilon:
            return random.randrange(5)  # Exploration
        
        state_array = np.array(state, dtype=np.float32).reshape(1, -1)
        act_values = self.model.predict(state_array, verbose=0)
        return np.argmax(act_values[0])  # Exploitation
    
    def replay(self):
        """Apprentissage sur la mémoire"""
        if len(self.memory) < self.batch_size:
            return
        
        minibatch = random.sample(self.memory, self.batch_size)
        
        for state, action, reward, next_state, done in minibatch:
            target = self.model.predict(np.array(state).reshape(1, -1), verbose=0)
            
            if done:
                target[0][action] = reward
            else:
                next_state = np.array(next_state).reshape(1, -1)
                t = self.target_model.predict(next_state, verbose=0)
                target[0][action] = reward + self.gamma * np.amax(t)
            
            self.model.fit(np.array(state).reshape(1, -1), target, epochs=1, verbose=0)
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        self.step_count += 1
        if self.step_count % self.update_target_every == 0:
            self.update_target_model()
    
    def update_target_model(self):
        """Met à jour le modèle cible"""
        self.target_model.set_weights(self.model.get_weights())  # ⬅️ CORRECTION ICI
        
    def cleanup_memory(self):
        """Nettoie la mémoire périodiquement"""
        current_time = time.time()
        if current_time - self.last_memory_cleanup > self.memory_cleanup_interval:
            before = psutil.Process(os.getpid()).memory_percent()
            
            # Nettoyage mémoire principale
            gc.collect()
            
            # Nettoyage mémoire sorties (garder seulement les plus récentes)
            if len(self.exit_experiences) > 4000:
                self.exit_experiences = deque(list(self.exit_experiences)[-4000:], maxlen=5000)
                self.exit_memory_size = len(self.exit_experiences)
                print(f"🧹 Mémoire sorties nettoyée - Gardé: {self.exit_memory_size} expériences")
            
            self.last_memory_cleanup = current_time
            after = psutil.Process(os.getpid()).memory_percent()
            print(f"🧹 Mémoire nettoyée - RAM: {before:.1f}% → {after:.1f}%")
            
    def optimize_exit_training(self):
        """Optimise l'entraînement du modèle de sortie"""
        try:
            if len(self.exit_experiences) < 100:
                print("⚠️ Pas assez de données pour l'optimisation")
                return
            
            # Séparer les expériences réussies et échouées
            successful_exits = [exp for exp in self.exit_experiences if exp['reward'] > 0]
            failed_exits = [exp for exp in self.exit_experiences if exp['reward'] <= 0]
            
            # Équilibrer les données si nécessaire
            min_samples = min(len(successful_exits), len(failed_exits))
            if min_samples > 0:
                # Prendre un nombre égal d'échantillons de chaque classe
                balanced_successful = random.sample(successful_exits, min_samples)
                balanced_failed = random.sample(failed_exits, min_samples)
                balanced_data = balanced_successful + balanced_failed
                random.shuffle(balanced_data)
                
                # Réentraînement avec données équilibrées
                features_batch = [exp['features'] for exp in balanced_data]
                targets_batch = [[exp['target']] for exp in balanced_data]
                
                features_array = np.array(features_batch, dtype=np.float32)
                targets_array = np.array(targets_batch, dtype=np.float32)
                
                history = self.exit_model.fit(
                    features_array, 
                    targets_array, 
                    epochs=3,  # Plus d'epochs pour l'optimisation
                    verbose=0,
                    batch_size=min(32, len(balanced_data))
                )
                
                loss = history.history['loss'][-1] if 'loss' in history.history else 0
                accuracy = history.history['accuracy'][-1] if 'accuracy' in history.history else 0
                
                print(f"🎯 Optimisation modèle sortie - Loss: {loss:.4f}, Accuracy: {accuracy:.4f}")
                return True
                
        except Exception as e:
            print(f"❌ Erreur optimisation entraînement sortie: {e}")
            return False
            
    def calculate_momentum(self, prices, period=14):
        """Calcule le momentum de manière sécurisée"""
        try:
            if len(prices) < period + 1:
                return 0.0
            
            current_price = prices[-1]
            previous_price = prices[-period-1]
            
            if previous_price > 0:
                momentum = ((current_price - previous_price) / previous_price) * 100
                return momentum
            return 0.0
        except Exception as e:
            print(f"❌ Erreur calcul momentum: {e}")
            return 0.0

# ████████████████████████████████████████████████████████████████████████████████
# AJOUTER APRÈS LA CLASSE - PAS DEDANS !
# ████████████████████████████████████████████████████████████████████████████████

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "service": "Evolutionary Brain - BTCUSD Micro Scalper V8", 
        "status": "running",
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/brain/health')
def health():
    return jsonify({"status": "healthy", "service": "Evolutionary Brain"})
    
@app.route('/api/brain/quick_health', methods=['GET'])
def quick_health():
    """Endpoint de santé ultra-rapide"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'memory_size': len(get_brain_instance().memory),
            'response_time_ms': 0.1
        })
    except:
        return jsonify({'status': 'unhealthy'}), 500

@app.route('/api/status') 
def status():
    return jsonify({
        "model_version": "v1.0",
        "status": "ACTIVE", 
        "predictions": 0,
        "accuracy": 0.0
    })
   
# ████████████████████████████████████████████████████████████████████████████████
# AJOUTER APRÈS LES AUTRES ROUTES @app.route
# ████████████████████████████████████████████████████████████████████████████████

from flask import request
@app.route('/api/analyze', methods=['POST'])
def analyze_market():
    """Endpoint pour analyser le marché avec l'IA évolutive - VERSION CORRIGÉE"""
    try:
        # ✅ AJOUTER CETTE LIGNE MANQUANTE
        import time
        start_time = time.time()
        
        # Vérifier que les données sont présentes
        if not request.json:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        market_data = request.get_json()
        symbol = market_data.get('symbol', 'BTCUSD')
        
        # ✅ UTILISER L'INSTANCE GLOBALE UNIQUE
        brain = get_brain_instance()
        
        # Préparer l'état avec les données du marché
        state = [
            market_data.get('rsi', 50) / 100,                    # RSI normalisé
            market_data.get('volatility', 0.01) * 100,           # Volatilité
            market_data.get('bid', 0) / 100000,                  # Prix normalisé
            market_data.get('momentum', 0) / 100,                # Momentum
            market_data.get('volume', 1000) / 10000,             # Volume
            market_data.get('spread', 0) / 1000,                 # Spread
            market_data.get('trend_strength', 0.5),              # Force tendance
            datetime.now().hour / 24.0,                          # Heure
            datetime.now().weekday() / 7.0,                      # Jour
            random.random(),                                     # Bruit exploration
        ]
        
        # Compléter à 50 features
        if len(state) < 50:
            state += [0.0] * (50 - len(state))
        elif len(state) > 50:
            state = state[:50]
        
        # ✅ NOUVELLE LOGIQUE DE PRÉDICTION AVEC EXPLORATION/EXPLOITATION
        state_array = np.array(state, dtype=np.float32).reshape(1, -1)
        
        # Exploration vs Exploitation
        if np.random.random() <= brain.epsilon:
            action = random.randint(0, 4)  # Exploration aléatoire
            probabilities = [0.2, 0.2, 0.2, 0.2, 0.2]  # Distribution uniforme pour l'exploration
        else:
            # Exploitation : utiliser le modèle
            probabilities = brain.model.predict(state_array, verbose=0)[0]
            action = np.argmax(probabilities)
            
        processing_time = time.time() - start_time
        # ✅ LOG de performance
        if processing_time > 2.0:  # Si > 2 secondes
            logging.warning(f"⏱️  Prédiction lente: {processing_time:.2f}s")

        confidence = float(np.max(probabilities)) if brain.epsilon < 0.9 else 0.5
        
        # ✅ NOUVELLE LOGIQUE DE RÉCOMPENSE INTELLIGENTE
        reward = 0.0
        rsi = market_data.get('rsi', 50)
        volatility = market_data.get('volatility', 0.01)
        
        # Récompenser les décisions logiques selon le RSI
        if action == 0 or action == 1:  # BUY actions
            if rsi < 35:
                reward = 0.8  # Bon achat en zone oversold
            elif rsi > 65:
                reward = -0.5  # Mauvais achat en zone overbought
            else:
                reward = 0.1  # Neutre
                
        elif action == 3 or action == 4:  # SELL actions  
            if rsi > 65:
                reward = 0.8  # Bonne vente en zone overbought
            elif rsi < 35:
                reward = -0.5  # Mauvaise vente en zone oversold
            else:
                reward = 0.1  # Neutre
                
        else:  # NEUTRAL action (2)
            if 40 <= rsi <= 60:
                reward = 0.3  # Bon neutre en zone neutre
            else:
                reward = -0.2  # Mauvais neutre en zone extrême
        
        # Ajustement basé sur la volatilité
        if volatility > 0.03:
            reward *= 0.7  # Réduction récompense en haute volatilité
        
        # ✅ MÉMORISATION ET APPRENTISSAGE
        next_state = state  # Même état pour simplification
        done = False
        
        brain.remember(state, action, reward, next_state, done)
        
        # ✅ APPRENTISSAGE SEULEMENT SI ASSEZ DE MÉMOIRE
        if len(brain.memory) >= brain.batch_size:
            brain.replay()
        
        # ✅ SAUVEGARDE AUTOMATIQUE TOUTES LES 50 STEPS
        if brain.step_count > 0 and brain.step_count % 50 == 0:
            brain.save_model()
        
        brain.step_count += 1
        
        direction_map = {
            0: "STRONG_BUY",
            1: "BUY", 
            2: "NEUTRAL",
            3: "SELL",
            4: "STRONG_SELL"
        }
        
        return jsonify({
            'symbol': symbol,
            'direction': direction_map[action],
            'confidence': confidence,
            'reward': reward,  # ✅ NOUVEAU : montrer la récompense
            'price': market_data.get('bid', 0),
            'memory_size': len(brain.memory),  # ✅ NOUVEAU : taille mémoire
            'epsilon': brain.epsilon,  # ✅ DÉJÀ PRÉSENT
            'step_count': brain.step_count,  # ✅ NOUVEAU : compteur d'étapes
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Erreur dans analyze_market: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_brain_server():
    """Démarre le serveur du cerveau évolutif"""
    print("=" * 50)
    print("🧠 CERVEAU ÉVOLUTIF AVEC TENSORFLOW")
    print("🌐 Serveur: http://localhost:5004")
    print("🤖 Deep Learning: Activé")
    print("🎯 Réseau neuronal: 512-256-128-64-5")
    print("=" * 50)
    
    # Test du cerveau
    brain = EvolutionaryBrain()
    test_state = [0.5] * 50
    action = brain.act(test_state)
    print(f"🧪 Test réussi - Action: {action}")
    
    # ✅ SERVEUR HAUTE PERFORMANCE
    from werkzeug.serving import WSGIRequestHandler

    class CustomRequestHandler(WSGIRequestHandler):
        def handle(self):
            """Override pour timeout réduit"""
            self.timeout = 30  # Timeout de 30s par requête
            super().handle()
    
    # Démarrer le serveur Flask
    app.run(host='0.0.0.0', port=5004, debug=False, use_reloader=False, threaded=True, processes=1, request_handler=CustomRequestHandler)
    
# evolutionary_brain.py - AJOUTER APRÈS LES AUTRES ROUTES

@app.route('/api/save_model', methods=['POST'])
def save_model():
    """Sauvegarde manuelle du modèle"""
    try:
        brain = get_brain_instance()
        brain.save_model()
        return jsonify({'status': 'success', 'message': 'Modèle sauvegardé'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# evolutionary_brain.py - REMPLACER la route brain_stats()

@app.route('/api/brain/stats', methods=['GET'])
def brain_stats():
    """Retourne les statistiques d'apprentissage - VERSION CORRIGÉE"""
    brain = get_brain_instance()
    return jsonify({
        'memory_size': len(brain.memory),  # ✅ CORRIGÉ : 'memory_size' au lieu de 'taille_mémoire'
        'epsilon': brain.epsilon,
        'step_count': brain.step_count,
        'batch_size': brain.batch_size,
        'model_loaded': os.path.exists('evolutionary_brain_model.h5')
    })
    
@app.route('/api/brain/ping')
def ping():
    """Simple endpoint ping pour tester la latence"""
    return jsonify({'status': 'pong', 'timestamp': datetime.now().isoformat()})
    
# evolutionary_brain.py - AJOUTER cette nouvelle route

@app.route('/api/brain/debug', methods=['POST'])
def brain_debug():
    """Route de debug pour tester l'apprentissage"""
    brain = get_brain_instance()
    
    # Créer un état de test
    test_state = [0.5] * 50
    
    # Test prediction
    action = brain.act(test_state)
    state_array = np.array(test_state).reshape(1, -1)
    probabilities = brain.model.predict(state_array, verbose=0)[0]
    
    # Ajouter à la mémoire
    reward = 1.0
    brain.remember(test_state, action, reward, test_state, False)
    
    return jsonify({
        'debug_action': action,
        'debug_probabilities': probabilities.tolist(),
        'memory_size_before_replay': len(brain.memory),
        'epsilon_before_replay': brain.epsilon
    })
    
@app.route('/api/brain/test_instance', methods=['GET'])
def test_instance():
    """Test si l'instance globale fonctionne"""
    brain1 = get_brain_instance()
    brain2 = get_brain_instance()
    
    return jsonify({
        'same_instance': brain1 is brain2,
        'brain1_id': id(brain1),
        'brain2_id': id(brain2),
        'brain1_memory': len(brain1.memory),
        'brain2_memory': len(brain2.memory)
    })
    
@app.route('/api/brain/force_memory', methods=['POST'])
def force_memory():
    """Force l'ajout d'expériences en mémoire pour test"""
    brain = get_brain_instance()
    
    data = request.get_json() or {}
    count = data.get('count', 5)
    
    before = len(brain.memory)
    brain.force_add_memory(count)
    after = len(brain.memory)
    
    return jsonify({
        'memory_before': before,
        'memory_after': after,
        'added': after - before,
        'success': after > before
    })
    
@app.route('/api/reset_memory', methods=['POST'])
def reset_memory():
    """Réinitialise la mémoire du cerveau"""
    try:
        brain = get_brain_instance()
        brain.reset_memory()
        return jsonify({'status': 'success', 'message': 'Mémoire réinitialisée'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/brain/exit_stats', methods=['GET'])
def exit_stats_V2():
    """Retourne les statistiques du système de sortie"""
    brain = get_brain_instance()
    
    # Calculer les statistiques de performance des sorties
    if brain.exit_experiences:
        recent_experiences = list(brain.exit_experiences)[-100:]  # 100 dernières
        successful_exits = sum(1 for exp in recent_experiences if exp['reward'] > 0)
        total_exits = len(recent_experiences)
        success_rate = successful_exits / total_exits if total_exits > 0 else 0
        
        avg_profit = np.mean([exp['profit'] for exp in recent_experiences])
        avg_exit_score = np.mean([exp['exit_score'] for exp in recent_experiences])
    else:
        success_rate = 0
        avg_profit = 0
        avg_exit_score = 0
    
    return jsonify({
        'exit_memory_size': brain.exit_memory_size,
        'success_rate': success_rate,
        'avg_profit': avg_profit,
        'avg_exit_score': avg_exit_score,
        'total_exit_experiences': len(brain.exit_experiences)
    })

@app.route('/api/brain/test_exit_prediction', methods=['POST'])
def test_exit_prediction():
    """Teste la prédiction de sortie avec des données d'exemple"""
    try:
        brain = get_brain_instance()
        
        # Données de test
        test_state = {
            'position_type': 'BUY',
            'entry_price': 50000,
            'current_price': 50200,
            'profit': 200,
            'rsi': 65,
            'macd': 0.002,
            'volatility': 0.08,
            'momentum': 0.05,
            'position_age': 15,  # minutes
            'candle_patterns': ['DOJI'],
            'spread': 0.0001
        }
        
        exit_prob = brain.predict_exit_probability(test_state)
        features = brain.extract_exit_features(test_state)
        
        return jsonify({
            'exit_probability': exit_prob,
            'features': features,
            'features_count': len(features),
            'interpretation': 'HAUTE' if exit_prob > 0.7 else 'MOYENNE' if exit_prob > 0.5 else 'FAIBLE'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/brain/train_exit_model', methods=['POST'])
def train_exit_model():
    """Lance l'entraînement du modèle de sortie"""
    try:
        brain = get_brain_instance()
        data = request.get_json() or {}
        batch_size = data.get('batch_size', 32)
        
        brain.train_exit_model(batch_size)
        
        return jsonify({
            'status': 'success',
            'message': f'Modèle de sortie entraîné avec batch_size={batch_size}',
            'exit_memory_size': brain.exit_memory_size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/brain/save_exit_model', methods=['POST'])
def save_exit_model():
    """Sauvegarde le modèle de sortie"""
    try:
        brain = get_brain_instance()
        brain.save_exit_model()
        return jsonify({'status': 'success', 'message': 'Modèle de sortie sauvegardé'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/brain/exit_debug', methods=['POST'])
def exit_debug():
    """Debug détaillé du système de sortie"""
    brain = get_brain_instance()
    
    # État de test complet
    test_state = {
        'position_type': 'BUY',
        'entry_price': 50000,
        'current_price': 50100,  # 0.2% de profit
        'profit': 100,
        'rsi': 75,  # Suracheté
        'macd': -0.001,  # Négatif
        'volatility': 0.12,  # Élevée
        'momentum': -0.08,  # Baissier
        'position_age': 45,  # 45 minutes
        'candle_patterns': ['BEARISH_ENGULFING', 'SHOOTING_STAR'],
        'spread': 0.0002
    }
    
    # Test de prédiction
    exit_prob = brain.predict_exit_probability(test_state)
    features = brain.extract_exit_features(test_state)
    basic_prob = brain.basic_exit_probability(test_state)
    
    # Simulation de mise à jour
    exit_data = {
        'market_conditions': test_state,
        'exit_score': exit_prob,
        'profit': 100
    }
    brain.update_with_reward(exit_data, 1.0)  # Récompense positive
    
    return jsonify({
        'exit_probability_model': exit_prob,
        'exit_probability_basic': basic_prob,
        'features': features,
        'feature_names': [
            'pnl_pct', 'position_age_hours', 'rsi_normalized', 'macd_normalized',
            'volatility', 'momentum_normalized', 'position_type', 'candle_patterns_count', 'spread'
        ],
        'memory_size_after_update': brain.exit_memory_size,
        'interpretation': 'SORTIE RECOMMANDÉE' if exit_prob > 0.7 else 'SURVEILLANCE' if exit_prob > 0.5 else 'MAINTIEN'
    })
    
@app.route('/api/brain/full_integration_test', methods=['GET'])
def full_integration_test():
    """Test complet de l'intégration sortie intelligente"""
    brain = get_brain_instance()
    
    # Test 1: Prédiction de sortie
    test_state = {
        'position_type': 'BUY',
        'entry_price': 50000,
        'current_price': 50250,
        'profit': 250,
        'rsi': 72,
        'macd': -0.002,
        'volatility': 0.09,
        'momentum': -0.03,
        'position_age': 25,
        'candle_patterns': ['DOJI'],
        'spread': 0.00015
    }
    
    exit_prob = brain.predict_exit_probability(test_state)
    
    # Test 2: Apprentissage
    exit_data = {
        'market_conditions': test_state,
        'exit_score': exit_prob,
        'profit': 250
    }
    brain.update_with_reward(exit_data, 1.0)
    
    # Test 3: Entraînement
    brain.train_exit_model(16)
    
    return jsonify({
        'integration_test': 'COMPLETED',
        'exit_probability': exit_prob,
        'exit_memory_size': brain.exit_memory_size,
        'main_memory_size': len(brain.memory),
        'recommendation': 'SORTIE' if exit_prob > 0.7 else 'ATTENTE',
        'confidence': 'ÉLEVÉE' if exit_prob > 0.8 else 'MOYENNE' if exit_prob > 0.6 else 'FAIBLE'
    })
    
@app.route('/api/brain/exit_stats', methods=['GET'])
def exit_stats():
    """Retourne les statistiques du système de sortie"""
    brain = get_brain_instance()
    
    # Calculer les statistiques de performance des sorties
    if brain.exit_experiences:
        recent_experiences = list(brain.exit_experiences)[-100:]  # 100 dernières
        successful_exits = sum(1 for exp in recent_experiences if exp['reward'] > 0)
        total_exits = len(recent_experiences)
        success_rate = successful_exits / total_exits if total_exits > 0 else 0
        
        avg_profit = np.mean([exp['profit'] for exp in recent_experiences])
        avg_exit_score = np.mean([exp['exit_score'] for exp in recent_experiences])
    else:
        success_rate = 0
        avg_profit = 0
        avg_exit_score = 0
    
    return jsonify({
        'exit_memory_size': brain.exit_memory_size,
        'success_rate': success_rate,
        'avg_profit': avg_profit,
        'avg_exit_score': avg_exit_score,
        'total_exit_experiences': len(brain.exit_experiences)
    })
    
@app.route('/api/brain/test_intelligent_exit', methods=['POST'])
def test_intelligent_exit():
    """Test complet du système de sortie intelligente"""
    try:
        brain = get_brain_instance()
        
        # Données de test réalistes
        test_cases = [
            {
                'name': 'CAS PROFITABLE - DOIT RESTER',
                'state': {
                    'position_type': 'BUY',
                    'entry_price': 50000,
                    'current_price': 50300,  # 0.6% profit
                    'profit': 300,
                    'rsi': 45,  # Neutre
                    'macd': 0.001,  # Positif
                    'volatility': 0.06,  # Normale
                    'momentum': 0.02,  # Légèrement positif
                    'position_age': 10,  # 10 minutes
                    'candle_patterns': ['BULLISH_ENGULFING'],
                    'spread': 0.0001
                },
                'expected_action': 'MAINTIEN'
            },
            {
                'name': 'CAS RISQUÉ - DOIT SORTIR',
                'state': {
                    'position_type': 'BUY',
                    'entry_price': 50000,
                    'current_price': 49800,  # 0.4% perte
                    'profit': -200,
                    'rsi': 78,  # Suracheté
                    'macd': -0.003,  # Négatif
                    'volatility': 0.15,  # Élevée
                    'momentum': -0.08,  # Négatif
                    'position_age': 40,  # 40 minutes
                    'candle_patterns': ['BEARISH_ENGULFING', 'SHOOTING_STAR'],
                    'spread': 0.0003
                },
                'expected_action': 'SORTIE'
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            exit_prob = brain.predict_exit_probability(test_case['state'])
            features = brain.extract_exit_features(test_case['state'])
            
            # Décision basée sur le seuil de 0.75
            decision = 'SORTIE' if exit_prob > 0.75 else 'MAINTIEN'
            correct = decision == test_case['expected_action']
            
            results.append({
                'test_name': test_case['name'],
                'exit_probability': exit_prob,
                'decision': decision,
                'expected': test_case['expected_action'],
                'correct': correct,
                'features_count': len(features)
            })
        
        # Calcul du score global
        correct_count = sum(1 for r in results if r['correct'])
        total_tests = len(results)
        success_rate = correct_count / total_tests if total_tests > 0 else 0
        
        return jsonify({
            'test_results': results,
            'success_rate': success_rate,
            'total_tests': total_tests,
            'correct_count': correct_count,
            'system_status': 'FONCTIONNEL' if success_rate >= 0.5 else 'BESOIN AJUSTEMENTS'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/brain/performance_monitor', methods=['GET'])
def performance_monitor():
    """Surveillance en temps réel des performances"""
    brain = get_brain_instance()
    
    # Statistiques principales
    main_stats = {
        'memory_size': len(brain.memory),
        'epsilon': brain.epsilon,
        'step_count': brain.step_count,
        'model_loaded': os.path.exists('evolutionary_brain_model.h5')
    }
    
    # Statistiques sortie intelligente
    exit_stats = {
        'exit_memory_size': brain.exit_memory_size,
        'total_exit_experiences': len(brain.exit_experiences),
        'exit_model_loaded': os.path.exists('exit_model.h5')
    }
    
    # Performance récente
    if brain.exit_experiences:
        recent = list(brain.exit_experiences)[-50:]  # 50 dernières
        recent_success = sum(1 for exp in recent if exp['reward'] > 0)
        recent_total = len(recent)
        recent_success_rate = recent_success / recent_total if recent_total > 0 else 0
        recent_avg_profit = np.mean([exp['profit'] for exp in recent])
    else:
        recent_success_rate = 0
        recent_avg_profit = 0
    
    return jsonify({
        'main_brain': main_stats,
        'intelligent_exit': exit_stats,
        'recent_performance': {
            'success_rate': recent_success_rate,
            'avg_profit': recent_avg_profit,
            'sample_size': len(brain.exit_experiences) if brain.exit_experiences else 0
        },
        'system_health': {
            'memory_usage_percent': psutil.Process(os.getpid()).memory_percent(),
            'cpu_usage_percent': psutil.cpu_percent(),
            'timestamp': datetime.now().isoformat()
        }
    })
    
@app.route('/api/brain/optimize_exit_training', methods=['POST'])
def optimize_exit_training_route():
    """Lance l'optimisation de l'entraînement du modèle de sortie"""
    try:
        brain = get_brain_instance()
        success = brain.optimize_exit_training()
        
        return jsonify({
            'status': 'success' if success else 'insufficient_data',
            'message': 'Optimisation terminée' if success else 'Données insuffisantes pour optimisation',
            'exit_memory_size': brain.exit_memory_size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/brain/final_integration_test', methods=['GET'])
def final_integration_test():
    """Test final de l'intégration complète du système de sortie intelligente"""
    brain = get_brain_instance()
    
    # Test de toutes les fonctionnalités
    test_results = {}
    
    # 1. Test du modèle principal
    try:
        test_state = [0.5] * 50
        action = brain.act(test_state)
        test_results['main_model'] = {'status': 'OK', 'action': action}
    except Exception as e:
        test_results['main_model'] = {'status': 'ERROR', 'error': str(e)}
    
    # 2. Test du modèle de sortie
    try:
        test_exit_state = {
            'position_type': 'BUY',
            'entry_price': 50000,
            'current_price': 50100,
            'profit': 100,
            'rsi': 60,
            'macd': 0.001,
            'volatility': 0.05,
            'momentum': 0.01,
            'position_age': 15,
            'candle_patterns': [],
            'spread': 0.0001
        }
        exit_prob = brain.predict_exit_probability(test_exit_state)
        test_results['exit_model'] = {'status': 'OK', 'exit_probability': exit_prob}
    except Exception as e:
        test_results['exit_model'] = {'status': 'ERROR', 'error': str(e)}
    
    # 3. Test de l'apprentissage
    try:
        brain.remember(test_state, 1, 0.5, test_state, False)
        test_results['learning'] = {'status': 'OK', 'memory_size': len(brain.memory)}
    except Exception as e:
        test_results['learning'] = {'status': 'ERROR', 'error': str(e)}
    
    # 4. Test de la mise à jour des sorties
    try:
        exit_data = {
            'market_conditions': test_exit_state,
            'exit_score': 0.7,
            'profit': 100
        }
        brain.update_with_reward(exit_data, 1.0)
        test_results['exit_learning'] = {'status': 'OK', 'exit_memory_size': brain.exit_memory_size}
    except Exception as e:
        test_results['exit_learning'] = {'status': 'ERROR', 'error': str(e)}
    
    # Résumé final
    all_ok = all(result['status'] == 'OK' for result in test_results.values())
    
    return jsonify({
        'integration_test': 'COMPLETED',
        'all_systems_ok': all_ok,
        'test_results': test_results,
        'system_status': 'FULLY_OPERATIONAL' if all_ok else 'PARTIALLY_OPERATIONAL',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    run_brain_server()
"""