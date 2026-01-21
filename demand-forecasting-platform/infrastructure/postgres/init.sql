-- Initialize PostgreSQL database for Demand Forecasting Platform
-- This script runs automatically when the Docker container starts

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable PostGIS for geospatial data (optional, for location-based features)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas for different domains
CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS inventory;
CREATE SCHEMA IF NOT EXISTS forecasts;
CREATE SCHEMA IF NOT EXISTS weather;
CREATE SCHEMA IF NOT EXISTS economic;
CREATE SCHEMA IF NOT EXISTS ml_metadata;
CREATE SCHEMA IF NOT EXISTS tenants;

-- Set search path
SET search_path TO public, sales, inventory, forecasts, weather, economic, ml_metadata, tenants;

-- Create custom types
CREATE TYPE forecast_model_type AS ENUM ('prophet', 'xgboost', 'lstm', 'ensemble');
CREATE TYPE alert_severity AS ENUM ('critical', 'warning', 'info');
CREATE TYPE inventory_status AS ENUM ('normal', 'low', 'critical', 'excess');
CREATE TYPE transfer_status AS ENUM ('pending', 'in_transit', 'completed', 'cancelled');

-- Grant privileges
GRANT ALL PRIVILEGES ON SCHEMA sales TO forecasting_user;
GRANT ALL PRIVILEGES ON SCHEMA inventory TO forecasting_user;
GRANT ALL PRIVILEGES ON SCHEMA forecasts TO forecasting_user;
GRANT ALL PRIVILEGES ON SCHEMA weather TO forecasting_user;
GRANT ALL PRIVILEGES ON SCHEMA economic TO forecasting_user;
GRANT ALL PRIVILEGES ON SCHEMA ml_metadata TO forecasting_user;
GRANT ALL PRIVILEGES ON SCHEMA tenants TO forecasting_user;

-- Logging
\echo 'Database initialization complete. TimescaleDB extension enabled.'
\echo 'Schemas created: sales, inventory, forecasts, weather, economic, ml_metadata, tenants'
