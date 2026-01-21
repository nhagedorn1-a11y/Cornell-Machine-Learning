"""
Forecasting Service - Model Inference
Handles demand prediction using trained ML models
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
import numpy as np
import pandas as pd

from shared.models.schemas import SKUForecast, DemandPrediction, ModelType

logger = logging.getLogger(__name__)


class ForecastingService:
    """
    Service for generating demand forecasts
    Uses ensemble of Prophet + XGBoost + LSTM models
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.models = {}
        self._load_models()

    def _load_models(self):
        """Load trained models from MLflow or local cache"""
        # TODO: Implement actual model loading from MLflow
        # For now, we'll use mock models
        logger.info("Loading forecasting models...")

        self.models = {
            "prophet": None,  # Placeholder for Prophet model
            "xgboost": None,  # Placeholder for XGBoost model
            "lstm": None,     # Placeholder for LSTM model
            "ensemble": None  # Ensemble orchestrator
        }

        logger.info("Models loaded (mock mode)")

    async def generate_forecasts(
        self,
        sku_ids: List[str],
        location_ids: Optional[List[str]],
        start_date: date,
        end_date: date,
        confidence_level: float = 0.95,
        model_type: Optional[ModelType] = None,
        include_features: bool = False
    ) -> List[SKUForecast]:
        """
        Generate demand forecasts for specified SKUs and locations

        Args:
            sku_ids: List of SKU IDs to forecast
            location_ids: List of location IDs (None = all locations)
            start_date: Forecast start date
            end_date: Forecast end date
            confidence_level: Confidence level for prediction intervals
            model_type: Specific model to use (None = ensemble)
            include_features: Include feature importance in response

        Returns:
            List of SKU forecasts with predictions
        """

        logger.info(
            f"Generating forecasts: {len(sku_ids)} SKUs, "
            f"{len(location_ids) if location_ids else 'all'} locations, "
            f"{(end_date - start_date).days} days"
        )

        forecasts = []

        # If no locations specified, get all locations from database
        if location_ids is None:
            location_ids = await self._get_all_locations()

        # Generate forecast for each SKU-location combination
        for sku_id in sku_ids:
            for location_id in location_ids:
                try:
                    # Get historical data for this SKU-location
                    historical_data = await self._get_historical_data(
                        sku_id, location_id, lookback_days=365
                    )

                    # Generate predictions
                    predictions = self._predict(
                        sku_id=sku_id,
                        location_id=location_id,
                        historical_data=historical_data,
                        start_date=start_date,
                        end_date=end_date,
                        confidence_level=confidence_level,
                        model_type=model_type or ModelType.ENSEMBLE
                    )

                    # Get feature importance (if requested)
                    features_used = None
                    if include_features:
                        features_used = self._get_feature_importance(
                            sku_id, location_id
                        )

                    forecast = SKUForecast(
                        sku_id=sku_id,
                        location_id=location_id,
                        predictions=predictions,
                        features_used=features_used
                    )

                    forecasts.append(forecast)

                except Exception as e:
                    logger.error(
                        f"Failed to forecast {sku_id} at {location_id}: {e}",
                        exc_info=True
                    )
                    # Continue with other forecasts

        logger.info(f"Generated {len(forecasts)} forecasts")

        return forecasts

    def _predict(
        self,
        sku_id: str,
        location_id: str,
        historical_data: pd.DataFrame,
        start_date: date,
        end_date: date,
        confidence_level: float,
        model_type: ModelType
    ) -> List[DemandPrediction]:
        """
        Generate predictions using specified model

        For MVP, using simplified forecasting logic
        In production, this would use trained ML models
        """

        predictions = []
        current_date = start_date

        # Calculate baseline from historical data
        if len(historical_data) > 0:
            baseline_demand = historical_data['quantity'].mean()
            demand_std = historical_data['quantity'].std()
        else:
            # No historical data - use conservative estimate
            baseline_demand = 100
            demand_std = 20

        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z_score = z_scores.get(confidence_level, 1.96)

        # Generate daily predictions
        while current_date <= end_date:
            # Add seasonality (mock - would be learned from data)
            day_of_week = current_date.weekday()
            month = current_date.month

            # Weekend boost (mock pattern)
            weekend_factor = 1.2 if day_of_week >= 5 else 1.0

            # Seasonal factor (mock pattern)
            seasonal_factor = 1.0 + 0.3 * np.sin(2 * np.pi * month / 12)

            # Calculate demand
            demand = baseline_demand * weekend_factor * seasonal_factor

            # Add some random variation (mock)
            noise = np.random.normal(0, demand_std * 0.1)
            demand += noise

            # Ensure non-negative
            demand = max(0, demand)

            # Calculate bounds
            margin = z_score * demand_std
            lower_bound = max(0, demand - margin)
            upper_bound = demand + margin

            # Recommended stock = upper bound + safety stock (20%)
            recommended_stock = int(upper_bound * 1.2)

            prediction = DemandPrediction(
                date=current_date,
                demand=Decimal(str(round(demand, 2))),
                lower_bound=Decimal(str(round(lower_bound, 2))),
                upper_bound=Decimal(str(round(upper_bound, 2))),
                recommended_stock=recommended_stock
            )

            predictions.append(prediction)
            current_date += timedelta(days=1)

        return predictions

    async def _get_historical_data(
        self,
        sku_id: str,
        location_id: str,
        lookback_days: int = 365
    ) -> pd.DataFrame:
        """
        Get historical sales data for SKU-location

        In production, this would query the sales.transactions table
        For MVP, returning mock data
        """

        # TODO: Implement actual database query
        # query = select(SalesTransaction).where(
        #     and_(
        #         SalesTransaction.sku_id == sku_id,
        #         SalesTransaction.location_id == location_id,
        #         SalesTransaction.timestamp >= datetime.utcnow() - timedelta(days=lookback_days)
        #     )
        # )
        # result = await self.db.execute(query)
        # transactions = result.scalars().all()

        # Mock historical data
        dates = pd.date_range(
            end=datetime.utcnow(),
            periods=lookback_days,
            freq='D'
        )

        data = pd.DataFrame({
            'date': dates,
            'quantity': np.random.poisson(lam=100, size=lookback_days),
            'sku_id': sku_id,
            'location_id': location_id
        })

        return data

    async def _get_all_locations(self) -> List[str]:
        """Get all active location IDs from database"""

        # TODO: Implement actual database query
        # query = select(Location.id).where(Location.active == True)
        # result = await self.db.execute(query)
        # return [row[0] for row in result.all()]

        # Mock locations
        return ["DC-ATL", "DC-CHI", "DC-NYC", "DC-LAX", "DC-SEA"]

    def _get_feature_importance(
        self,
        sku_id: str,
        location_id: str
    ) -> Dict[str, float]:
        """
        Get feature importance for this SKU-location

        Returns top features that drive demand predictions
        """

        # Mock feature importance
        # In production, this would come from trained models
        return {
            "temperature": 0.35,
            "day_of_week": 0.22,
            "lag_7_days": 0.18,
            "promotional_activity": 0.12,
            "seasonality": 0.08,
            "economic_indicator_cpi": 0.05
        }

    async def get_model_metadata(self) -> Dict[str, Any]:
        """Get metadata about current production models"""

        return {
            "model_version": "ensemble-v1.0-mvp",
            "model_type": "ensemble",
            "training_date": "2026-01-15",
            "forecast_accuracy_mape": 14.2,
            "components": {
                "prophet": {"weight": 0.4, "accuracy_mape": 16.5},
                "xgboost": {"weight": 0.4, "accuracy_mape": 12.8},
                "lstm": {"weight": 0.2, "accuracy_mape": 13.2}
            }
        }

    async def get_accuracy_metrics(
        self,
        model_version: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate forecast accuracy metrics by comparing predictions to actuals

        In production, this would query forecasts.accuracy_metrics table
        """

        # Mock accuracy metrics
        return {
            "mape": 14.2,
            "rmse": 45.8,
            "mae": 32.1,
            "bias": -2.3,
            "samples": 1250,
            "evaluation_period": f"Last {days} days",
            "model_version": model_version or "ensemble-v1.0-mvp"
        }

    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models and their metadata"""

        # Mock model list
        # In production, this would query ml_metadata.model_versions table
        return [
            {
                "model_name": "prophet-baseline",
                "model_type": "prophet",
                "version": "v1.0",
                "training_date": "2026-01-10",
                "is_production": False,
                "test_accuracy": {"mape": 16.5, "rmse": 52.3}
            },
            {
                "model_name": "xgboost-optimized",
                "model_type": "xgboost",
                "version": "v1.2",
                "training_date": "2026-01-12",
                "is_production": False,
                "test_accuracy": {"mape": 12.8, "rmse": 41.2}
            },
            {
                "model_name": "ensemble-production",
                "model_type": "ensemble",
                "version": "v1.0",
                "training_date": "2026-01-15",
                "is_production": True,
                "test_accuracy": {"mape": 14.2, "rmse": 45.8}
            }
        ]
