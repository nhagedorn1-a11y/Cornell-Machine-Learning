"""
Quick API Test Script
Tests the forecasting API without requiring full Docker setup
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import date, timedelta
from decimal import Decimal

# Mock the database connection for testing
class MockDB:
    """Mock database session for testing"""
    async def execute(self, query):
        return None

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass


async def test_forecasting_service():
    """Test the forecasting service directly"""
    print("=" * 70)
    print("TESTING FORECASTING SERVICE")
    print("=" * 70)

    from services.forecasting_service.inference import ForecastingService

    # Create mock database
    db = MockDB()

    # Initialize service
    service = ForecastingService(db)

    print("\n✓ Forecasting service initialized")

    # Test forecast generation
    print("\n📊 Generating forecast for SKU-001 at DC-ATL...")
    print(f"   Date range: {date.today()} to {date.today() + timedelta(days=30)}")

    forecasts = await service.generate_forecasts(
        sku_ids=["SKU-001", "SKU-002"],
        location_ids=["DC-ATL", "DC-CHI"],
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        confidence_level=0.95,
        include_features=True
    )

    print(f"\n✓ Generated {len(forecasts)} forecasts")

    # Display first forecast
    if forecasts:
        fc = forecasts[0]
        print(f"\n📦 Sample Forecast: {fc.sku_id} @ {fc.location_id}")
        print(f"   Predictions: {len(fc.predictions)} days")

        # Show first 3 days
        for i, pred in enumerate(fc.predictions[:3]):
            print(f"   Day {i+1} ({pred.date}): "
                  f"Demand={pred.demand:.0f}, "
                  f"Range=[{pred.lower_bound:.0f}, {pred.upper_bound:.0f}], "
                  f"Stock={pred.recommended_stock}")

        if fc.features_used:
            print(f"\n🔍 Top Features:")
            for feature, importance in list(fc.features_used.items())[:3]:
                print(f"   {feature}: {importance:.2%}")

    # Test model metadata
    print("\n📋 Model Metadata:")
    metadata = await service.get_model_metadata()
    for key, value in metadata.items():
        if key != "components":
            print(f"   {key}: {value}")

    # Test accuracy metrics
    print("\n📈 Accuracy Metrics:")
    accuracy = await service.get_accuracy_metrics(days=30)
    for key, value in accuracy.items():
        if key != "samples":
            print(f"   {key}: {value}")

    print("\n✅ Forecasting service test complete!\n")


async def test_api_schemas():
    """Test Pydantic schemas"""
    print("=" * 70)
    print("TESTING API SCHEMAS")
    print("=" * 70)

    from shared.models.schemas import (
        ForecastRequest, DateRange, DemandPrediction,
        RebalanceRequest, CurrentInventory, Constraints
    )

    # Test forecast request
    print("\n📋 Creating ForecastRequest...")
    request = ForecastRequest(
        date_range=DateRange(
            start=date.today(),
            end=date.today() + timedelta(days=60)
        ),
        sku_ids=["SKU-001", "SKU-002"],
        location_ids=["DC-ATL", "DC-CHI"],
        confidence_level=0.95
    )
    print(f"✓ Valid forecast request created: {len(request.sku_ids)} SKUs")

    # Test rebalance request
    print("\n📦 Creating RebalanceRequest...")
    rebalance_req = RebalanceRequest(
        current_inventory=CurrentInventory(__root__={
            "DC-ATL": {"SKU-001": 200, "SKU-002": 150},
            "DC-CHI": {"SKU-001": 800, "SKU-002": 650}
        }),
        constraints=Constraints(
            budget=Decimal("50000.00"),
            max_transfers=10
        )
    )
    print(f"✓ Valid rebalance request created")

    print("\n✅ Schema validation test complete!\n")


def test_configuration():
    """Test configuration loading"""
    print("=" * 70)
    print("TESTING CONFIGURATION")
    print("=" * 70)

    from shared.utils.config import settings

    print(f"\n⚙️  Environment: {settings.ENVIRONMENT}")
    print(f"⚙️  Log Level: {settings.LOG_LEVEL}")
    print(f"⚙️  API Port: {settings.API_PORT}")
    print(f"⚙️  Default Forecast Horizon: {settings.DEFAULT_FORECAST_HORIZON} days")
    print(f"⚙️  Confidence Level: {settings.DEFAULT_CONFIDENCE_LEVEL}")

    # Check API keys (masked)
    if settings.OPENWEATHER_API_KEY:
        print(f"⚙️  OpenWeather API: {'*' * 20} (configured)")
    else:
        print(f"⚙️  OpenWeather API: Not configured (using mock data)")

    if settings.FRED_API_KEY:
        print(f"⚙️  FRED API: {'*' * 20} (configured)")
    else:
        print(f"⚙️  FRED API: Not configured (using mock data)")

    print("\n✅ Configuration test complete!\n")


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("DEMAND FORECASTING PLATFORM - API TEST")
    print("=" * 70 + "\n")

    try:
        # Test configuration
        test_configuration()

        # Test schemas
        await test_api_schemas()

        # Test forecasting service
        await test_forecasting_service()

        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n📚 Next Steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Start Docker services: docker-compose up -d")
        print("  3. Launch API: uvicorn services.api_gateway.main:app --reload")
        print("  4. View docs: http://localhost:8000/docs")
        print("\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Set environment variables for testing
    os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("LOG_LEVEL", "INFO")

    asyncio.run(main())
