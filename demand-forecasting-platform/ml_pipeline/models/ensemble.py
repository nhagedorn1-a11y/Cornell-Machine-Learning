"""
Ensemble Model - Combines Prophet, XGBoost, and LSTM
Weighted average based on recent accuracy
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EnsembleForecaster:
    """
    Ensemble forecasting model combining multiple base models

    Combines:
    - Prophet (40%): Good for seasonality and trends
    - XGBoost (40%): Good for complex non-linear patterns
    - LSTM (20%): Good for sequential dependencies (optional)

    Weights can be:
    - Fixed (predefined)
    - Dynamic (based on recent accuracy)
    - Stacked (meta-model learns optimal weights)
    """

    def __init__(
        self,
        prophet_weight: float = 0.4,
        xgboost_weight: float = 0.4,
        lstm_weight: float = 0.2,
        use_dynamic_weights: bool = False,
        lookback_days: int = 30
    ):
        """
        Initialize ensemble model

        Args:
            prophet_weight: Weight for Prophet predictions
            xgboost_weight: Weight for XGBoost predictions
            lstm_weight: Weight for LSTM predictions
            use_dynamic_weights: Adjust weights based on recent performance
            lookback_days: Days to look back for dynamic weighting
        """
        self.prophet_weight = prophet_weight
        self.xgboost_weight = xgboost_weight
        self.lstm_weight = lstm_weight
        self.use_dynamic_weights = use_dynamic_weights
        self.lookback_days = lookback_days

        # Normalize weights
        total = prophet_weight + xgboost_weight + lstm_weight
        self.prophet_weight /= total
        self.xgboost_weight /= total
        self.lstm_weight /= total

        self.models = {
            'prophet': None,
            'xgboost': None,
            'lstm': None
        }

        self.metadata = {}

    def set_models(
        self,
        prophet_model=None,
        xgboost_model=None,
        lstm_model=None
    ):
        """Set the base models"""
        self.models['prophet'] = prophet_model
        self.models['xgboost'] = xgboost_model
        self.models['lstm'] = lstm_model

        logger.info(
            f"Ensemble configured with "
            f"Prophet={self.prophet_weight:.1%}, "
            f"XGBoost={self.xgboost_weight:.1%}, "
            f"LSTM={self.lstm_weight:.1%}"
        )

    def predict(
        self,
        prophet_pred: np.ndarray,
        xgboost_pred: np.ndarray,
        lstm_pred: Optional[np.ndarray] = None,
        recent_errors: Optional[Dict[str, np.ndarray]] = None
    ) -> np.ndarray:
        """
        Generate ensemble predictions

        Args:
            prophet_pred: Prophet predictions
            xgboost_pred: XGBoost predictions
            lstm_pred: LSTM predictions (optional)
            recent_errors: Recent prediction errors for dynamic weighting

        Returns:
            Ensemble predictions
        """
        if self.use_dynamic_weights and recent_errors is not None:
            weights = self._calculate_dynamic_weights(recent_errors)
        else:
            weights = {
                'prophet': self.prophet_weight,
                'xgboost': self.xgboost_weight,
                'lstm': self.lstm_weight
            }

        # Weighted average
        ensemble_pred = (
            weights['prophet'] * prophet_pred +
            weights['xgboost'] * xgboost_pred
        )

        if lstm_pred is not None:
            ensemble_pred += weights['lstm'] * lstm_pred

        logger.debug(
            f"Ensemble weights: Prophet={weights['prophet']:.2f}, "
            f"XGBoost={weights['xgboost']:.2f}, "
            f"LSTM={weights['lstm']:.2f}"
        )

        return ensemble_pred

    def predict_with_uncertainty(
        self,
        prophet_pred: Tuple[np.ndarray, np.ndarray, np.ndarray],
        xgboost_pred: Tuple[np.ndarray, np.ndarray, np.ndarray],
        lstm_pred: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Ensemble predictions with confidence intervals

        Args:
            prophet_pred: (predictions, lower, upper) from Prophet
            xgboost_pred: (predictions, lower, upper) from XGBoost
            lstm_pred: (predictions, lower, upper) from LSTM (optional)

        Returns:
            (ensemble_pred, ensemble_lower, ensemble_upper)
        """
        # Unpack predictions
        p_mean, p_lower, p_upper = prophet_pred
        x_mean, x_lower, x_upper = xgboost_pred

        if lstm_pred:
            l_mean, l_lower, l_upper = lstm_pred

        # Ensemble mean
        ensemble_mean = (
            self.prophet_weight * p_mean +
            self.xgboost_weight * x_mean
        )
        if lstm_pred:
            ensemble_mean += self.lstm_weight * l_mean

        # Ensemble uncertainty (combine variances)
        # Var(aX + bY) = a²Var(X) + b²Var(Y) + 2abCov(X,Y)
        # Assuming independent models (Cov = 0)

        p_var = ((p_upper - p_lower) / 3.92) ** 2  # Approx from 95% CI
        x_var = ((x_upper - x_lower) / 3.92) ** 2

        ensemble_var = (
            self.prophet_weight ** 2 * p_var +
            self.xgboost_weight ** 2 * x_var
        )

        if lstm_pred:
            l_var = ((l_upper - l_lower) / 3.92) ** 2
            ensemble_var += self.lstm_weight ** 2 * l_var

        ensemble_std = np.sqrt(ensemble_var)

        # 95% confidence interval
        ensemble_lower = np.maximum(0, ensemble_mean - 1.96 * ensemble_std)
        ensemble_upper = ensemble_mean + 1.96 * ensemble_std

        return ensemble_mean, ensemble_lower, ensemble_upper

    def _calculate_dynamic_weights(
        self,
        recent_errors: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """
        Calculate weights based on recent forecast errors

        Lower error → Higher weight
        """
        # Calculate inverse error (lower error = higher score)
        scores = {}

        for model_name, errors in recent_errors.items():
            if len(errors) > 0:
                # Use MAPE as error metric
                mape = np.mean(np.abs(errors))
                # Inverse error score
                scores[model_name] = 1.0 / (mape + 1e-6)
            else:
                scores[model_name] = 0.0

        # Normalize to get weights
        total_score = sum(scores.values())

        if total_score > 0:
            weights = {k: v / total_score for k, v in scores.items()}
        else:
            # Fallback to default weights
            weights = {
                'prophet': self.prophet_weight,
                'xgboost': self.xgboost_weight,
                'lstm': self.lstm_weight
            }

        return weights

    def evaluate(
        self,
        y_true: np.ndarray,
        prophet_pred: np.ndarray,
        xgboost_pred: np.ndarray,
        lstm_pred: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Evaluate ensemble performance against individual models

        Returns:
            Dictionary with MAPE for each model + ensemble
        """
        # Ensemble prediction
        ensemble_pred = self.predict(prophet_pred, xgboost_pred, lstm_pred)

        # Calculate MAPE for each
        def mape(y_true, y_pred):
            return np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100

        results = {
            'prophet_mape': mape(y_true, prophet_pred),
            'xgboost_mape': mape(y_true, xgboost_pred),
            'ensemble_mape': mape(y_true, ensemble_pred)
        }

        if lstm_pred is not None:
            results['lstm_mape'] = mape(y_true, lstm_pred)

        # Improvement over best individual model
        best_individual = min(results['prophet_mape'], results['xgboost_mape'])
        improvement = best_individual - results['ensemble_mape']
        results['improvement_over_best'] = improvement

        logger.info(f"Ensemble MAPE: {results['ensemble_mape']:.2f}%")
        logger.info(f"Improvement: {improvement:.2f}%")

        return results

    def get_model_contributions(
        self,
        prophet_pred: np.ndarray,
        xgboost_pred: np.ndarray,
        lstm_pred: Optional[np.ndarray] = None
    ) -> pd.DataFrame:
        """
        Get contribution of each model to final prediction

        Returns:
            DataFrame with predictions from each model
        """
        contributions = pd.DataFrame({
            'prophet': prophet_pred,
            'xgboost': xgboost_pred,
            'prophet_contribution': prophet_pred * self.prophet_weight,
            'xgboost_contribution': xgboost_pred * self.xgboost_weight
        })

        if lstm_pred is not None:
            contributions['lstm'] = lstm_pred
            contributions['lstm_contribution'] = lstm_pred * self.lstm_weight

        ensemble_pred = self.predict(prophet_pred, xgboost_pred, lstm_pred)
        contributions['ensemble'] = ensemble_pred

        return contributions


def select_best_model(
    predictions: Dict[str, np.ndarray],
    y_true: np.ndarray,
    method: str = 'mape'
) -> str:
    """
    Select best performing model for a specific dataset

    Args:
        predictions: Dict of model_name -> predictions
        y_true: True values
        method: Selection metric ('mape', 'rmse', 'mae')

    Returns:
        Name of best model
    """
    scores = {}

    for model_name, y_pred in predictions.items():
        if method == 'mape':
            score = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1))) * 100
        elif method == 'rmse':
            score = np.sqrt(np.mean((y_true - y_pred) ** 2))
        elif method == 'mae':
            score = np.mean(np.abs(y_true - y_pred))
        else:
            raise ValueError(f"Unknown method: {method}")

        scores[model_name] = score

    best_model = min(scores, key=scores.get)

    logger.info(f"Best model: {best_model} ({method}={scores[best_model]:.2f})")

    return best_model
