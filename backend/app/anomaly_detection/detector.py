"""Anomaly Detection Module using Isolation Forest."""
import os
import json
import pickle
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    IsolationForest = StandardScaler = None


class SensorPreprocessor:
    """
    Data preprocessing pipeline for sensor data.
    
    Handles:
    - Missing value imputation
    - Feature scaling (StandardScaler)
    - Data validation
    """
    
    FEATURE_NAMES = ['temperature', 'vibration', 'current', 'pressure', 'rpm']
    DEFAULT_THRESHOLDS = {
        'temperature': {'min': 20, 'max': 120, 'optimal': 80},
        'vibration': {'min': 0, 'max': 5, 'optimal': 1.5},
        'current': {'min': 5, 'max': 35, 'optimal': 20},
        'pressure': {'min': 40, 'max': 100, 'optimal': 70},
        'rpm': {'min': 500, 'max': 2500, 'optimal': 1500}
    }
    
    def __init__(self, model_dir: str = "./models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.scaler_path = self.model_dir / "scaler.pkl"
        self.is_fitted = False
    
    def fit(self, data: np.ndarray) -> 'SensorPreprocessor':
        """
        Fit the preprocessor on training data.
        
        Args:
            data: numpy array of shape (n_samples, n_features)
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for preprocessing")
        
        self.scaler.fit(data)
        self.is_fitted = True
        self._save_scaler()
        return self
    
    def transform(self, data: np.ndarray) -> np.ndarray:
        """Transform data using fitted scaler."""
        if not self.is_fitted:
            raise ValueError("Preprocessor not fitted. Call fit() first.")
        return self.scaler.transform(data)
    
    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(data)
        return self.transform(data)
    
    def inverse_transform(self, data: np.ndarray) -> np.ndarray:
        """Inverse transform scaled data back to original scale."""
        if not self.is_fitted:
            raise ValueError("Preprocessor not fitted. Call fit() first.")
        return self.scaler.inverse_transform(data)
    
    def handle_missing_values(self, data: np.ndarray, strategy: str = 'mean') -> np.ndarray:
        """
        Handle missing values in the data.
        
        Args:
            data: numpy array with potential NaN values
            strategy: 'mean', 'median', or 'zero'
        """
        result = data.copy()
        
        for i in range(result.shape[1]):
            col = result[:, i]
            mask = np.isnan(col)
            
            if mask.any():
                if strategy == 'mean':
                    fill_value = np.nanmean(col)
                elif strategy == 'median':
                    fill_value = np.nanmedian(col)
                else:  # zero
                    fill_value = 0
                
                result[mask, i] = fill_value
        
        return result
    
    def validate_reading(self, reading: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate a sensor reading against thresholds.
        
        Args:
            reading: Dictionary with sensor values
            
        Returns:
            Tuple of (is_valid, list of warnings)
        """
        warnings = []
        thresholds = self.DEFAULT_THRESHOLDS
        
        for feature in self.FEATURE_NAMES:
            if feature not in reading:
                warnings.append(f"Missing {feature}")
                continue
            
            value = reading[feature]
            threshold = thresholds.get(feature, {})
            
            if value < threshold.get('min', float('-inf')):
                warnings.append(f"{feature} below minimum ({value} < {threshold['min']})")
            elif value > threshold.get('max', float('inf')):
                warnings.append(f"{feature} above maximum ({value} > {threshold['max']})")
        
        return len(warnings) == 0, warnings
    
    def _save_scaler(self):
        """Save fitted scaler to disk."""
        if self.scaler and self.scaler_path:
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
    
    def load_scaler(self) -> bool:
        """Load scaler from disk."""
        if not self.scaler_path.exists():
            return False
        
        try:
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            self.is_fitted = True
            return True
        except Exception:
            return False


class AnomalyDetector:
    """
    Isolation Forest-based anomaly detector for equipment sensor data.
    
    Features:
    - Training on historical data
    - Real-time anomaly prediction
    - Model persistence
    - Contamination tuning
    """
    
    DEFAULT_PARAMS = {
        'n_estimators': 100,
        'max_samples': 'auto',
        'contamination': 0.1,
        'max_features': 1.0,
        'bootstrap': False,
        'random_state': 42,
        'n_jobs': -1
    }
    
    def __init__(self, model_dir: str = "./models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.model_dir / "isolation_forest.pkl"
        self.model = None
        self.is_trained = False
        self.feature_names = SensorPreprocessor.FEATURE_NAMES
    
    def train(
        self,
        data: np.ndarray,
        params: Optional[Dict[str, Any]] = None,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train the Isolation Forest model.
        
        Args:
            data: Training data array of shape (n_samples, n_features)
            params: Model hyperparameters
            test_size: Fraction of data for testing
            
        Returns:
            Dictionary with training metrics
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for anomaly detection")
        
        # Use default params if not provided
        train_params = {**self.DEFAULT_PARAMS, **(params or {})}
        
        # Split data
        X_train, X_test = train_test_split(data, test_size=test_size, random_state=42)
        
        # Train model
        self.model = IsolationForest(**train_params)
        self.model.fit(X_train)
        self.is_trained = True
        
        # Evaluate on test set
        predictions = self.model.predict(X_test)
        anomaly_count = np.sum(predictions == -1)
        
        # Calculate metrics
        metrics = {
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'anomalies_detected': int(anomaly_count),
            'anomaly_rate': float(anomaly_count / len(X_test)),
            'params': train_params
        }
        
        # Save model
        self.save_model()
        
        return metrics
    
    def predict(self, data: np.ndarray) -> np.ndarray:
        """
        Predict anomalies in the data.
        
        Args:
            data: Data array of shape (n_samples, n_features) or (n_features,)
            
        Returns:
            Array of predictions: 1 for normal, -1 for anomaly
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() or load_model() first.")
        
        # Handle single sample
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        return self.model.predict(data)
    
    def predict_proba(self, data: np.ndarray) -> np.ndarray:
        """
        Get anomaly scores (negative of the anomaly score).
        
        Args:
            data: Data array
            
        Returns:
            Array of anomaly scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained.")
        
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        return self.model.score_samples(data)
    
    def decision_function(self, data: np.ndarray) -> np.ndarray:
        """
        Get raw anomaly scores.
        
        Args:
            data: Data array
            
        Returns:
            Array of decision scores (lower = more anomalous)
        """
        if not self.is_trained:
            raise ValueError("Model not trained.")
        
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        return self.model.decision_function(data)
    
    def save_model(self) -> str:
        """Save trained model to disk."""
        if self.model is None:
            raise ValueError("No model to save.")
        
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'trained_at': datetime.now().isoformat()
            }, f)
        
        return str(self.model_path)
    
    def load_model(self) -> bool:
        """Load model from disk."""
        if not self.model_path.exists():
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.feature_names = data.get('feature_names', self.feature_names)
            self.is_trained = True
            return True
        except Exception:
            return False
    
    def get_feature_importance(self, data: np.ndarray) -> Dict[str, float]:
        """
        Get feature importance based on contribution to anomaly score.
        
        Args:
            data: Data sample
            
        Returns:
            Dictionary of feature importance scores
        """
        if data.ndim == 1:
            data = data.reshape(1, -1)
        
        # Calculate deviation from mean for each feature
        mean_vals = np.mean(data, axis=0)
        
        # Calculate importance based on z-scores
        std_vals = np.std(data, axis=0) + 1e-8
        z_scores = np.abs((data - mean_vals) / std_vals)
        
        importance = {}
        for i, name in enumerate(self.feature_names):
            importance[name] = float(np.mean(z_scores[:, i]))
        
        return importance


def create_synthetic_training_data(n_samples: int = 1000) -> np.ndarray:
    """
    Create synthetic sensor data for initial model training.
    
    This simulates typical steel plant equipment sensor readings.
    """
    np.random.seed(42)
    
    data = []
    
    for _ in range(n_samples):
        # Normal operating conditions with some variation
        temperature = np.random.normal(75, 10)  # °C
        vibration = np.random.normal(1.5, 0.5)  # mm/s
        current = np.random.normal(20, 3)  # A
        pressure = np.random.normal(70, 8)  # bar
        rpm = np.random.normal(1500, 200)  # rpm
        
        # Occasional anomalies (about 10%)
        if np.random.random() < 0.1:
            # Choose random anomaly type
            anomaly_type = np.random.choice(['temperature', 'vibration', 'current', 'pressure', 'rpm'])
            
            if anomaly_type == 'temperature':
                temperature += np.random.choice([-30, 35])
            elif anomaly_type == 'vibration':
                vibration += np.random.choice([-0.8, 2.5])
            elif anomaly_type == 'current':
                current += np.random.choice([-8, 12])
            elif anomaly_type == 'pressure':
                pressure += np.random.choice([-20, 25])
            else:
                rpm += np.random.choice([-400, 600])
        
        data.append([temperature, vibration, current, pressure, rpm])
    
    return np.array(data)


# Singleton instances
_detector: Optional[AnomalyDetector] = None
_preprocessor: Optional[SensorPreprocessor] = None


def get_anomaly_detector() -> AnomalyDetector:
    """Get or create global anomaly detector instance."""
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
        _detector.load_model()
    return _detector


def get_preprocessor() -> SensorPreprocessor:
    """Get or create global preprocessor instance."""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = SensorPreprocessor()
        _preprocessor.load_scaler()
    return _preprocessor


def train_initial_model():
    """Train initial model with synthetic data if no model exists."""
    detector = get_anomaly_detector()
    preprocessor = get_preprocessor()
    
    if not detector.is_trained:
        # Create synthetic training data
        data = create_synthetic_training_data(2000)
        
        # Fit preprocessor and scale data
        scaled_data = preprocessor.fit_transform(data)
        
        # Train detector
        metrics = detector.train(scaled_data)
        print(f"Initial model trained: {metrics}")
        
        return metrics
    
    return None