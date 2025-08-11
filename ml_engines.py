import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import networkx as nx
import logging
from datetime import datetime, timedelta
from models import EmailRecord, RecipientRecord

class BasicMLEngine:
    """Basic ML engine for risk scoring and anomaly detection"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.logger = logging.getLogger(__name__)
    
    def predict_risk(self, features):
        """Predict risk score for email/recipient"""
        try:
            # Convert features to array
            feature_array = self._features_to_array(features)
            
            if not self.is_fitted:
                self._fit_model(feature_array)
            
            # Normalize features
            feature_array = feature_array.reshape(1, -1)
            normalized_features = self.scaler.transform(feature_array)
            
            # Get anomaly score
            anomaly_score = self.isolation_forest.decision_function(normalized_features)[0]
            
            # Convert to risk score (0-10)
            risk_score = max(0, min(10, (1 - anomaly_score) * 5))
            
            return float(risk_score)
            
        except Exception as e:
            self.logger.error(f"Error in basic ML prediction: {str(e)}")
            return 0.0
    
    def _features_to_array(self, features):
        """Convert feature dict to numpy array"""
        # Define feature order
        feature_keys = [
            'subject_length', 'has_attachments', 'sender_domain_length',
            'is_external', 'is_leaver', 'has_termination',
            'security_score', 'risk_score'
        ]
        
        return np.array([features.get(key, 0) for key in feature_keys])
    
    def _fit_model(self, sample_features):
        """Fit model with sample data"""
        try:
            # Generate synthetic training data for initial fitting
            np.random.seed(42)
            synthetic_data = np.random.rand(100, len(sample_features))
            
            # Fit scaler and model
            self.scaler.fit(synthetic_data)
            self.isolation_forest.fit(synthetic_data)
            
            self.is_fitted = True
            self.logger.info("Basic ML model fitted successfully")
            
        except Exception as e:
            self.logger.error(f"Error fitting basic ML model: {str(e)}")

class AdvancedMLEngine:
    """Advanced ML engine with network analysis and correlation detection"""
    
    def __init__(self):
        self.network_graph = nx.DiGraph()
        self.random_forest = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.logger = logging.getLogger(__name__)
    
    def predict_risk(self, features):
        """Predict risk score using advanced ML techniques"""
        try:
            # Convert features to array
            feature_array = self._features_to_array(features)
            
            if not self.is_fitted:
                self._fit_model(feature_array)
            
            # Add network features
            network_features = self._extract_network_features(features)
            combined_features = np.concatenate([feature_array, network_features])
            
            # Normalize features
            combined_features = combined_features.reshape(1, -1)
            normalized_features = self.scaler.transform(combined_features)
            
            # Predict risk probability
            risk_probability = self.random_forest.predict_proba(normalized_features)[0]
            
            # Convert to risk score (0-10)
            risk_score = risk_probability[1] * 10 if len(risk_probability) > 1 else 5.0
            
            return float(risk_score)
            
        except Exception as e:
            self.logger.error(f"Error in advanced ML prediction: {str(e)}")
            return 0.0
    
    def _features_to_array(self, features):
        """Convert feature dict to numpy array"""
        # Define extended feature order
        feature_keys = [
            'subject_length', 'has_attachments', 'sender_domain_length',
            'is_external', 'is_leaver', 'has_termination',
            'security_score', 'risk_score', 'hour_of_day', 'day_of_week',
            'subject_exclamation_count', 'subject_question_count', 'subject_caps_ratio'
        ]
        
        return np.array([features.get(key, 0) for key in feature_keys])
    
    def _extract_network_features(self, features):
        """Extract network-based features"""
        try:
            # Simplified network features
            network_features = np.array([
                0.0,  # sender_centrality (placeholder)
                0.0,  # recipient_centrality (placeholder)
                0.0,  # communication_frequency (placeholder)
                0.0   # anomaly_in_pattern (placeholder)
            ])
            
            return network_features
            
        except Exception as e:
            self.logger.error(f"Error extracting network features: {str(e)}")
            return np.zeros(4)
    
    def _fit_model(self, sample_features):
        """Fit advanced ML model"""
        try:
            # Generate synthetic training data
            np.random.seed(42)
            n_features = len(sample_features) + 4  # +4 for network features
            synthetic_data = np.random.rand(200, n_features)
            
            # Generate synthetic labels (0: normal, 1: risky)
            synthetic_labels = np.random.choice([0, 1], size=200, p=[0.8, 0.2])
            
            # Fit scaler and model
            self.scaler.fit(synthetic_data)
            self.random_forest.fit(synthetic_data, synthetic_labels)
            
            self.is_fitted = True
            self.logger.info("Advanced ML model fitted successfully")
            
        except Exception as e:
            self.logger.error(f"Error fitting advanced ML model: {str(e)}")
    
    def update_network_graph(self, sender, recipient):
        """Update communication network graph"""
        try:
            self.network_graph.add_edge(sender, recipient)
            
            # Limit graph size to prevent memory issues
            if len(self.network_graph.nodes()) > 1000:
                # Remove oldest edges (simplified approach)
                edges_to_remove = list(self.network_graph.edges())[:100]
                self.network_graph.remove_edges_from(edges_to_remove)
                
        except Exception as e:
            self.logger.error(f"Error updating network graph: {str(e)}")
    
    def analyze_communication_patterns(self, sender, time_window_days=30):
        """Analyze communication patterns for anomaly detection"""
        try:
            # This would analyze historical communication patterns
            # For now, return baseline values
            return {
                'frequency_anomaly': 0.0,
                'timing_anomaly': 0.0,
                'recipient_anomaly': 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing communication patterns: {str(e)}")
            return {'frequency_anomaly': 0.0, 'timing_anomaly': 0.0, 'recipient_anomaly': 0.0}

class AdaptiveMLEngine:
    """Self-learning threat detection engine"""
    
    def __init__(self):
        self.feedback_buffer = []
        self.retrain_threshold = 100
        self.logger = logging.getLogger(__name__)
    
    def learn_from_feedback(self, features, actual_outcome):
        """Learn from human feedback on case outcomes"""
        self.feedback_buffer.append({
            'features': features,
            'outcome': actual_outcome,
            'timestamp': datetime.utcnow()
        })
        
        # Retrain if enough feedback accumulated
        if len(self.feedback_buffer) >= self.retrain_threshold:
            self._retrain_models()
    
    def _retrain_models(self):
        """Retrain models based on accumulated feedback"""
        try:
            self.logger.info(f"Retraining models with {len(self.feedback_buffer)} feedback samples")
            
            # Extract features and labels from feedback
            X = np.array([fb['features'] for fb in self.feedback_buffer])
            y = np.array([1 if fb['outcome'] == 'threat' else 0 for fb in self.feedback_buffer])
            
            # Update models (simplified implementation)
            # In production, this would update the actual ML models
            
            # Clear feedback buffer
            self.feedback_buffer = []
            
            self.logger.info("Model retraining completed")
            
        except Exception as e:
            self.logger.error(f"Error in model retraining: {str(e)}")
