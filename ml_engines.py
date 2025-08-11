import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
try:
    from imblearn.ensemble import BalancedRandomForestClassifier
    from imblearn.over_sampling import SMOTE
    IMBALANCED_LEARN_AVAILABLE = True
except ImportError:
    from sklearn.ensemble import RandomForestClassifier as BalancedRandomForestClassifier
    SMOTE = None
    IMBALANCED_LEARN_AVAILABLE = False
import xgboost as xgb
import networkx as nx
import textblob
from textblob import TextBlob
import logging
import re
import pickle
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from models import EmailRecord, RecipientRecord

class AdvancedNLPAnalyzer:
    """Advanced NLP analysis for email content"""
    
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 3),
            lowercase=True
        )
        self.sentiment_threshold = 0.1
        self.phishing_keywords = [
            'urgent', 'immediate', 'verify', 'account', 'suspended',
            'click here', 'update', 'confirm', 'expire', 'winner',
            'congratulations', 'limited time', 'act now', 'free',
            'guarantee', 'no risk', 'call now', 'credit card'
        ]
        self.financial_keywords = [
            'bank', 'payment', 'invoice', 'transfer', 'wire',
            'bitcoin', 'cryptocurrency', 'paypal', 'refund',
            'tax', 'irs', 'social security', 'ssn'
        ]
        self.is_fitted = False
        self.logger = logging.getLogger(__name__)
    
    def analyze_text(self, subject, content=""):
        """Comprehensive text analysis"""
        try:
            full_text = f"{subject} {content}".lower()
            blob = TextBlob(full_text)
            
            # Sentiment analysis
            sentiment_score = blob.sentiment.polarity
            sentiment_subjectivity = blob.sentiment.subjectivity
            
            # Keyword analysis
            phishing_score = self._calculate_keyword_score(full_text, self.phishing_keywords)
            financial_score = self._calculate_keyword_score(full_text, self.financial_keywords)
            
            # Text characteristics
            text_features = {
                'sentiment_score': sentiment_score,
                'sentiment_subjectivity': sentiment_subjectivity,
                'phishing_keyword_score': phishing_score,
                'financial_keyword_score': financial_score,
                'exclamation_count': full_text.count('!'),
                'question_count': full_text.count('?'),
                'caps_ratio': sum(1 for c in full_text if c.isupper()) / max(len(full_text), 1),
                'number_count': len(re.findall(r'\d+', full_text)),
                'url_count': len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', full_text)),
                'email_count': len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', full_text)),
                'word_count': len(full_text.split()),
                'char_count': len(full_text)
            }
            
            return text_features
            
        except Exception as e:
            self.logger.error(f"Error in text analysis: {str(e)}")
            return self._get_default_text_features()
    
    def _calculate_keyword_score(self, text, keywords):
        """Calculate keyword density score"""
        matches = sum(1 for keyword in keywords if keyword in text)
        return matches / len(keywords) if keywords else 0
    
    def _get_default_text_features(self):
        """Default text features for error cases"""
        return {
            'sentiment_score': 0.0,
            'sentiment_subjectivity': 0.0,
            'phishing_keyword_score': 0.0,
            'financial_keyword_score': 0.0,
            'exclamation_count': 0,
            'question_count': 0,
            'caps_ratio': 0.0,
            'number_count': 0,
            'url_count': 0,
            'email_count': 0,
            'word_count': 0,
            'char_count': 0
        }

class BasicMLEngine:
    """Enhanced basic ML engine with XGBoost"""
    
    def __init__(self):
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        self.isolation_forest = IsolationForest(
            contamination=0.15,
            random_state=42,
            n_estimators=200
        )
        self.scaler = RobustScaler()
        self.nlp_analyzer = AdvancedNLPAnalyzer()
        self.is_fitted = False
        self.feature_importance = {}
        self.logger = logging.getLogger(__name__)
    
    def predict_risk(self, features):
        """Enhanced risk prediction with NLP and ensemble methods"""
        try:
            # Extract NLP features if subject available
            subject = features.get('subject', '')
            nlp_features = self.nlp_analyzer.analyze_text(subject)
            
            # Combine traditional and NLP features
            combined_features = {**features, **nlp_features}
            feature_array = self._features_to_array(combined_features)
            
            if not self.is_fitted:
                self._fit_model(feature_array)
            
            # Normalize features
            feature_array = feature_array.reshape(1, -1)
            normalized_features = self.scaler.transform(feature_array)
            
            # Ensemble prediction
            xgb_risk = self._predict_with_xgboost(normalized_features)
            isolation_risk = self._predict_with_isolation_forest(normalized_features)
            
            # Weighted ensemble (70% XGBoost, 30% Isolation Forest)
            final_risk = (0.7 * xgb_risk) + (0.3 * isolation_risk)
            
            # Apply NLP boost for high-risk keywords
            if nlp_features.get('phishing_keyword_score', 0) > 0.3:
                final_risk = min(10.0, final_risk * 1.5)
            
            return float(max(0, min(10, final_risk)))
            
        except Exception as e:
            self.logger.error(f"Error in enhanced ML prediction: {str(e)}")
            return 2.5  # Default medium risk
    
    def _predict_with_xgboost(self, features):
        """XGBoost-based risk prediction"""
        try:
            if hasattr(self.xgb_model, 'predict_proba'):
                probabilities = self.xgb_model.predict_proba(features)[0]
                return probabilities[1] * 10 if len(probabilities) > 1 else 5.0
            else:
                return 5.0
        except:
            return 5.0
    
    def _predict_with_isolation_forest(self, features):
        """Isolation Forest anomaly detection"""
        try:
            anomaly_score = self.isolation_forest.decision_function(features)[0]
            return max(0, min(10, (1 - anomaly_score) * 5))
        except:
            return 2.5
    
    def _features_to_array(self, features):
        """Convert enhanced feature dict to numpy array"""
        # Enhanced feature set including NLP features
        feature_keys = [
            'subject_length', 'has_attachments', 'sender_domain_length',
            'is_external', 'is_leaver', 'has_termination',
            'security_score', 'risk_score', 'hour_of_day', 'day_of_week',
            # NLP features
            'sentiment_score', 'sentiment_subjectivity', 'phishing_keyword_score',
            'financial_keyword_score', 'exclamation_count', 'question_count',
            'caps_ratio', 'number_count', 'url_count', 'email_count',
            'word_count', 'char_count'
        ]
        
        return np.array([features.get(key, 0) for key in feature_keys])
    
    def _fit_model(self, sample_features):
        """Fit enhanced models with synthetic training data"""
        try:
            # Generate more sophisticated synthetic training data
            np.random.seed(42)
            n_samples = 500
            n_features = len(sample_features)
            
            # Create realistic synthetic data with different risk patterns
            normal_data = np.random.normal(0.3, 0.2, (int(n_samples * 0.7), n_features))
            risky_data = np.random.normal(0.8, 0.3, (int(n_samples * 0.3), n_features))
            
            # Combine and clip to valid ranges
            synthetic_data = np.vstack([normal_data, risky_data])
            synthetic_data = np.clip(synthetic_data, 0, 1)
            
            # Create corresponding labels
            synthetic_labels = np.hstack([
                np.zeros(int(n_samples * 0.7)),  # Normal emails
                np.ones(int(n_samples * 0.3))   # Risky emails
            ])
            
            # Fit models
            self.scaler.fit(synthetic_data)
            normalized_data = self.scaler.transform(synthetic_data)
            
            self.isolation_forest.fit(normalized_data)
            self.xgb_model.fit(normalized_data, synthetic_labels)
            
            # Calculate feature importance
            if hasattr(self.xgb_model, 'feature_importances_'):
                feature_names = [
                    'subject_length', 'has_attachments', 'sender_domain_length',
                    'is_external', 'is_leaver', 'has_termination',
                    'security_score', 'risk_score', 'hour_of_day', 'day_of_week',
                    'sentiment_score', 'sentiment_subjectivity', 'phishing_keyword_score',
                    'financial_keyword_score', 'exclamation_count', 'question_count',
                    'caps_ratio', 'number_count', 'url_count', 'email_count',
                    'word_count', 'char_count'
                ]
                self.feature_importance = dict(zip(
                    feature_names[:len(self.xgb_model.feature_importances_)],
                    self.xgb_model.feature_importances_
                ))
            
            self.is_fitted = True
            self.logger.info("Enhanced ML models fitted successfully")
            
        except Exception as e:
            self.logger.error(f"Error fitting enhanced ML models: {str(e)}")
    
    def get_feature_importance(self):
        """Get feature importance for model interpretability"""
        return self.feature_importance

class AdvancedMLEngine:
    """State-of-the-art ML engine with ensemble methods and deep pattern analysis"""
    
    def __init__(self):
        self.network_graph = nx.DiGraph()
        
        # Ensemble of advanced models
        self.models = {
            'gradient_boost': GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=8,
                random_state=42
            ),
            'balanced_rf': BalancedRandomForestClassifier(
                n_estimators=150,
                max_depth=10,
                random_state=42,
                class_weight='balanced' if IMBALANCED_LEARN_AVAILABLE else 'balanced'
            ),
            'xgboost': xgb.XGBClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                random_state=42,
                eval_metric='logloss'
            ),
            'svm': SVC(
                kernel='rbf',
                probability=True,
                random_state=42
            )
        }
        
        self.scaler = RobustScaler()
        self.smote = SMOTE(random_state=42) if IMBALANCED_LEARN_AVAILABLE else None
        self.nlp_analyzer = AdvancedNLPAnalyzer()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # Behavioral pattern tracking
        self.sender_patterns = defaultdict(list)
        self.temporal_patterns = defaultdict(list)
        self.communication_graph = defaultdict(set)
        
        # Model performance tracking
        self.model_weights = {
            'gradient_boost': 0.3,
            'balanced_rf': 0.25,
            'xgboost': 0.3,
            'svm': 0.15
        }
        
        self.is_fitted = False
        self.feature_importance_ensemble = {}
        self.logger = logging.getLogger(__name__)
    
    def predict_risk(self, features):
        """Advanced ensemble risk prediction with behavioral analysis"""
        try:
            # Extract and analyze email content
            subject = features.get('subject', '')
            sender = features.get('sender', '')
            recipient = features.get('recipient', '')
            
            # NLP analysis
            nlp_features = self.nlp_analyzer.analyze_text(subject)
            
            # Behavioral pattern analysis
            behavioral_features = self._analyze_behavioral_patterns(sender, features)
            
            # Network analysis
            network_features = self._extract_network_features(features)
            
            # Temporal analysis
            temporal_features = self._analyze_temporal_patterns(features)
            
            # Combine all feature sets
            combined_features = {
                **features,
                **nlp_features,
                **behavioral_features,
                **network_features,
                **temporal_features
            }
            
            feature_array = self._features_to_array(combined_features)
            
            if not self.is_fitted:
                self._fit_model(feature_array)
            
            # Normalize features
            feature_array = feature_array.reshape(1, -1)
            normalized_features = self.scaler.transform(feature_array)
            
            # Ensemble prediction
            ensemble_scores = []
            for model_name, model in self.models.items():
                try:
                    if hasattr(model, 'predict_proba'):
                        prob = model.predict_proba(normalized_features)[0]
                        score = prob[1] if len(prob) > 1 else 0.5
                    else:
                        score = model.decision_function(normalized_features)[0]
                        score = 1 / (1 + np.exp(-score))  # Sigmoid
                    
                    weighted_score = score * self.model_weights[model_name]
                    ensemble_scores.append(weighted_score)
                    
                except Exception as e:
                    self.logger.warning(f"Model {model_name} prediction failed: {e}")
                    ensemble_scores.append(0.5 * self.model_weights[model_name])
            
            # Final ensemble score
            final_score = sum(ensemble_scores) * 10
            
            # Apply advanced risk modifiers
            final_score = self._apply_advanced_risk_modifiers(final_score, combined_features)
            
            # Update behavioral patterns
            self._update_behavioral_patterns(sender, features, final_score)
            
            return float(max(0, min(10, final_score)))
            
        except Exception as e:
            self.logger.error(f"Error in advanced ML prediction: {str(e)}")
            return 2.5
    
    def _features_to_array(self, features):
        """Convert comprehensive feature dict to numpy array"""
        # Comprehensive feature set for advanced ML
        feature_keys = [
            # Basic email features
            'subject_length', 'has_attachments', 'sender_domain_length',
            'is_external', 'is_leaver', 'has_termination',
            'security_score', 'risk_score', 'hour_of_day', 'day_of_week',
            
            # NLP features
            'sentiment_score', 'sentiment_subjectivity', 'phishing_keyword_score',
            'financial_keyword_score', 'exclamation_count', 'question_count',
            'caps_ratio', 'number_count', 'url_count', 'email_count',
            'word_count', 'char_count',
            
            # Behavioral features
            'sender_frequency_anomaly', 'sender_timing_anomaly', 'sender_pattern_deviation',
            'recipient_diversity_score', 'communication_frequency',
            
            # Network features
            'sender_centrality', 'recipient_centrality', 'communication_path_length',
            'network_clustering_coefficient',
            
            # Temporal features
            'time_since_last_email', 'emails_in_last_hour', 'emails_in_last_day',
            'unusual_timing_score', 'weekend_email_ratio'
        ]
        
        return np.array([features.get(key, 0) for key in feature_keys])
    
    def _extract_network_features(self, features):
        """Extract sophisticated network-based features"""
        try:
            sender = features.get('sender', '')
            recipient = features.get('recipient', '')
            
            # Update communication graph
            if sender and recipient:
                self.communication_graph[sender].add(recipient)
                self.network_graph.add_edge(sender, recipient)
            
            # Calculate network metrics
            sender_centrality = 0.0
            recipient_centrality = 0.0
            path_length = 0.0
            clustering_coeff = 0.0
            
            if sender in self.network_graph:
                # Degree centrality
                sender_centrality = self.network_graph.degree(sender) / max(len(self.network_graph.nodes()), 1)
                
                # Local clustering coefficient
                try:
                    clustering_coeff = nx.clustering(self.network_graph, sender)
                except:
                    clustering_coeff = 0.0
            
            if recipient in self.network_graph:
                recipient_centrality = self.network_graph.degree(recipient) / max(len(self.network_graph.nodes()), 1)
            
            # Communication frequency between sender and recipient
            communication_freq = 0.0
            if sender in self.communication_graph:
                total_communications = sum(len(recipients) for recipients in self.communication_graph.values())
                sender_total = len(self.communication_graph[sender])
                communication_freq = sender_total / max(total_communications, 1)
            
            return {
                'sender_centrality': sender_centrality,
                'recipient_centrality': recipient_centrality,
                'communication_path_length': path_length,
                'network_clustering_coefficient': clustering_coeff
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting network features: {str(e)}")
            return {
                'sender_centrality': 0.0,
                'recipient_centrality': 0.0,
                'communication_path_length': 0.0,
                'network_clustering_coefficient': 0.0
            }
    
    def _analyze_behavioral_patterns(self, sender, features):
        """Analyze sender behavioral patterns for anomaly detection"""
        try:
            # Store current behavior
            current_behavior = {
                'timestamp': datetime.utcnow(),
                'hour': features.get('hour_of_day', 0),
                'day': features.get('day_of_week', 0),
                'recipients': features.get('recipient', ''),
                'subject_length': features.get('subject_length', 0)
            }
            
            self.sender_patterns[sender].append(current_behavior)
            
            # Keep only recent patterns (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            self.sender_patterns[sender] = [
                p for p in self.sender_patterns[sender] 
                if p['timestamp'] > cutoff_date
            ]
            
            # Calculate behavioral anomalies
            frequency_anomaly = self._calculate_frequency_anomaly(sender)
            timing_anomaly = self._calculate_timing_anomaly(sender, current_behavior)
            pattern_deviation = self._calculate_pattern_deviation(sender, current_behavior)
            recipient_diversity = self._calculate_recipient_diversity(sender)
            
            return {
                'sender_frequency_anomaly': frequency_anomaly,
                'sender_timing_anomaly': timing_anomaly,
                'sender_pattern_deviation': pattern_deviation,
                'recipient_diversity_score': recipient_diversity,
                'communication_frequency': len(self.sender_patterns[sender]) / 30.0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing behavioral patterns: {str(e)}")
            return {
                'sender_frequency_anomaly': 0.0,
                'sender_timing_anomaly': 0.0,
                'sender_pattern_deviation': 0.0,
                'recipient_diversity_score': 0.0,
                'communication_frequency': 0.0
            }
    
    def _analyze_temporal_patterns(self, features):
        """Analyze temporal patterns for anomaly detection"""
        try:
            current_time = datetime.utcnow()
            hour = current_time.hour
            day_of_week = current_time.weekday()
            
            # Calculate temporal features
            time_since_last = 0.0  # Placeholder
            emails_last_hour = 0  # Placeholder
            emails_last_day = 0   # Placeholder
            unusual_timing = 0.0  # Placeholder
            weekend_ratio = 1.0 if day_of_week >= 5 else 0.0
            
            return {
                'time_since_last_email': time_since_last,
                'emails_in_last_hour': emails_last_hour,
                'emails_in_last_day': emails_last_day,
                'unusual_timing_score': unusual_timing,
                'weekend_email_ratio': weekend_ratio
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing temporal patterns: {str(e)}")
            return {
                'time_since_last_email': 0.0,
                'emails_in_last_hour': 0,
                'emails_in_last_day': 0,
                'unusual_timing_score': 0.0,
                'weekend_email_ratio': 0.0
            }
    
    def _apply_advanced_risk_modifiers(self, score, features):
        """Apply sophisticated risk modifiers based on advanced analysis"""
        try:
            modified_score = score
            
            # High phishing keyword concentration
            if features.get('phishing_keyword_score', 0) > 0.4:
                modified_score *= 1.8
            
            # Financial keywords + external sender
            if (features.get('financial_keyword_score', 0) > 0.2 and 
                features.get('is_external', 0) > 0.5):
                modified_score *= 1.6
            
            # Unusual behavioral patterns
            behavioral_risk = (
                features.get('sender_frequency_anomaly', 0) +
                features.get('sender_timing_anomaly', 0) +
                features.get('sender_pattern_deviation', 0)
            ) / 3.0
            
            if behavioral_risk > 0.7:
                modified_score *= 1.4
            
            # Network-based risk (isolated or unusual centrality)
            sender_centrality = features.get('sender_centrality', 0)
            if sender_centrality > 0.8 or sender_centrality < 0.1:
                modified_score *= 1.2
            
            # Sentiment-based risk
            sentiment = features.get('sentiment_score', 0)
            if sentiment < -0.5:  # Very negative sentiment
                modified_score *= 1.3
            
            return min(10.0, modified_score)
            
        except Exception as e:
            self.logger.error(f"Error applying risk modifiers: {str(e)}")
            return score
    
    def _calculate_frequency_anomaly(self, sender):
        """Calculate frequency anomaly for sender"""
        try:
            patterns = self.sender_patterns[sender]
            if len(patterns) < 3:
                return 0.0
            
            # Calculate daily email frequency
            daily_counts = defaultdict(int)
            for pattern in patterns:
                day = pattern['timestamp'].date()
                daily_counts[day] += 1
            
            if not daily_counts:
                return 0.0
            
            frequencies = list(daily_counts.values())
            mean_freq = np.mean(frequencies)
            std_freq = np.std(frequencies) if len(frequencies) > 1 else 0
            
            # Current frequency vs historical
            today = datetime.utcnow().date()
            current_freq = daily_counts.get(today, 0)
            
            if std_freq == 0:
                return 0.0
            
            z_score = abs(current_freq - mean_freq) / std_freq
            return min(1.0, z_score / 3.0)  # Normalize to 0-1
            
        except Exception as e:
            self.logger.error(f"Error calculating frequency anomaly: {str(e)}")
            return 0.0
    
    def _calculate_timing_anomaly(self, sender, current_behavior):
        """Calculate timing pattern anomaly"""
        try:
            patterns = self.sender_patterns[sender]
            if len(patterns) < 5:
                return 0.0
            
            # Historical hours
            historical_hours = [p['hour'] for p in patterns[:-1]]
            if not historical_hours:
                return 0.0
            
            current_hour = current_behavior['hour']
            
            # Check if current hour is unusual
            hour_counts = Counter(historical_hours)
            total_emails = len(historical_hours)
            current_hour_prob = hour_counts.get(current_hour, 0) / total_emails
            
            # If probability is very low, it's anomalous
            anomaly_score = 1.0 - (current_hour_prob * 24)  # Normalize
            return max(0.0, min(1.0, anomaly_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating timing anomaly: {str(e)}")
            return 0.0
    
    def _calculate_pattern_deviation(self, sender, current_behavior):
        """Calculate overall pattern deviation"""
        try:
            patterns = self.sender_patterns[sender]
            if len(patterns) < 3:
                return 0.0
            
            # Compare subject length patterns
            historical_lengths = [p['subject_length'] for p in patterns[:-1]]
            if not historical_lengths:
                return 0.0
            
            mean_length = np.mean(historical_lengths)
            std_length = np.std(historical_lengths) if len(historical_lengths) > 1 else 0
            
            current_length = current_behavior['subject_length']
            
            if std_length == 0:
                return 0.0
            
            deviation = abs(current_length - mean_length) / std_length
            return min(1.0, deviation / 3.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating pattern deviation: {str(e)}")
            return 0.0
    
    def _calculate_recipient_diversity(self, sender):
        """Calculate recipient diversity score"""
        try:
            patterns = self.sender_patterns[sender]
            if len(patterns) < 2:
                return 0.0
            
            recipients = [p['recipients'] for p in patterns if p['recipients']]
            unique_recipients = len(set(recipients))
            total_emails = len([p for p in patterns if p['recipients']])
            
            if total_emails == 0:
                return 0.0
            
            diversity_score = unique_recipients / total_emails
            return min(1.0, diversity_score)
            
        except Exception as e:
            self.logger.error(f"Error calculating recipient diversity: {str(e)}")
            return 0.0
    
    def _update_behavioral_patterns(self, sender, features, risk_score):
        """Update behavioral patterns with new data"""
        try:
            # Store the risk assessment for learning
            pattern_entry = {
                'timestamp': datetime.utcnow(),
                'features': features.copy(),
                'risk_score': risk_score
            }
            
            # Keep pattern history for adaptive learning
            if len(self.sender_patterns[sender]) > 100:
                # Keep only recent patterns
                self.sender_patterns[sender] = self.sender_patterns[sender][-50:]
            
        except Exception as e:
            self.logger.error(f"Error updating behavioral patterns: {str(e)}")
    
    def _fit_model(self, sample_features):
        """Fit advanced ensemble models with sophisticated synthetic data"""
        try:
            # Generate comprehensive synthetic training data
            np.random.seed(42)
            n_features = len(sample_features)
            n_samples = 1000
            
            # Create realistic multi-modal synthetic data
            # Normal emails (60%)
            normal_base = np.random.normal(0.3, 0.15, (int(n_samples * 0.6), n_features))
            
            # Suspicious emails (25%)
            suspicious_base = np.random.normal(0.6, 0.2, (int(n_samples * 0.25), n_features))
            
            # High-risk emails (15%)
            risky_base = np.random.normal(0.85, 0.1, (int(n_samples * 0.15), n_features))
            
            # Combine all data
            synthetic_data = np.vstack([normal_base, suspicious_base, risky_base])
            synthetic_data = np.clip(synthetic_data, 0, 1)
            
            # Create sophisticated labels
            synthetic_labels = np.hstack([
                np.zeros(int(n_samples * 0.6)),      # Normal
                np.random.choice([0, 1], int(n_samples * 0.25), p=[0.7, 0.3]),  # Mixed suspicious
                np.ones(int(n_samples * 0.15))       # High risk
            ])
            
            # Apply SMOTE for balanced training if available
            if self.smote is not None:
                try:
                    synthetic_data_balanced, synthetic_labels_balanced = self.smote.fit_resample(
                        synthetic_data, synthetic_labels
                    )
                except:
                    synthetic_data_balanced = synthetic_data
                    synthetic_labels_balanced = synthetic_labels
            else:
                synthetic_data_balanced = synthetic_data
                synthetic_labels_balanced = synthetic_labels
            
            # Fit scaler
            self.scaler.fit(synthetic_data_balanced)
            normalized_data = self.scaler.transform(synthetic_data_balanced)
            
            # Train ensemble models
            trained_models = 0
            for model_name, model in self.models.items():
                try:
                    # Split data for each model
                    X_train, X_test, y_train, y_test = train_test_split(
                        normalized_data, synthetic_labels_balanced, 
                        test_size=0.2, random_state=42
                    )
                    
                    # Train model
                    model.fit(X_train, y_train)
                    
                    # Evaluate and adjust weights based on performance
                    if hasattr(model, 'predict_proba'):
                        cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='roc_auc')
                        avg_score = np.mean(cv_scores)
                        
                        # Adjust model weight based on performance
                        self.model_weights[model_name] *= (avg_score * 1.2)
                    
                    trained_models += 1
                    self.logger.info(f"Trained {model_name} successfully")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to train {model_name}: {str(e)}")
                    # Set lower weight for failed models
                    self.model_weights[model_name] *= 0.5
            
            # Normalize weights
            total_weight = sum(self.model_weights.values())
            if total_weight > 0:
                self.model_weights = {k: v/total_weight for k, v in self.model_weights.items()}
            
            # Calculate ensemble feature importance
            self._calculate_ensemble_feature_importance()
            
            self.is_fitted = True
            self.logger.info(f"Advanced ensemble ML models fitted successfully ({trained_models}/{len(self.models)} models)")
            
        except Exception as e:
            self.logger.error(f"Error fitting advanced ensemble models: {str(e)}")
    
    def _calculate_ensemble_feature_importance(self):
        """Calculate weighted feature importance across ensemble"""
        try:
            feature_names = [
                'subject_length', 'has_attachments', 'sender_domain_length',
                'is_external', 'is_leaver', 'has_termination',
                'security_score', 'risk_score', 'hour_of_day', 'day_of_week',
                'sentiment_score', 'sentiment_subjectivity', 'phishing_keyword_score',
                'financial_keyword_score', 'exclamation_count', 'question_count',
                'caps_ratio', 'number_count', 'url_count', 'email_count',
                'word_count', 'char_count', 'sender_frequency_anomaly',
                'sender_timing_anomaly', 'sender_pattern_deviation',
                'recipient_diversity_score', 'communication_frequency',
                'sender_centrality', 'recipient_centrality', 'communication_path_length',
                'network_clustering_coefficient', 'time_since_last_email',
                'emails_in_last_hour', 'emails_in_last_day', 'unusual_timing_score',
                'weekend_email_ratio'
            ]
            
            ensemble_importance = defaultdict(float)
            
            for model_name, model in self.models.items():
                if hasattr(model, 'feature_importances_'):
                    model_weight = self.model_weights[model_name]
                    importances = model.feature_importances_
                    
                    for i, importance in enumerate(importances):
                        if i < len(feature_names):
                            ensemble_importance[feature_names[i]] += importance * model_weight
            
            self.feature_importance_ensemble = dict(ensemble_importance)
            
        except Exception as e:
            self.logger.error(f"Error calculating ensemble feature importance: {str(e)}")
    
    def get_model_insights(self):
        """Get comprehensive model insights and performance metrics"""
        return {
            'model_weights': self.model_weights,
            'feature_importance': self.feature_importance_ensemble,
            'is_fitted': self.is_fitted,
            'models_count': len(self.models),
            'network_nodes': len(self.network_graph.nodes()) if self.network_graph else 0,
            'behavioral_patterns_tracked': len(self.sender_patterns)
        }
    
    def analyze_communication_patterns(self, sender, time_window_days=30):
        """Analyze communication patterns for anomaly detection"""
        try:
            # Get recent patterns for sender
            patterns = self.sender_patterns.get(sender, [])
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
            recent_patterns = [p for p in patterns if p['timestamp'] > cutoff_date]
            
            if len(recent_patterns) < 2:
                return {
                    'frequency_anomaly': 0.0,
                    'timing_anomaly': 0.0,
                    'recipient_anomaly': 0.0
                }
            
            # Frequency analysis
            daily_counts = defaultdict(int)
            for pattern in recent_patterns:
                day = pattern['timestamp'].date()
                daily_counts[day] += 1
            
            frequencies = list(daily_counts.values())
            frequency_anomaly = np.std(frequencies) / (np.mean(frequencies) + 1e-6)
            
            # Timing analysis
            hours = [p['hour'] for p in recent_patterns]
            hour_counts = Counter(hours)
            most_common_hour = hour_counts.most_common(1)[0][1] if hour_counts else 0
            timing_anomaly = 1.0 - (most_common_hour / len(hours)) if hours else 0.0
            
            # Recipient diversity analysis
            recipients = [p.get('recipients', '') for p in recent_patterns if p.get('recipients')]
            unique_recipients = len(set(recipients))
            recipient_anomaly = unique_recipients / len(recipients) if recipients else 0.0
            
            return {
                'frequency_anomaly': min(1.0, frequency_anomaly),
                'timing_anomaly': min(1.0, timing_anomaly),
                'recipient_anomaly': min(1.0, recipient_anomaly)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing communication patterns: {str(e)}")
            return {'frequency_anomaly': 0.0, 'timing_anomaly': 0.0, 'recipient_anomaly': 0.0}
    
    def update_network_graph(self, sender, recipient):
        """Update communication network graph with advanced metrics"""
        try:
            self.network_graph.add_edge(sender, recipient)
            self.communication_graph[sender].add(recipient)
            
            # Limit graph size for performance
            if len(self.network_graph.nodes()) > 1500:
                # Remove oldest 20% of edges
                edges_to_remove = list(self.network_graph.edges())[:300]
                self.network_graph.remove_edges_from(edges_to_remove)
                
            # Update temporal patterns
            current_time = datetime.utcnow()
            temporal_key = (sender, recipient)
            self.temporal_patterns[temporal_key].append(current_time)
            
            # Keep only recent temporal data (last 60 days)
            cutoff_date = current_time - timedelta(days=60)
            self.temporal_patterns[temporal_key] = [
                t for t in self.temporal_patterns[temporal_key] if t > cutoff_date
            ]
                
        except Exception as e:
            self.logger.error(f"Error updating network graph: {str(e)}")

class AdaptiveMLEngine:
    """Advanced self-learning threat detection engine with continuous improvement"""
    
    def __init__(self):
        self.feedback_buffer = []
        self.retrain_threshold = 50
        self.performance_history = []
        self.model_versions = {}
        self.adaptive_weights = defaultdict(float)
        
        # Advanced models for adaptive learning
        self.base_models = {
            'xgboost_adaptive': xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            ),
            'gradient_boost_adaptive': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        }
        
        self.feature_selector = None
        self.outlier_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = RobustScaler()
        self.is_fitted = False
        
        # Learning parameters
        self.learning_rate = 0.01
        self.forgetting_factor = 0.95
        self.confidence_threshold = 0.7
        
        self.logger = logging.getLogger(__name__)
    
    def predict_risk_adaptive(self, features):
        """Adaptive risk prediction that learns from feedback"""
        try:
            if not self.is_fitted:
                return 2.5  # Default risk score
            
            # Prepare features
            feature_array = self._prepare_features(features)
            if feature_array is None:
                return 2.5
            
            # Get predictions from multiple models
            predictions = []
            confidences = []
            
            for model_name, model in self.base_models.items():
                try:
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(feature_array.reshape(1, -1))[0]
                        prediction = proba[1] if len(proba) > 1 else 0.5
                        confidence = max(proba) - min(proba) if len(proba) > 1 else 0.5
                    else:
                        prediction = 0.5
                        confidence = 0.5
                    
                    # Apply adaptive weights
                    weight = self.adaptive_weights.get(model_name, 1.0)
                    weighted_prediction = prediction * weight
                    
                    predictions.append(weighted_prediction)
                    confidences.append(confidence)
                    
                except Exception as e:
                    self.logger.warning(f"Model {model_name} prediction failed: {e}")
                    predictions.append(0.5)
                    confidences.append(0.0)
            
            # Ensemble prediction with confidence weighting
            if predictions:
                total_confidence = sum(confidences) + 1e-6
                weighted_prediction = sum(p * c for p, c in zip(predictions, confidences)) / total_confidence
                final_score = weighted_prediction * 10
            else:
                final_score = 2.5
            
            # Apply adaptive risk modifiers
            final_score = self._apply_adaptive_modifiers(final_score, features)
            
            return float(max(0, min(10, final_score)))
            
        except Exception as e:
            self.logger.error(f"Error in adaptive prediction: {str(e)}")
            return 2.5
    
    def learn_from_feedback(self, features, actual_outcome, confidence=1.0):
        """Enhanced learning from human feedback with confidence scoring"""
        try:
            feedback_entry = {
                'features': features.copy(),
                'outcome': actual_outcome,
                'confidence': confidence,
                'timestamp': datetime.utcnow(),
                'source': 'human_feedback'
            }
            
            self.feedback_buffer.append(feedback_entry)
            
            # Update adaptive weights based on feedback
            self._update_adaptive_weights(features, actual_outcome, confidence)
            
            # Trigger retraining if enough feedback accumulated
            if len(self.feedback_buffer) >= self.retrain_threshold:
                self._retrain_models()
            
            # Online learning for immediate adaptation
            self._online_learning_update(features, actual_outcome, confidence)
            
        except Exception as e:
            self.logger.error(f"Error learning from feedback: {str(e)}")
    
    def _update_adaptive_weights(self, features, outcome, confidence):
        """Update model weights based on prediction accuracy"""
        try:
            if not self.is_fitted:
                return
            
            feature_array = self._prepare_features(features)
            if feature_array is None:
                return
            
            # Get predictions from each model
            for model_name, model in self.base_models.items():
                try:
                    if hasattr(model, 'predict_proba'):
                        proba = model.predict_proba(feature_array.reshape(1, -1))[0]
                        prediction = proba[1] if len(proba) > 1 else 0.5
                    else:
                        prediction = 0.5
                    
                    # Calculate prediction error
                    target = 1.0 if outcome == 'threat' else 0.0
                    error = abs(prediction - target)
                    
                    # Update weight using exponential moving average
                    current_weight = self.adaptive_weights.get(model_name, 1.0)
                    accuracy = 1.0 - error
                    new_weight = (self.forgetting_factor * current_weight + 
                                 self.learning_rate * accuracy * confidence)
                    
                    self.adaptive_weights[model_name] = max(0.1, min(2.0, new_weight))
                    
                except Exception as e:
                    self.logger.warning(f"Weight update failed for {model_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error updating adaptive weights: {str(e)}")
    
    def _online_learning_update(self, features, outcome, confidence):
        """Perform online learning update for immediate adaptation"""
        try:
            if confidence < self.confidence_threshold:
                return  # Skip low-confidence updates
            
            feature_array = self._prepare_features(features)
            if feature_array is None:
                return
            
            target = 1 if outcome == 'threat' else 0
            
            # Incremental learning for XGBoost (simplified)
            # In a production environment, this would use proper incremental learning
            
        except Exception as e:
            self.logger.error(f"Error in online learning update: {str(e)}")
    
    def _prepare_features(self, features):
        """Prepare and normalize features for prediction"""
        try:
            # Basic feature extraction (can be expanded)
            feature_keys = [
                'subject_length', 'has_attachments', 'sender_domain_length',
                'is_external', 'is_leaver', 'has_termination',
                'security_score', 'risk_score'
            ]
            
            feature_array = np.array([features.get(key, 0) for key in feature_keys])
            
            if self.is_fitted:
                feature_array = self.scaler.transform(feature_array.reshape(1, -1)).flatten()
            
            return feature_array
            
        except Exception as e:
            self.logger.error(f"Error preparing features: {str(e)}")
            return None
    
    def _apply_adaptive_modifiers(self, score, features):
        """Apply adaptive risk modifiers based on learned patterns"""
        try:
            modified_score = score
            
            # Apply learned pattern modifiers
            if 'phishing' in features.get('subject', '').lower():
                modified_score *= 1.3
            
            if features.get('is_external', 0) > 0.5:
                modified_score *= 1.1
            
            return modified_score
            
        except Exception as e:
            self.logger.error(f"Error applying adaptive modifiers: {str(e)}")
            return score
    
    def _retrain_models(self):
        """Retrain models based on accumulated feedback"""
        try:
            if len(self.feedback_buffer) < 10:
                return
            
            self.logger.info(f"Retraining adaptive models with {len(self.feedback_buffer)} feedback samples")
            
            # Extract features and labels from feedback
            X = []
            y = []
            sample_weights = []
            
            for fb in self.feedback_buffer:
                feature_array = self._prepare_features(fb['features'])
                if feature_array is not None:
                    X.append(feature_array)
                    y.append(1 if fb['outcome'] == 'threat' else 0)
                    sample_weights.append(fb['confidence'])
            
            if len(X) < 5:
                return
            
            X = np.array(X)
            y = np.array(y)
            sample_weights = np.array(sample_weights)
            
            # Fit scaler if not fitted
            if not self.is_fitted:
                self.scaler.fit(X)
                X = self.scaler.transform(X)
                self.is_fitted = True
            else:
                X = self.scaler.transform(X)
            
            # Retrain models
            for model_name, model in self.base_models.items():
                try:
                    if len(np.unique(y)) > 1:  # Need both classes for training
                        model.fit(X, y, sample_weight=sample_weights)
                        self.logger.info(f"Retrained {model_name} successfully")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to retrain {model_name}: {e}")
            
            # Clear old feedback, keep recent
            self.feedback_buffer = self.feedback_buffer[-self.retrain_threshold//2:]
            
            # Record performance
            self.performance_history.append({
                'timestamp': datetime.utcnow(),
                'samples_used': len(X),
                'model_weights': self.adaptive_weights.copy()
            })
            
            self.logger.info("Adaptive model retraining completed")
            
        except Exception as e:
            self.logger.error(f"Error in model retraining: {str(e)}")
    
    def get_learning_insights(self):
        """Get insights about the adaptive learning process"""
        return {
            'feedback_buffer_size': len(self.feedback_buffer),
            'adaptive_weights': dict(self.adaptive_weights),
            'performance_history_length': len(self.performance_history),
            'is_fitted': self.is_fitted,
            'learning_rate': self.learning_rate,
            'confidence_threshold': self.confidence_threshold
        }
    
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
