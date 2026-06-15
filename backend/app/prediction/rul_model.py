"""
Remaining Useful Life (RUL) Prediction Module.

This module provides:
- RUL estimation using regression models
- Degradation trend analysis
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
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import (
        mean_absolute_error, mean_squared_error, r2_score,
        mean_absolute_percentage_error
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    RandomForestRegressor = GradientBoostingRegressor = None

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None


class RULPredictor:
    """
    Machine learning model for predicting Remaining Useful Life.
    
    Estimates how many days of operation remain before equipment
    is expected to fail based on current sensor readings.
    """
    
    FEATURE_NAMES = ['temperature', 'vibration', 'current', 'pressure', 'rpm']
    MAX_RUL = 100  # Maximum RUL in days
    
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
        self.model_path = self.model_dir / "rul_model.pkl"
        self.scaler_path = self.model_dir / "rul_scaler.pkl"
        self.metrics_path = self.model_dir / "rul_metrics.json"
        
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
        Train the RUL prediction model.
        
        Args:
            X: Feature array (n_samples, n_features)
            y: Target array (n_samples,) - RUL in days
            model_type: 'random_forest', 'xgboost', or 'gradient_boosting'
            test_size: Fraction for test set
            params: Model hyperparameters
            
        Returns:
            Dictionary with training metrics
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for RUL prediction")
        
        # Clip RUL to maximum
        y = np.clip(y, 0, self.MAX_RUL)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Select and train model
        train_params = {**self.DEFAULT_PARAMS, **(params or {})}
        
        if model_type == 'xgboost' and XGBOOST_AVAILABLE:
            self.model = xgb.XGBRegressor(
                n_estimators=train_params['n_estimators'],
                max_depth=train_params['max_depth'],
                learning_rate=0.1,
                random_state=42
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(**train_params)
        else:
            self.model = RandomForestRegressor(**train_params)
        
        self.model.fit(X_train_scaled, y_train)
        self.model_type = model_type
        self.is_trained = True
        
        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        y_pred = np.clip(y_pred, 0, self.MAX_RUL)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        try:
            mape = mean_absolute_percentage_error(y_test, y_pred)
        except:
            mape = 0.0
        
        metrics = {
            'mae': float(mae),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'mape': float(mape),
            'training_samples': len(X_train),
            'test_samples': len(y_test),
            'model_type': model_type,
            'trained_at': datetime.now().isoformat()
        }
        
        # Percentile errors
        errors = np.abs(y_test - y_pred)
        metrics['error_p50'] = float(np.percentile(errors, 50))
        metrics['error_p90'] = float(np.percentile(errors, 90))
        metrics['error_p95'] = float(np.percentile(errors, 95))
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=5, scoring='neg_mean_absolute_error'
        )
        metrics['cv_mae_mean'] = float(-cv_scores.mean())
        metrics['cv_mae_std'] = float(cv_scores.std())
        
        self.metrics = metrics
        
        # Save model
        self.save_model()
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict Remaining Useful Life.
        
        Args:
            X: Feature array of shape (n_samples, n_features) or (n_features,)
            
        Returns:
            Array of RUL predictions in days
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() or load_model() first.")
        
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        return np.clip(predictions, 0, self.MAX_RUL)
    
    def get_confidence_interval(
        self, 
        X: np.ndarray, 
        confidence: float = 0.95
    ) -> Dict[str, np.ndarray]:
        """
        Get confidence intervals for predictions.
        
        Args:
            X: Feature array
            confidence: Confidence level (0-1)
            
        Returns:
            Dictionary with lower, upper bounds and predictions
        """
        if not self.is_trained:
            raise ValueError("Model not trained.")
        
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Get predictions from individual trees (for Random Forest)
        if hasattr(self.model, 'estimators_'):
            predictions = np.array([
                tree.predict(self.scaler.transform(X)) 
                for tree in self.model.estimators_
            ])
            predictions = np.clip(predictions, 0, self.MAX_RUL)
            
            # Calculate percentiles
            lower = np.percentile(predictions, (1 - confidence) / 2 * 100, axis=0)
            upper = np.percentile(predictions, (1 + confidence) / 2 * 100, axis=0)
        else:
            # Fallback: use MAE as uncertainty
            predictions = self.predict(X)
            uncertainty = self.metrics.get('mae', 5) if self.metrics else 5
            lower = np.clip(predictions - uncertainty, 0, self.MAX_RUL)
            upper = np.clip(predictions + uncertainty, 0, self.MAX_RUL)
        
        return {
            'rul': self.predict(X),
            'lower': lower,
            'upper': upper,
            'confidence': confidence
        }
    
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
            importances = np.zeros(len(self.FEATURE_NAMES))
        
        return {
            name: float(imp) 
            for name, imp in zip(self.FEATURE_NAMES, importances)
        }
    
    def explain_prediction(
        self,
        X: np.ndarray
    ) -> Dict[str, Any]:
        """
        Generate explanation for RUL prediction.
        
        Args:
            X: Feature array
            
        Returns:
            Explanation dictionary
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        rul = float(self.predict(X)[0])
        
        # Get feature importance
        importance = self.get_feature_importance()
        
        # Get feature values
        feature_values = {
            name: float(val) 
            for name, val in zip(self.FEATURE_NAMES, X[0])
        }
        
        # Analyze each feature
        analysis = []
        for name, val in feature_values.items():
            imp = importance.get(name, 0)
            
            # Determine status based on thresholds
            if name == 'temperature':
                if val > 95:
                    status = 'critical_high'
                    impact = 'severely reduces RUL'
                elif val > 85:
                    status = 'warning_high'
                    impact = 'reduces RUL'
                elif val < 40:
                    status = 'critical_low'
                    impact = 'abnormal - may affect RUL'
                elif val < 50:
                    status = 'warning_low'
                    impact = 'slightly affects RUL'
                else:
                    status = 'optimal'
                    impact = 'normal operating range'
            elif name == 'vibration':
                if val > 3.5:
                    status = 'critical_high'
                    impact = 'severely reduces RUL'
                elif val > 2.5:
                    status = 'warning_high'
                    impact = 'reduces RUL'
                else:
                    status = 'optimal'
                    impact = 'normal operating range'
            elif name == 'current':
                if val > 30:
                    status = 'critical_high'
                    impact = 'severely reduces RUL'
                elif val > 27:
                    status = 'warning_high'
                    impact = 'reduces RUL'
                else:
                    status = 'optimal'
                    impact = 'normal operating range'
            elif name == 'pressure':
                if val > 90 or val < 45:
                    status = 'critical'
                    impact = 'severely affects RUL'
                elif val > 85 or val < 55:
                    status = 'warning'
                    impact = 'affects RUL'
                else:
                    status = 'optimal'
                    impact = 'normal operating range'
            elif name == 'rpm':
                if val > 2200 or val < 800:
                    status = 'critical'
                    impact = 'severely affects RUL'
                elif val > 2000 or val < 1000:
                    status = 'warning'
                    impact = 'affects RUL'
                else:
                    status = 'optimal'
                    impact = 'normal operating range'
            else:
                status = 'optimal'
                impact = 'normal'
            
            analysis.append({
                'feature': name,
                'value': val,
                'importance': imp,
                'status': status,
                'impact': impact
            })
        
        # Sort by importance
        analysis.sort(key=lambda x: x['importance'], reverse=True)
        
        # Identify key factors
        critical_factors = [
            a['feature'] for a in analysis 
            if 'critical' in a['status']
        ]
        warning_factors = [
            a['feature'] for a in analysis 
            if 'warning' in a['status']
        ]
        
        # Generate explanation
        if critical_factors:
            explanation = f"Critical conditions detected in: {', '.join(critical_factors)}. RUL significantly affected."
        elif warning_factors:
            explanation = f"Warning conditions in: {', '.join(warning_factors)}. RUL moderately affected."
        else:
            explanation = "All parameters within optimal range. RUL prediction stable."
        
        return {
            'rul': rul,
            'explanation': explanation,
            'critical_factors': critical_factors,
            'warning_factors': warning_factors,
            'feature_analysis': analysis
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
                    'max_rul': self.MAX_RUL,
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


def create_synthetic_rul_data(n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create synthetic RUL data for training.
    """
    np.random.seed(42)
    
    X = []
    y = []
    
    for i in range(n_samples):
        # Generate random sensor values
        temp = np.random.normal(75, 15)
        vib = np.random.normal(1.5, 0.6)
        curr = np.random.normal(20, 4)
        press = np.random.normal(70, 10)
        rpm_val = np.random.normal(1500, 300)
        
        # Calculate RUL based on conditions
        rul = 60  # Base RUL
        
        # Temperature effect
        if temp > 100:
            rul -= 40
        elif temp > 90:
            rul -= 25
        elif temp > 85:
            rul -= 15
        
        # Vibration effect
        if vib > 3.5:
            rul -= 35
        elif vib > 3.0:
            rul -= 20
        elif vib > 2.5:
            rul -= 10
        
        # Current effect
        if curr > 30:
            rul -= 20
        elif curr > 27:
            rul -= 10
        
        # Pressure effect
        if press > 90 or press < 45:
            rul -= 25
        elif press > 85 or press < 55:
            rul -= 10
        
        # RPM effect
        if rpm_val > 2200 or rpm_val < 800:
            rul -= 20
        elif rpm_val > 2000 or rpm_val < 1000:
            rul -= 10
        
        # Add noise
        rul += np.random.normal(0, 5)
        
        # Clip to valid range
        rul = max(1, min(100, rul))
        
        X.append([temp, vib, curr, press, rpm_val])
        y.append(rul)
    
    return np.array(X), np.array(y)


# Singleton instance
_rul_predictor: Optional[RULPredictor] = None


def get_rul_predictor() -> RULPredictor:
    """Get or create global RUL predictor instance."""
    global _rul_predictor
    if _rul_predictor is None:
        _rul_predictor = RULPredictor()
        _rul_predictor.load_model()
    return _rul_predictor


def train_initial_rul_model():
    """Train initial RUL model with synthetic data."""
    predictor = get_rul_predictor()
    
    if not predictor.is_trained:
        X, y = create_synthetic_rul_data(2000)
        metrics = predictor.train(X, y, model_type='random_forest')
        print(f"Initial RUL model trained: {metrics}")
        return metrics
    
    return None