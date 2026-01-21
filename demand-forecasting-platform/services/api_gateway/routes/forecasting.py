"""
Forecasting API Routes
Demand prediction endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging
from datetime import datetime

from shared.models.schemas import ForecastRequest, ForecastResponse, SKUForecast, DemandPrediction
from shared.database.connection import get_db
from services.forecasting_service.inference import ForecastingService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ForecastResponse, status_code=status.HTTP_200_OK)
async def create_forecast(
    request: ForecastRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate demand forecast for specified SKUs and locations

    **Example Request:**
    ```json
    {
      "date_range": {
        "start": "2026-02-01",
        "end": "2026-03-31"
      },
      "sku_ids": ["SKU-001", "SKU-002"],
      "location_ids": ["DC-ATL", "DC-CHI"],
      "confidence_level": 0.95
    }
    ```

    **Returns:**
    - Daily demand predictions
    - Confidence intervals (upper/lower bounds)
    - Recommended stock levels
    - Model metadata (version, accuracy)
    """

    try:
        logger.info(
            f"Forecast request: {len(request.sku_ids)} SKUs, "
            f"{len(request.location_ids or [])} locations, "
            f"{(request.date_range.end - request.date_range.start).days} days"
        )

        # Initialize forecasting service
        forecasting_service = ForecastingService(db)

        # Generate forecasts
        forecasts = await forecasting_service.generate_forecasts(
            sku_ids=request.sku_ids,
            location_ids=request.location_ids,
            start_date=request.date_range.start,
            end_date=request.date_range.end,
            confidence_level=request.confidence_level,
            model_type=request.model_type,
            include_features=request.include_features
        )

        # Get model metadata
        metadata = await forecasting_service.get_model_metadata()

        response = ForecastResponse(
            forecasts=forecasts,
            metadata={
                **metadata,
                "generated_at": datetime.utcnow().isoformat(),
                "request_params": {
                    "confidence_level": request.confidence_level,
                    "model_type": request.model_type.value if request.model_type else "ensemble"
                }
            }
        )

        logger.info(f"Forecast generated: {len(forecasts)} SKU-location combinations")

        return response

    except ValueError as e:
        logger.error(f"Invalid forecast request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate forecast. Please try again later."
        )


@router.get("/accuracy", status_code=status.HTTP_200_OK)
async def get_forecast_accuracy(
    model_version: str = None,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """
    Get forecast accuracy metrics for recent predictions

    **Query Parameters:**
    - `model_version`: Specific model version (optional, defaults to current)
    - `days`: Number of days to evaluate (default: 30)

    **Returns:**
    - MAPE (Mean Absolute Percentage Error)
    - RMSE (Root Mean Squared Error)
    - Bias (over/under forecasting tendency)
    - Sample count
    """

    try:
        forecasting_service = ForecastingService(db)

        accuracy_metrics = await forecasting_service.get_accuracy_metrics(
            model_version=model_version,
            days=days
        )

        return {
            "metrics": accuracy_metrics,
            "evaluation_period_days": days,
            "model_version": model_version or "current"
        }

    except Exception as e:
        logger.error(f"Failed to retrieve accuracy metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accuracy metrics"
        )


@router.get("/models", status_code=status.HTTP_200_OK)
async def list_available_models(
    db: AsyncSession = Depends(get_db)
):
    """
    List all available forecast models and their performance

    **Returns:**
    - Model versions
    - Accuracy metrics
    - Training dates
    - Production status
    """

    try:
        forecasting_service = ForecastingService(db)
        models = await forecasting_service.list_models()

        return {
            "models": models,
            "count": len(models)
        }

    except Exception as e:
        logger.error(f"Failed to list models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list models"
        )


@router.post("/retrain", status_code=status.HTTP_202_ACCEPTED)
async def trigger_model_retraining(
    model_type: str = "ensemble",
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger model retraining (async operation)

    **Query Parameters:**
    - `model_type`: Type of model to retrain (prophet, xgboost, lstm, ensemble)

    **Returns:**
    - Job ID for tracking retraining progress
    """

    try:
        # This would typically trigger a background job
        # For now, return a placeholder

        logger.info(f"Model retraining triggered: {model_type}")

        return {
            "status": "accepted",
            "message": "Model retraining initiated",
            "model_type": model_type,
            "job_id": f"retrain-{model_type}-{datetime.utcnow().timestamp()}",
            "estimated_completion": "30-60 minutes"
        }

    except Exception as e:
        logger.error(f"Failed to trigger retraining: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger model retraining"
        )
