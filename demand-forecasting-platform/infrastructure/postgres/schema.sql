-- Demand Forecasting Platform - Database Schema
-- Optimized for time-series data with TimescaleDB hypertables

SET search_path TO public, sales, inventory, forecasts, weather, economic, ml_metadata, tenants;

-- ============================================================================
-- TENANTS SCHEMA (Multi-tenancy support)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenants.organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    api_key_hash VARCHAR(255),
    plan_tier VARCHAR(50) DEFAULT 'free',  -- free, starter, professional, enterprise
    max_skus INTEGER DEFAULT 100,
    max_locations INTEGER DEFAULT 10,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS tenants.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'viewer',  -- admin, analyst, viewer
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

CREATE INDEX idx_users_org ON tenants.users(organization_id);

-- ============================================================================
-- SALES SCHEMA (Transactional sales data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sales.transactions (
    id BIGSERIAL,
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    timestamp TIMESTAMPTZ NOT NULL,
    sku_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    channel VARCHAR(50),  -- online, in-store, wholesale
    customer_id VARCHAR(100),
    promotion_id VARCHAR(100),
    metadata JSONB,
    PRIMARY KEY (id, timestamp)
);

-- Convert to TimescaleDB hypertable (partitioned by time)
SELECT create_hypertable('sales.transactions', 'timestamp', if_not_exists => TRUE);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_sales_org_sku_time ON sales.transactions (organization_id, sku_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sales_location_time ON sales.transactions (location_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sales_sku ON sales.transactions (sku_id);
CREATE INDEX IF NOT EXISTS idx_sales_channel ON sales.transactions (channel);

-- SKU master data
CREATE TABLE IF NOT EXISTS sales.skus (
    id VARCHAR(50) PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    unit_cost DECIMAL(10, 2),
    unit_price DECIMAL(10, 2),
    weight_kg DECIMAL(10, 3),
    dimensions_cm VARCHAR(50),  -- LxWxH
    seasonal_index DECIMAL(5, 2) DEFAULT 1.0,
    lifecycle_stage VARCHAR(50),  -- introduction, growth, maturity, decline
    weather_sensitive BOOLEAN DEFAULT false,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skus_org ON sales.skus(organization_id);
CREATE INDEX IF NOT EXISTS idx_skus_category ON sales.skus(category);

-- Locations/Distribution Centers
CREATE TABLE IF NOT EXISTS sales.locations (
    id VARCHAR(50) PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50),  -- DC, warehouse, retail, e-commerce
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    lat DECIMAL(10, 7),
    lon DECIMAL(10, 7),
    capacity_units INTEGER,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_locations_org ON sales.locations(organization_id);
CREATE INDEX IF NOT EXISTS idx_locations_geo ON sales.locations USING GIST(ST_SetSRID(ST_MakePoint(lon, lat), 4326));

-- ============================================================================
-- INVENTORY SCHEMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory.stock_levels (
    id BIGSERIAL,
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    timestamp TIMESTAMPTZ NOT NULL,
    sku_id VARCHAR(50) NOT NULL REFERENCES sales.skus(id),
    location_id VARCHAR(50) NOT NULL REFERENCES sales.locations(id),
    quantity_on_hand INTEGER NOT NULL,
    quantity_reserved INTEGER DEFAULT 0,
    quantity_available INTEGER GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    status inventory_status DEFAULT 'normal',
    safety_stock_level INTEGER,
    reorder_point INTEGER,
    economic_order_quantity INTEGER,
    last_restock_date DATE,
    metadata JSONB,
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('inventory.stock_levels', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_inventory_org_sku_loc ON inventory.stock_levels (organization_id, sku_id, location_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory.stock_levels (status, timestamp DESC);

-- Inventory transfers
CREATE TABLE IF NOT EXISTS inventory.transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    from_location_id VARCHAR(50) NOT NULL REFERENCES sales.locations(id),
    to_location_id VARCHAR(50) NOT NULL REFERENCES sales.locations(id),
    sku_id VARCHAR(50) NOT NULL REFERENCES sales.skus(id),
    quantity INTEGER NOT NULL,
    cost DECIMAL(10, 2),
    expected_roi DECIMAL(10, 2),
    status transfer_status DEFAULT 'pending',
    priority VARCHAR(20),  -- HIGH, MEDIUM, LOW
    initiated_by VARCHAR(100),  -- user or 'SYSTEM' for auto-rebalancing
    completed_at TIMESTAMPTZ,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_transfers_org ON inventory.transfers(organization_id);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON inventory.transfers(status);
CREATE INDEX IF NOT EXISTS idx_transfers_created ON inventory.transfers(created_at DESC);

-- ============================================================================
-- WEATHER SCHEMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS weather.observations (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    location_id VARCHAR(50) NOT NULL REFERENCES sales.locations(id),
    temperature_f DECIMAL(5, 2),
    precipitation_inches DECIMAL(5, 3),
    humidity_pct DECIMAL(5, 2),
    wind_speed_mph DECIMAL(5, 2),
    cloud_cover_pct DECIMAL(5, 2),
    uv_index DECIMAL(4, 1),
    air_quality_index INTEGER,
    weather_condition VARCHAR(100),  -- sunny, rainy, snowy, etc.
    source VARCHAR(50),  -- NOAA, OpenWeather, etc.
    metadata JSONB,
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('weather.observations', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_weather_location_time ON weather.observations (location_id, timestamp DESC);

-- Weather forecasts (14-day rolling)
CREATE TABLE IF NOT EXISTS weather.forecasts (
    id BIGSERIAL,
    forecast_timestamp TIMESTAMPTZ NOT NULL,  -- When forecast was made
    target_timestamp TIMESTAMPTZ NOT NULL,     -- Date being forecasted
    location_id VARCHAR(50) NOT NULL REFERENCES sales.locations(id),
    temperature_f_low DECIMAL(5, 2),
    temperature_f_high DECIMAL(5, 2),
    temperature_f_avg DECIMAL(5, 2),
    precipitation_prob DECIMAL(5, 2),
    precipitation_inches DECIMAL(5, 3),
    weather_condition VARCHAR(100),
    source VARCHAR(50),
    confidence DECIMAL(5, 2),
    PRIMARY KEY (id, forecast_timestamp)
);

SELECT create_hypertable('weather.forecasts', 'forecast_timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_weather_forecasts_location ON weather.forecasts (location_id, target_timestamp);

-- Heating/Cooling Degree Days (HDD/CDD) - important for seasonal demand
CREATE TABLE IF NOT EXISTS weather.degree_days (
    id BIGSERIAL,
    date DATE NOT NULL,
    location_id VARCHAR(50) NOT NULL REFERENCES sales.locations(id),
    heating_degree_days DECIMAL(6, 2),  -- Base 65°F
    cooling_degree_days DECIMAL(6, 2),  -- Base 65°F
    growing_degree_days DECIMAL(6, 2),  -- For agricultural products
    PRIMARY KEY (id, date)
);

SELECT create_hypertable('weather.degree_days', 'date', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_degree_days_location ON weather.degree_days (location_id, date DESC);

-- ============================================================================
-- ECONOMIC SCHEMA (Macro indicators)
-- ============================================================================

CREATE TABLE IF NOT EXISTS economic.indicators (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    indicator_name VARCHAR(100) NOT NULL,  -- CPI, PPI, Unemployment, etc.
    value DECIMAL(15, 4) NOT NULL,
    region VARCHAR(50) DEFAULT 'USA',  -- National, regional, or state-level
    source VARCHAR(50),  -- FRED, BLS, etc.
    metadata JSONB,
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('economic.indicators', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_econ_indicator ON economic.indicators (indicator_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_econ_region ON economic.indicators (region, timestamp DESC);

-- Commodity prices (raw materials)
CREATE TABLE IF NOT EXISTS economic.commodity_prices (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    commodity_name VARCHAR(100) NOT NULL,  -- oil, steel, plastic, etc.
    price DECIMAL(12, 4) NOT NULL,
    unit VARCHAR(20),  -- per barrel, per ton, etc.
    exchange VARCHAR(50),
    metadata JSONB,
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('economic.commodity_prices', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_commodity ON economic.commodity_prices (commodity_name, timestamp DESC);

-- ============================================================================
-- FORECASTS SCHEMA (Model predictions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS forecasts.demand_predictions (
    id BIGSERIAL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    sku_id VARCHAR(50) NOT NULL REFERENCES sales.skus(id),
    location_id VARCHAR(50) NOT NULL REFERENCES sales.locations(id),
    forecast_date DATE NOT NULL,  -- The date being forecasted
    model_version VARCHAR(100) NOT NULL,
    model_type forecast_model_type NOT NULL,
    predicted_demand DECIMAL(12, 2) NOT NULL,
    lower_bound DECIMAL(12, 2),
    upper_bound DECIMAL(12, 2),
    confidence_level DECIMAL(5, 2) DEFAULT 0.95,
    recommended_stock_level INTEGER,
    features_used JSONB,  -- Feature importance, values
    metadata JSONB,
    PRIMARY KEY (id, created_at)
);

SELECT create_hypertable('forecasts.demand_predictions', 'created_at', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_forecasts_org_sku ON forecasts.demand_predictions (organization_id, sku_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecasts_model ON forecasts.demand_predictions (model_type, model_version);

-- Forecast accuracy tracking (compare predictions vs actuals)
CREATE TABLE IF NOT EXISTS forecasts.accuracy_metrics (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    model_version VARCHAR(100) NOT NULL,
    model_type forecast_model_type NOT NULL,
    evaluation_date DATE NOT NULL,
    sku_id VARCHAR(50),
    location_id VARCHAR(50),
    mape DECIMAL(8, 4),  -- Mean Absolute Percentage Error
    rmse DECIMAL(12, 4),  -- Root Mean Squared Error
    mae DECIMAL(12, 4),   -- Mean Absolute Error
    bias DECIMAL(8, 4),   -- Forecast bias (over/under forecasting)
    samples_count INTEGER,
    metadata JSONB,
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('forecasts.accuracy_metrics', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_accuracy_model ON forecasts.accuracy_metrics (model_type, evaluation_date DESC);

-- Weather-driven alerts
CREATE TABLE IF NOT EXISTS forecasts.weather_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    severity alert_severity NOT NULL,
    region VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,  -- HEATWAVE, EARLY_SPRING, etc.
    forecast_summary TEXT,
    demand_impact_pct DECIMAL(6, 2),
    revenue_at_risk DECIMAL(12, 2),
    recommended_actions JSONB,  -- Array of action items
    expires_at TIMESTAMPTZ,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_org_severity ON forecasts.weather_alerts (organization_id, severity, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON forecasts.weather_alerts (expires_at) WHERE acknowledged = false;

-- ============================================================================
-- ML METADATA SCHEMA (Model versioning, experiments)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_metadata.model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    model_name VARCHAR(100) NOT NULL,
    model_type forecast_model_type NOT NULL,
    version VARCHAR(50) NOT NULL,
    training_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hyperparameters JSONB,
    features JSONB,  -- List of features used
    training_samples INTEGER,
    validation_samples INTEGER,
    test_accuracy JSONB,  -- MAPE, RMSE, etc.
    mlflow_run_id VARCHAR(100),
    artifact_path TEXT,
    is_production BOOLEAN DEFAULT false,
    deployed_at TIMESTAMPTZ,
    deprecated_at TIMESTAMPTZ,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_models_org_type ON ml_metadata.model_versions (organization_id, model_type);
CREATE INDEX IF NOT EXISTS idx_models_production ON ml_metadata.model_versions (is_production, model_type);

-- Feature store (precomputed features for fast inference)
CREATE TABLE IF NOT EXISTS ml_metadata.feature_store (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    organization_id UUID NOT NULL REFERENCES tenants.organizations(id),
    sku_id VARCHAR(50) NOT NULL,
    location_id VARCHAR(50),
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(15, 6),
    feature_metadata JSONB,
    PRIMARY KEY (id, timestamp)
);

SELECT create_hypertable('ml_metadata.feature_store', 'timestamp', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_features_org_sku ON ml_metadata.feature_store (organization_id, sku_id, feature_name, timestamp DESC);

-- ============================================================================
-- CONTINUOUS AGGREGATES (TimescaleDB materialized views for performance)
-- ============================================================================

-- Daily sales aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS sales.daily_sales
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    organization_id,
    sku_id,
    location_id,
    SUM(quantity) AS total_quantity,
    SUM(total_price) AS total_revenue,
    AVG(unit_price) AS avg_price,
    COUNT(*) AS transaction_count
FROM sales.transactions
GROUP BY day, organization_id, sku_id, location_id
WITH NO DATA;

-- Refresh policy (update every hour)
SELECT add_continuous_aggregate_policy('sales.daily_sales',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Weekly inventory summary
CREATE MATERIALIZED VIEW IF NOT EXISTS inventory.weekly_inventory
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 week', timestamp) AS week,
    organization_id,
    sku_id,
    location_id,
    AVG(quantity_available) AS avg_available,
    MIN(quantity_available) AS min_available,
    MAX(quantity_available) AS max_available,
    AVG(safety_stock_level) AS avg_safety_stock
FROM inventory.stock_levels
GROUP BY week, organization_id, sku_id, location_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('inventory.weekly_inventory',
    start_offset => INTERVAL '2 weeks',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Automatically update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON tenants.organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skus_updated_at BEFORE UPDATE ON sales.skus
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate forecast accuracy
CREATE OR REPLACE FUNCTION calculate_forecast_accuracy(
    p_organization_id UUID,
    p_model_version VARCHAR,
    p_evaluation_date DATE
)
RETURNS TABLE(mape DECIMAL, rmse DECIMAL, mae DECIMAL, bias DECIMAL) AS $$
BEGIN
    RETURN QUERY
    SELECT
        AVG(ABS((actual - predicted) / NULLIF(actual, 0))) * 100 AS mape,
        SQRT(AVG(POWER(actual - predicted, 2))) AS rmse,
        AVG(ABS(actual - predicted)) AS mae,
        AVG(predicted - actual) AS bias
    FROM (
        SELECT
            f.predicted_demand AS predicted,
            COALESCE(SUM(s.quantity), 0) AS actual
        FROM forecasts.demand_predictions f
        LEFT JOIN sales.transactions s
            ON f.sku_id = s.sku_id
            AND f.location_id = s.location_id
            AND f.forecast_date = DATE(s.timestamp)
        WHERE f.organization_id = p_organization_id
            AND f.model_version = p_model_version
            AND f.forecast_date = p_evaluation_date
        GROUP BY f.id, f.predicted_demand
    ) accuracy_calc;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA SEEDING (Optional, for development)
-- ============================================================================

-- Insert demo organization
INSERT INTO tenants.organizations (id, name, subdomain, plan_tier)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'Demo Organization',
    'demo',
    'enterprise'
) ON CONFLICT (id) DO NOTHING;

-- Logging
\echo 'Database schema created successfully with TimescaleDB hypertables'
\echo 'Schemas: sales, inventory, forecasts, weather, economic, ml_metadata, tenants'
\echo 'Continuous aggregates created for performance optimization'
