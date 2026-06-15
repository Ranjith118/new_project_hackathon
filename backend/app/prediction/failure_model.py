"""
Failure Prediction Module using Machine Learning.

This module provides:
- Failure probability prediction using ensemble methods
- Feature importance analysis
- Model persistence and loading
"""
import os
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        classification_report, confusion_matrix, roc_auc_score
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestClassifier = GradientBoostingClassifier = None

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None


class FailurePredictor:
    """
    Machine learning model for predicting equipment failures.
    
    Uses ensemble methods (Random Forest, XGBoost) to predict
    the probability of failure based on sensor readings.
    """
    
    FEATURE_NAMES = ['temperature', 'vibration', 'current', 'pressure', 'rpm']
    
    DEFAULT_PARAMS = {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42,
        'n_jobs': -1
    }
    
    def __init__(self, model_dir: str = "./models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.model_dir / "failure_model.pkl"
        self.scaler_path = self.model_dir / "failure_scaler.pkl"
        self.metrics_path = self.model_dir / "failure_metrics.json"
        
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.model_type = None
        self.is_trained = False
        self.metrics = None
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_type: str = 'random_forest',
        test_size: float = 0.2,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Train the failure prediction model.
        
        Args:
            X: Feature array (n_samples, n_features)
            y: Target array (n_samples,)
            model_type: 'random_forest', 'xgboost', or 'gradient_boosting'
            test_size: Fraction for test set
            params: Model hyperparameters
            
        Returns:
            Dictionary with training metrics
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for failure prediction")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Select and train model
        train_params = {**self.DEFAULT_PARAMS, **(params or {})}
        
        if model_type == 'xgboost' and XGBOOST_AVAILABLE:
            self.model = xgb.XGBClassifier(
                n_estimators=train_params['n_estimators'],
                max_depth=train_params['max_depth'],
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(**train_params)
        else:
            self.model = RandomForestClassifier(**train_params)
        
        self.model.fit(X_train_scaled, y_train)
        self.model_type = model_type
        self.is_trained = True
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred)),
            'recall': float(recall_score(y_test, y_pred)),
            'f1_score': float(f1_score(y_test, y_pred)),
            'roc_auc': float(roc_auc_score(y_test, y_pred_proba)),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'model_type': model_type,
            'trained_at': datetime.now().isoformat()
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        metrics['confusion_matrix'] = {
            'true_negative': int(cm[0][0]),
            'false_positive': int(cm[0][1]),
            'false_negative': int(cm[1][0]),
            'true_positive': int(cm[1][1])
        }
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='f1')
        metrics['cv_f1_mean'] = float(cv_scores.mean())
        metrics['cv_f1_std'] = float(cv_scores.std())
        
        self.metrics = metrics
        
        # Save model
        self.save_model()
        
        return metrics
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict failure probability.
        
        Args:
            X: Feature array of shape (n_samples, n_features) or (n_features,)
            
        Returns:
            Array of failure probabilities
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() or load_model() first.")
        
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict failure (binary).
        
        Args:
            X: Feature array
            
        Returns:
            Array of binary predictions (0 or 1)
        """
        if not self.is_trained:
            raise ValueError("Model not trained.")
        
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores.
        
        Returns:
            Dictionary of feature importance scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained.")
        
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
        else:
            # For models without feature_importances_
            importances = np.zeros(len(self.FEATURE_NAMES))
        
        return {
            name: float(imp) 
            for name, imp in zip(self.FEATURE_NAMES, importances)
        }
    
    def explain_prediction(
        self,
        X: np.ndarray,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Generate explanation for prediction.
        
        Args:
            X: Feature array
            threshold: Decision threshold
            
        Returns:
            Explanation dictionary with contributing factors
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        proba = self.predict_proba(X)[0]
        prediction = int(proba >= threshold)
        
        # Get feature importance
        importance = self.get_feature_importance()
        
        # Get feature values
        feature_values = {
            name: float(val) 
            for name, val in zip(self.FEATURE_NAMES, X[0])
        }
        
        # Calculate individual feature contributions (simplified)
        contributions = []
        for name, imp in importance.items():
            val = feature_values[name]
            
            # Determine if this feature contributes to failure risk
            if name == 'temperature' and val > 85:
                contribution = 'high'
            elif name == 'vibration' and val > 2.5:
                contribution = 'high'
            elif name == 'current' and val > 25:
                contribution = 'high'
            elif name == 'pressure' and (val < 55 or val > 85):
                contribution = 'high'
            elif name == 'rpm' and (val < 1000 or val > 2000):
                contribution = 'high'
            else:
                contribution = 'normal'
            
            contributions.append({
                'feature': name,
                'value': val,
                'importance': imp,
                'status': contribution
            })
        
        # Sort by importance
        contributions.sort(key=lambda x: x['importance'], reverse=True)
        
        # Identify contributing factors
        contributing_factors = [
            c['feature'] for c in contributions 
            if c['status'] == 'high' and c['importance'] > 0.1
        ]
        
        # Generate reason
        if prediction == 1:
            reason = f"High failure probability due to: {', '.join(contributing_factors)}"
        else:
            reason = "All parameters within acceptable ranges"
        
        # Confidence based on probability distance from threshold
        confidence = abs(proba - 0.5) * 2
        confidence = min(1.0, max(0.0, confidence))
        
        return {
            'prediction': prediction,
            'failure_probability': float(proba),
            'confidence': float(confidence),
            'reason': reason,
            'contributing_factors': contributing_factors,
            'feature_analysis': contributions
        }
    
    def save_model(self) -> Dict[str, str]:
        """Save trained model to disk."""
        paths = {}
        
        if self.model is not None:
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'model_type': self.model_type,
                    'feature_names': self.FEATURE_NAMES,
                    'trained_at': datetime.now().isoformat()
                }, f)
            paths['model'] = str(self.model_path)
        
        if self.scaler is not None:
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            paths['scaler'] = str(self.scaler_path)
        
        if self.metrics is not None:
            with open(self.metrics_path, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            paths['metrics'] = str(self.metrics_path)
        
        return paths
    
    def load_model(self) -> bool:
        """Load model from disk."""
        if not self.model_path.exists():
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.model_type = data.get('model_type')
            self.is_trained = True
            
            # Load scaler
            if self.scaler_path.exists():
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Load metrics
            if self.metrics_path.exists():
                with open(self.metrics_path, 'r') as f:
                    self.metrics = json.load(f)
            
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get training metrics."""
        return self.metrics


def create_synthetic_failure_data(n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create synthetic failure data for training.
    
    Simulates equipment failure patterns in steel plant.
    """
    np.random.seed(42)
    
    X = []
    y = []
    
    for i in range(n_samples):
        # Normal operating conditions
        temp = np.random.normal(75, 15)
        vib = np.random.normal(1.5, 0.6)
        curr = np.random.normal(20, 4)
        press = np.random.normal(70, 10)
        rpm_val = np.random.normal(1500, 300)
        
        # Determine failure based on conditions
        failure_score = 0
        
        if temp > 100 or temp < 30:
            failure_score += 3
        elif temp > 90 or temp < 40:
            failure_score += 2
        elif temp > 85 or temp < 50:
            failure_score += 1
        
        if vib > 3.5 or vib < 0.5:
            failure_score += 3
        elif vib > 3.0 or vib < 0.8:
            failure_score += 2
        elif vib > 2.5:
            failure_score += 1
        
        if curr > 30 or curr < 10:
            failure_score += 2
        elif curr > 27:
            failure_score += 1
        
        if press > 90 or press < 45:
            failure_score += 2
        elif press > 85 or press < 55:
            failure_score += 1
        
        if rpm_val > 2200 or rpm_val < 800:
            failure_score += 2
        elif rpm_val > 2000 or rpm_val < 1000:
            failure_score += 1
        
        # Add some randomness
        failure_score += np.random.normal(0, 1)
        
        failure = 1 if failure_score > 5 else 0
        
        X.append([temp, vib, curr, press, rpm_val])
        y.append(failure)
    
    return np.array(X), np.array(y)


# Singleton instance
_failure_predictor: Optional[FailurePredictor] = None


def get_failure_predictor() -> FailurePredictor:
    """Get or create global failure predictor instance."""
    global _failure_predictor
    if _failure_predictor is None:
        _failure_predictor = FailurePredictor()
        _failure_predictor.load_model()
    return _failure_predictor


def train_initial_failure_model():
    """Train initial failure model with synthetic data."""
    predictor = get_failure_predictor()
    
    if not predictor.is_trained:
        X, y = create_synthetic_failure_data(2000)
        metrics = predictor.train(X, y, model_type='random_forest')
        print(f"Initial failure model trained: {metrics}")
        return metrics
    
    return None