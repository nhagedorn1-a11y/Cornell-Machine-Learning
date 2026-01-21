# Demand Forecasting & Inventory Optimization Platform
## Production SaaS MVP - Q1 2026

> **Mission**: Build a predictive inventory optimization platform that ingests multi-modal data streams (weather, sales, macro indicators) to forecast demand at SKU-level granularity. Target: 15-20% reduction in carrying costs while maintaining 98%+ fill rates.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway (FastAPI)                    │
│  /forecast  /optimize  /metrics  /commodities               │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        │            │            │              │
┌───────▼──────┐ ┌──▼────────┐ ┌─▼──────────┐ ┌▼─────────────┐
│ Forecasting  │ │Optimization│ │ Ingestion  │ │  Monitoring  │
│   Service    │ │  Service   │ │  Service   │ │   (MLflow)   │
│ (ML Models)  │ │ (Inventory)│ │ (APIs/ETL) │ │              │
└──────┬───────┘ └─────┬──────┘ └─────┬──────┘ └──────┬───────┘
       │               │              │               │
       └───────────────┴──────────────┴───────────────┘
                            │
                ┌───────────▼───────────┐
                │  PostgreSQL/TimescaleDB│
                │  (Time-Series Optimized)│
                │  + Redis Cache          │
                └─────────────────────────┘
```

---

## Tech Stack

**Backend:**
- Python 3.11+ (FastAPI, Pydantic, SQLAlchemy)
- PostgreSQL 15 + TimescaleDB extension
- Redis 7.x (caching, session management)
- Docker + Docker Compose (local dev)

**ML Pipeline:**
- Scikit-learn, XGBoost, LightGBM
- Prophet/NeuralProphet (time-series)
- TensorFlow/PyTorch (deep learning)
- MLflow (experiment tracking)
- Pandas/Polars (data wrangling)

**APIs & Data Sources:**
- NOAA, OpenWeather (weather data)
- FRED API (economic indicators)
- Custom sales data ingestion

---

## Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Make (optional, for shortcuts)

### 1. Clone and Setup

```bash
git clone <repo-url>
cd demand-forecasting-platform

# Copy environment template
cp .env.example .env

# Edit .env with your API keys:
# - OPENWEATHER_API_KEY
# - FRED_API_KEY (economic data)
# - Database credentials
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL, TimescaleDB, Redis
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### 3. Run Database Migrations

```bash
# Initialize database schema
python scripts/init_db.py

# Load sample data (optional)
python scripts/load_sample_data.py
```

### 4. Start API Gateway

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn services.api_gateway.main:app --reload --port 8000

# API docs available at: http://localhost:8000/docs
```

### 5. Run ML Training Pipeline

```bash
# Train baseline models
python ml_pipeline/train_models.py --config configs/baseline.yaml

# View experiments in MLflow
mlflow ui --port 5000
# Open http://localhost:5000
```

---

## API Endpoints

### Forecasting

**POST /api/v1/forecast**
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

**Response:**
```json
{
  "forecasts": [
    {
      "sku_id": "SKU-001",
      "location_id": "DC-ATL",
      "predictions": [
        {
          "date": "2026-02-01",
          "demand": 450,
          "lower_bound": 380,
          "upper_bound": 520,
          "recommended_stock": 500
        }
      ]
    }
  ],
  "metadata": {
    "model_version": "ensemble-v1.2",
    "forecast_accuracy_mape": 12.3
  }
}
```

### Optimization

**POST /api/v1/optimize/rebalance**
```json
{
  "current_inventory": {
    "DC-ATL": {"SKU-001": 200},
    "DC-CHI": {"SKU-001": 800}
  },
  "constraints": {
    "budget": 50000,
    "max_transfers": 10
  }
}
```

**Response:**
```json
{
  "transfer_recommendations": [
    {
      "from": "DC-CHI",
      "to": "DC-ATL",
      "sku_id": "SKU-001",
      "quantity": 300,
      "cost": 1200,
      "expected_roi": 4500,
      "priority": "HIGH"
    }
  ]
}
```

### Metrics Dashboard

**GET /api/v1/metrics/dashboard**
```json
{
  "forecast_accuracy": {
    "mape": 12.3,
    "rmse": 45.2,
    "bias": -2.1
  },
  "inventory_health": {
    "total_value": 12800000,
    "turnover_ratio": 4.2,
    "stockout_rate": 0.018,
    "excess_inventory_pct": 8.5
  },
  "service_levels": {
    "fill_rate": 0.942,
    "on_time_delivery": 0.956
  }
}
```

---

## Project Structure

```
demand-forecasting-platform/
├── services/
│   ├── api_gateway/           # Main FastAPI application
│   │   ├── main.py           # App entry point
│   │   ├── routes/           # API route handlers
│   │   └── middleware/       # Auth, logging, etc.
│   │
│   ├── forecasting_service/  # ML forecasting microservice
│   │   ├── models/           # Prophet, XGBoost, LSTM
│   │   ├── ensemble.py       # Ensemble logic
│   │   └── inference.py      # Prediction endpoint
│   │
│   ├── optimization_service/ # Inventory optimization
│   │   ├── algorithms/       # EOQ, safety stock, rebalancing
│   │   └── optimizer.py
│   │
│   └── ingestion_service/    # Data ingestion & ETL
│       ├── connectors/       # Weather, economic APIs
│       ├── pipelines/        # ETL jobs
│       └── scheduler.py      # Airflow/cron jobs
│
├── shared/
│   ├── models/               # Pydantic models (shared DTOs)
│   ├── database/             # SQLAlchemy models, migrations
│   │   ├── models.py
│   │   └── schema.sql
│   └── utils/                # Shared utilities
│
├── ml_pipeline/
│   ├── feature_engineering/  # Feature extraction
│   │   ├── lag_features.py
│   │   ├── rolling_stats.py
│   │   └── weather_features.py
│   │
│   ├── model_training/       # Training scripts
│   │   ├── train_prophet.py
│   │   ├── train_xgboost.py
│   │   └── train_ensemble.py
│   │
│   └── experiments/          # MLflow experiments
│
├── infrastructure/
│   ├── docker/               # Dockerfiles for each service
│   ├── postgres/             # PostgreSQL init scripts
│   └── kubernetes/           # K8s manifests (for production)
│
├── configs/
│   ├── baseline.yaml         # Model configs
│   └── production.yaml
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── scripts/
│   ├── init_db.py
│   └── load_sample_data.py
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Core Metrics (50 Tracked)

### Demand Signals (20)
1. Rolling 7/30/90-day sales velocity
2. Year-over-year growth rate
3. Seasonal decomposition (trend, seasonality, residual)
4. Weather correlation (heating/cooling degree days)
5. Promotional lift factors
6. Price elasticity
7. Competitive pricing indices
8. Google Trends momentum
9. Social sentiment scores
10. New customer acquisition rate
11. Repeat purchase frequency
12. Cart abandonment rate
13. Regional demographic shifts
14. Holiday/event impact
15. Stock-out history
16. Product lifecycle stage
17. Substitute product cannibalization
18. Cross-sell correlation
19. Marketing spend ROI
20. External events (disasters, policy)

### Supply Chain Metrics (15)
21-35. Lead time variability, on-time delivery, freight costs, capacity utilization, returns rates, etc.

### Financial/Operational (15)
36-50. Gross margin, carrying costs, inventory turnover, service levels, forecast accuracy (MAPE), etc.

---

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/new-metric

# Make changes, run tests
pytest tests/

# Commit and push
git commit -m "Add: Rolling 90-day velocity metric"
git push origin feature/new-metric
```

### 2. Model Training
```bash
# Train new model version
python ml_pipeline/train_models.py \
  --model xgboost \
  --config configs/baseline.yaml \
  --experiment "Q1-2026-baseline"

# Compare with previous in MLflow UI
mlflow ui
```

### 3. Database Migrations
```bash
# Generate migration
alembic revision -m "Add commodity_prices table"

# Apply migration
alembic upgrade head
```

---

## Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires Docker services)
docker-compose up -d
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Coverage report
pytest --cov=services --cov=ml_pipeline --cov-report=html
```

---

## Deployment

### Staging
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### Production (Kubernetes)
```bash
# Build and push images
docker build -t registry.example.com/forecasting-api:v1.0 .
docker push registry.example.com/forecasting-api:v1.0

# Apply K8s manifests
kubectl apply -f infrastructure/kubernetes/
kubectl rollout status deployment/forecasting-api
```

---

## Monitoring & Observability

- **MLflow**: http://localhost:5000 (model experiments, versioning)
- **Prometheus**: Metrics scraping (API latency, throughput)
- **Grafana**: Dashboards (forecast accuracy, inventory health)
- **Sentry**: Error tracking
- **DataDog**: APM (optional, for production)

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Forecast MAPE | < 15% | TBD |
| API Latency (p95) | < 200ms | TBD |
| System Uptime | 99.9% | TBD |
| Cost per Prediction | < $0.001 | TBD |
| Inventory Reduction | 15-20% | TBD |
| Fill Rate | > 98% | TBD |

---

## Roadmap

**Phase 1 (Weeks 1-2): MVP**
- ✅ Core infrastructure
- ✅ Baseline Prophet model
- ✅ FastAPI endpoints
- ✅ PostgreSQL schema

**Phase 2 (Weeks 3-4): Enhanced ML**
- ⏳ XGBoost with custom objective
- ⏳ LSTM for sequential patterns
- ⏳ Ensemble orchestration
- ⏳ Feature engineering (50 metrics)

**Phase 3 (Weeks 5-8): Production Ready**
- ⏳ Real-time data ingestion
- ⏳ Multi-tenancy
- ⏳ Kafka event streaming
- ⏳ React dashboard
- ⏳ Kubernetes deployment

**Phase 4 (Weeks 9-12): Scale & Optimize**
- ⏳ Multi-cloud support
- ⏳ Advanced causal inference
- ⏳ AutoML for hyperparameter tuning
- ⏳ Mobile app

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## License

Proprietary - Internal Use Only

---

## Support

- **Slack**: #supply-chain-ml
- **Email**: ml-team@company.com
- **Docs**: https://docs.internal.com/forecasting-platform

---

**Built with ❤️ by the Supply Chain Intelligence Engineering Team**
