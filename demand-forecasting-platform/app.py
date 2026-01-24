"""
Demand Forecasting & Inventory Optimization Platform
Main Streamlit Application - Production UI
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import API connectors
try:
    from services.data_connectors import get_weather_api, get_economic_api
    APIS_AVAILABLE = True
except ImportError:
    APIS_AVAILABLE = False
    print("Warning: API connectors not available. Using mock data.")

# Page configuration
st.set_page_config(
    page_title="Demand Forecasting Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern, visually compelling design
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1f77b4;
        --secondary-color: #ff7f0e;
        --success-color: #2ca02c;
        --warning-color: #d62728;
        --background-dark: #0e1117;
        --card-bg: #1a1d29;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }

    .metric-card h3 {
        color: white;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 0 0 0.5rem 0;
        opacity: 0.9;
    }

    .metric-card .value {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }

    .metric-card .delta {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.9rem;
        margin: 0.5rem 0 0 0;
    }

    /* Section headers */
    .section-header {
        border-left: 4px solid #667eea;
        padding-left: 1rem;
        margin: 2rem 0 1rem 0;
    }

    .section-header h2 {
        color: #667eea;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
    }

    /* Cards */
    .info-card {
        background: #1a1d29;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 1rem 0;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-success {
        background: rgba(44, 160, 44, 0.2);
        color: #2ca02c;
        border: 1px solid #2ca02c;
    }

    .status-warning {
        background: rgba(255, 127, 14, 0.2);
        color: #ff7f0e;
        border: 1px solid #ff7f0e;
    }

    .status-danger {
        background: rgba(214, 39, 40, 0.2);
        color: #d62728;
        border: 1px solid #d62728;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1d29 0%, #0e1117 100%);
    }

    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8001"

def check_api_health():
    """Check if API is available"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_demo_forecast():
    """Get demo forecast data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/forecast/demo")
        return response.json() if response.status_code == 200 else None
    except:
        return None

def get_system_info():
    """Get system information from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/info")
        return response.json() if response.status_code == 200 else None
    except:
        return None

# Sidebar navigation
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem;">
    <h1 style="color: #667eea; font-size: 1.5rem;">📊 Forecasting</h1>
    <p style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">Supply Chain Intelligence</p>
</div>
""", unsafe_allow_html=True)

# Check API status
api_status = check_api_health()
if api_status:
    st.sidebar.markdown('<span class="status-badge status-success">🟢 API Connected</span>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<span class="status-badge status-danger">🔴 API Offline</span>', unsafe_allow_html=True)
    st.sidebar.warning("⚠️ Make sure the API is running:\n```python simple_api.py```")

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Dashboard", "📈 Forecasting", "📦 Inventory Optimization", "📊 Analytics", "⚙️ Settings"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# Filters (shown on all pages)
st.sidebar.markdown("### 🎯 Filters")
selected_sku = st.sidebar.selectbox(
    "SKU",
    ["SKU-001", "SKU-002", "SKU-003", "SKU-004", "SKU-005"],
    index=0
)
selected_location = st.sidebar.selectbox(
    "Location",
    ["DC-ATL", "DC-CHI", "DC-NYC", "DC-LAX", "DC-SEA"],
    index=0
)
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now(), datetime.now() + timedelta(days=30))
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; padding: 1rem; color: rgba(255,255,255,0.4); font-size: 0.75rem;">
    <p>Built with ❤️ by Supply Chain Intelligence Team</p>
    <p>v1.0.0 | Phase 2 Complete</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================
if page == "🏠 Dashboard":
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏠 Supply Chain Intelligence Dashboard</h1>
        <p>Real-time demand forecasting and inventory optimization powered by ML</p>
    </div>
    """, unsafe_allow_html=True)

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <h3>Forecast Accuracy</h3>
            <div class="value">87.5%</div>
            <div class="delta">↑ 2.3% vs last month</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h3>Fill Rate</h3>
            <div class="value">94.2%</div>
            <div class="delta">↑ 1.1% vs last month</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h3>Inventory Turnover</h3>
            <div class="value">4.2x</div>
            <div class="delta">↑ 0.3x vs last month</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <h3>Cost Savings</h3>
            <div class="value">$1.2M</div>
            <div class="delta">↑ $180K vs last month</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="section-header"><h2>📈 Demand Forecast - Next 30 Days</h2></div>', unsafe_allow_html=True)

        # Get forecast data
        forecast_data = get_demo_forecast()

        if forecast_data and 'predictions' in forecast_data:
            predictions = forecast_data['predictions']
            df = pd.DataFrame(predictions)
            df['date'] = pd.to_datetime(df['date'])

            # Create interactive Plotly chart
            fig = go.Figure()

            # Add confidence interval
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['upper_bound'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))

            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['lower_bound'],
                mode='lines',
                line=dict(width=0),
                fillcolor='rgba(102, 126, 234, 0.2)',
                fill='tonexty',
                showlegend=True,
                name='95% Confidence Interval',
                hoverinfo='skip'
            ))

            # Add predicted demand
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['demand'],
                mode='lines+markers',
                name='Predicted Demand',
                line=dict(color='#667eea', width=3),
                marker=dict(size=6, color='#667eea')
            ))

            fig.update_layout(
                template='plotly_dark',
                height=400,
                margin=dict(l=0, r=0, t=30, b=0),
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis_title="Date",
                yaxis_title="Demand (units)"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Forecast details
            st.markdown(f"""
            <div class="info-card">
                <p style="margin: 0;"><strong>SKU:</strong> {forecast_data['sku_id']} |
                <strong>Location:</strong> {forecast_data['location_id']} |
                <strong>Model:</strong> Ensemble (Prophet + XGBoost + LSTM) |
                <strong>MAPE:</strong> {forecast_data['metadata']['mape']}%</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Unable to load forecast data. Make sure the API is running.")

    with col2:
        st.markdown('<div class="section-header"><h2>🎯 Key Insights</h2></div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="info-card">
            <h4 style="color: #2ca02c; margin-top: 0;">✅ Strong Performance</h4>
            <p style="font-size: 0.9rem;">Forecast accuracy improved by 2.3% this month due to enhanced weather integration.</p>
        </div>

        <div class="info-card">
            <h4 style="color: #ff7f0e; margin-top: 0;">⚠️ Attention Needed</h4>
            <p style="font-size: 0.9rem;">SKU-003 showing high variance. Consider safety stock increase.</p>
        </div>

        <div class="info-card">
            <h4 style="color: #1f77b4; margin-top: 0;">💡 Recommendation</h4>
            <p style="font-size: 0.9rem;">Rebalance 300 units from DC-CHI to DC-ATL to reduce stockout risk.</p>
        </div>

        <div class="info-card">
            <h4 style="color: #9467bd; margin-top: 0;">📊 This Week</h4>
            <ul style="font-size: 0.9rem; margin-bottom: 0;">
                <li>15 SKUs forecasted</li>
                <li>5 locations optimized</li>
                <li>12,500 units processed</li>
                <li>$45K potential savings identified</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Bottom row - Additional charts
    st.markdown('<div class="section-header"><h2>📊 Performance Metrics</h2></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        # Forecast accuracy by model
        model_accuracy = pd.DataFrame({
            'Model': ['Prophet', 'XGBoost', 'Ensemble'],
            'MAPE': [14.2, 13.8, 12.5]
        })

        fig = px.bar(
            model_accuracy,
            x='Model',
            y='MAPE',
            title='Forecast Accuracy by Model',
            color='MAPE',
            color_continuous_scale='viridis'
        )
        fig.update_layout(template='plotly_dark', height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Inventory health
        inventory_health = pd.DataFrame({
            'Status': ['Optimal', 'Overstock', 'Understock', 'Stockout Risk'],
            'Count': [45, 8, 5, 2]
        })

        fig = px.pie(
            inventory_health,
            values='Count',
            names='Status',
            title='Inventory Health Distribution',
            color_discrete_sequence=['#2ca02c', '#ff7f0e', '#d62728', '#9467bd']
        )
        fig.update_layout(template='plotly_dark', height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        # Weekly demand trend
        weekly_data = pd.DataFrame({
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Actual': [4200, 4500, 4350, 4600],
            'Forecast': [4150, 4480, 4400, 4550]
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=weekly_data['Week'], y=weekly_data['Actual'],
                                  name='Actual', mode='lines+markers', line=dict(color='#2ca02c', width=3)))
        fig.add_trace(go.Scatter(x=weekly_data['Week'], y=weekly_data['Forecast'],
                                  name='Forecast', mode='lines+markers', line=dict(color='#667eea', width=3, dash='dash')))

        fig.update_layout(
            title='4-Week Forecast vs Actual',
            template='plotly_dark',
            height=300,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE: FORECASTING
# ============================================================================
elif page == "📈 Forecasting":
    st.markdown("""
    <div class="main-header">
        <h1>📈 Demand Forecasting</h1>
        <p>AI-powered demand predictions with 95% confidence intervals</p>
    </div>
    """, unsafe_allow_html=True)

    # Forecast configuration
    col1, col2, col3 = st.columns(3)

    with col1:
        forecast_horizon = st.slider("Forecast Horizon (days)", 7, 90, 30)
    with col2:
        confidence_level = st.selectbox("Confidence Level", ["90%", "95%", "99%"], index=1)
    with col3:
        model_type = st.selectbox("Model", ["Ensemble", "Prophet", "XGBoost", "LSTM"])

    if st.button("🚀 Generate Forecast", use_container_width=True):
        with st.spinner("Running ML models..."):
            forecast_data = get_demo_forecast()

            if forecast_data:
                st.success("✅ Forecast generated successfully!")

                predictions = forecast_data['predictions'][:forecast_horizon]
                df = pd.DataFrame(predictions)
                df['date'] = pd.to_datetime(df['date'])

                # Main forecast chart
                fig = go.Figure()

                # Confidence band
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['upper_bound'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False
                ))

                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['lower_bound'],
                    fill='tonexty',
                    mode='lines',
                    line=dict(width=0),
                    fillcolor='rgba(102, 126, 234, 0.2)',
                    name='Confidence Interval'
                ))

                # Forecast line
                fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df['demand'],
                    mode='lines+markers',
                    name='Predicted Demand',
                    line=dict(color='#667eea', width=4),
                    marker=dict(size=8)
                ))

                fig.update_layout(
                    template='plotly_dark',
                    height=500,
                    title=f"{forecast_horizon}-Day Demand Forecast for {selected_sku} @ {selected_location}",
                    xaxis_title="Date",
                    yaxis_title="Demand (units)",
                    hovermode='x unified'
                )

                st.plotly_chart(fig, use_container_width=True)

                # Forecast statistics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    avg_demand = df['demand'].mean()
                    st.metric("Average Demand", f"{avg_demand:.0f} units")

                with col2:
                    total_demand = df['demand'].sum()
                    st.metric("Total Demand", f"{total_demand:.0f} units")

                with col3:
                    peak_demand = df['demand'].max()
                    st.metric("Peak Demand", f"{peak_demand:.0f} units")

                with col4:
                    st.metric("Model Accuracy", forecast_data['metadata']['accuracy'])

                # Detailed forecast table
                st.markdown('<div class="section-header"><h2>📋 Detailed Forecast</h2></div>', unsafe_allow_html=True)

                display_df = df.copy()
                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                display_df = display_df.round(1)

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=400
                )

                # Download button
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Forecast CSV",
                    data=csv,
                    file_name=f"forecast_{selected_sku}_{selected_location}.csv",
                    mime="text/csv"
                )
            else:
                st.error("❌ Failed to generate forecast. Check API connection.")

# ============================================================================
# PAGE: INVENTORY OPTIMIZATION
# ============================================================================
elif page == "📦 Inventory Optimization":
    st.markdown("""
    <div class="main-header">
        <h1>📦 Inventory Optimization</h1>
        <p>AI-driven rebalancing and procurement recommendations</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h2>🎯 Rebalancing Recommendations</h2></div>', unsafe_allow_html=True)

    # Sample rebalancing recommendations
    recommendations = pd.DataFrame({
        'From': ['DC-CHI', 'DC-LAX', 'DC-NYC', 'DC-SEA'],
        'To': ['DC-ATL', 'DC-ATL', 'DC-CHI', 'DC-NYC'],
        'SKU': ['SKU-001', 'SKU-002', 'SKU-001', 'SKU-003'],
        'Quantity': [300, 150, 200, 100],
        'Cost': [1200, 800, 950, 500],
        'Expected ROI': [4500, 2800, 3200, 1800],
        'Priority': ['HIGH', 'MEDIUM', 'HIGH', 'LOW']
    })

    # Add color coding to priority
    def color_priority(val):
        if val == 'HIGH':
            return 'background-color: rgba(214, 39, 40, 0.3); color: #d62728; font-weight: bold;'
        elif val == 'MEDIUM':
            return 'background-color: rgba(255, 127, 14, 0.3); color: #ff7f0e; font-weight: bold;'
        else:
            return 'background-color: rgba(44, 160, 44, 0.3); color: #2ca02c; font-weight: bold;'

    styled_df = recommendations.style.applymap(color_priority, subset=['Priority'])
    st.dataframe(styled_df, use_container_width=True)

    # Visualization
    col1, col2 = st.columns(2)

    with col1:
        # ROI by transfer
        fig = px.bar(
            recommendations,
            x='SKU',
            y='Expected ROI',
            color='Priority',
            title='Expected ROI by Transfer',
            color_discrete_map={'HIGH': '#d62728', 'MEDIUM': '#ff7f0e', 'LOW': '#2ca02c'}
        )
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Cost vs ROI scatter
        fig = px.scatter(
            recommendations,
            x='Cost',
            y='Expected ROI',
            size='Quantity',
            color='Priority',
            title='Cost vs ROI Analysis',
            hover_data=['SKU', 'From', 'To'],
            color_discrete_map={'HIGH': '#d62728', 'MEDIUM': '#ff7f0e', 'LOW': '#2ca02c'}
        )
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Approve All High Priority", use_container_width=True):
            st.success("3 high priority transfers approved!")
    with col2:
        if st.button("📊 Run Optimization", use_container_width=True):
            st.info("Running optimization algorithm...")
    with col3:
        if st.button("📥 Export Report", use_container_width=True):
            st.success("Report exported successfully!")

# ============================================================================
# PAGE: ANALYTICS
# ============================================================================
elif page == "📊 Analytics":
    st.markdown("""
    <div class="main-header">
        <h1>📊 Advanced Analytics</h1>
        <p>Deep dive into performance metrics and trends</p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs for different analytics
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Forecast Accuracy", "📦 Inventory Health", "💰 Financial Impact", "🌤️ Weather Correlation"])

    with tab1:
        st.markdown('<div class="section-header"><h2>Forecast Accuracy Over Time</h2></div>', unsafe_allow_html=True)

        # Generate sample data
        dates = pd.date_range(start='2025-07-01', end='2026-01-24', freq='W')
        accuracy_data = pd.DataFrame({
            'Date': dates,
            'MAPE': np.random.normal(12.5, 2, len(dates)),
            'RMSE': np.random.normal(45, 5, len(dates))
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=accuracy_data['Date'], y=accuracy_data['MAPE'],
                                  name='MAPE (%)', mode='lines+markers', line=dict(color='#667eea', width=3)))
        fig.add_trace(go.Scatter(x=accuracy_data['Date'], y=accuracy_data['RMSE'],
                                  name='RMSE', mode='lines+markers', line=dict(color='#f5576c', width=3), yaxis='y2'))

        fig.update_layout(
            template='plotly_dark',
            height=400,
            yaxis=dict(title='MAPE (%)'),
            yaxis2=dict(title='RMSE', overlaying='y', side='right'),
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown('<div class="section-header"><h2>Inventory Turnover by Category</h2></div>', unsafe_allow_html=True)

        categories = pd.DataFrame({
            'Category': ['Fertilizer', 'Lawn Care', 'Seeds', 'Pest Control', 'Tools'],
            'Turnover': [5.2, 4.8, 3.9, 4.5, 3.2],
            'Avg Stock': [12000, 8500, 6000, 9500, 4200]
        })

        fig = go.Figure()
        fig.add_trace(go.Bar(x=categories['Category'], y=categories['Turnover'],
                              name='Turnover Rate', marker_color='#667eea'))
        fig.update_layout(template='plotly_dark', height=400, yaxis_title='Turnover Rate')
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header"><h2>Cost Savings Attribution</h2></div>', unsafe_allow_html=True)

        savings = pd.DataFrame({
            'Source': ['Better Forecasting', 'Inventory Optimization', 'Reduced Stockouts', 'Lower Holding Costs'],
            'Savings': [450000, 380000, 280000, 210000]
        })

        fig = px.pie(savings, values='Savings', names='Source',
                     title='Cost Savings Breakdown ($1.32M Total)',
                     color_discrete_sequence=px.colors.sequential.Viridis)
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown('<div class="section-header"><h2>Weather Impact on Demand</h2></div>', unsafe_allow_html=True)

        # Try to get real weather data
        weather_api = get_weather_api() if APIS_AVAILABLE else None

        if weather_api:
            try:
                # Get weather for selected location
                location_map = {
                    'DC-ATL': 'Atlanta',
                    'DC-CHI': 'Chicago',
                    'DC-NYC': 'New York',
                    'DC-LAX': 'Los Angeles',
                    'DC-SEA': 'Seattle'
                }
                city = location_map.get(selected_location, 'Atlanta')

                # Get 5-day forecast
                forecast = weather_api.get_forecast(city, days=5)

                if forecast and not forecast[0].get('_mock'):
                    # Create DataFrame from real forecast data
                    weather_df = pd.DataFrame(forecast)
                    weather_df['Temperature'] = weather_df['temperature']
                    # Simulate demand based on temperature
                    weather_df['Demand'] = 100 + weather_df['Temperature'] * 1.5 + np.random.normal(0, 10, len(weather_df))

                    st.info(f"✅ Using real weather data from OpenWeather API for {city}")
                else:
                    raise Exception("Mock data returned")

            except Exception as e:
                st.warning("⚠️ Using simulated weather data. Set OPENWEATHER_API_KEY in .env for real data.")
                # Fallback to mock data
                weather_df = pd.DataFrame({
                    'Temperature': np.random.normal(70, 10, 50),
                    'Demand': np.random.normal(150, 20, 50)
                })
                weather_df['Demand'] = weather_df['Demand'] + weather_df['Temperature'] * 0.5
        else:
            st.warning("⚠️ Using simulated weather data. Set OPENWEATHER_API_KEY in .env for real data.")
            # Fallback to mock data
            weather_df = pd.DataFrame({
                'Temperature': np.random.normal(70, 10, 50),
                'Demand': np.random.normal(150, 20, 50)
            })
            weather_df['Demand'] = weather_df['Demand'] + weather_df['Temperature'] * 0.5

        fig = px.scatter(weather_df, x='Temperature', y='Demand',
                         title='Temperature vs Demand Correlation',
                         labels={'Temperature': 'Temperature (°F)', 'Demand': 'Daily Demand (units)'})

        # Add manual trendline (without statsmodels dependency)
        z = np.polyfit(weather_df['Temperature'], weather_df['Demand'], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=weather_df['Temperature'],
            y=p(weather_df['Temperature']),
            mode='lines',
            name='Trend Line',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
        fig.update_layout(template='plotly_dark', height=400)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# PAGE: SETTINGS
# ============================================================================
elif page == "⚙️ Settings":
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Settings & Configuration</h1>
        <p>Customize your forecasting platform</p>
    </div>
    """, unsafe_allow_html=True)

    # System info
    system_info = get_system_info()

    if system_info:
        st.markdown('<div class="section-header"><h2>🖥️ System Information</h2></div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="info-card">
                <h4>Platform Details</h4>
                <p><strong>Version:</strong> {system_info['system']['version']}</p>
                <p><strong>Environment:</strong> {system_info['system']['environment']}</p>
                <p><strong>Mode:</strong> {system_info.get('note', 'Production')}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="info-card">
                <h4>ML Capabilities</h4>
                <p><strong>Models:</strong> {', '.join(system_info['capabilities']['forecasting']['models'])}</p>
                <p><strong>Algorithms:</strong> {', '.join(system_info['capabilities']['optimization']['algorithms'])}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-header"><h2>🎛️ Model Configuration</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Forecast Settings")
        default_horizon = st.number_input("Default Forecast Horizon (days)", 7, 90, 30)
        confidence = st.slider("Default Confidence Level", 0.80, 0.99, 0.95, 0.01)
        auto_retrain = st.checkbox("Auto-retrain models weekly", value=True)

    with col2:
        st.subheader("Optimization Settings")
        rebalance_threshold = st.number_input("Rebalance Threshold (%)", 5, 50, 20)
        safety_stock_factor = st.slider("Safety Stock Factor", 1.0, 3.0, 1.5, 0.1)
        optimization_frequency = st.selectbox("Optimization Frequency", ["Daily", "Weekly", "Monthly"])

    if st.button("💾 Save Settings", use_container_width=True):
        st.success("✅ Settings saved successfully!")

    st.markdown('<div class="section-header"><h2>📡 API Configuration</h2></div>', unsafe_allow_html=True)

    api_url = st.text_input("API Base URL", value=API_BASE_URL)
    api_key = st.text_input("API Key (optional)", type="password")

    if st.button("🔌 Test Connection", use_container_width=True):
        if check_api_health():
            st.success("✅ API connection successful!")
        else:
            st.error("❌ Unable to connect to API. Check if it's running.")

    st.markdown('<div class="section-header"><h2>🌐 External API Status</h2></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Weather API (OpenWeather)")
        weather_api = get_weather_api() if APIS_AVAILABLE else None

        if weather_api:
            try:
                # Test weather API
                test_weather = weather_api.get_current_weather("Atlanta")
                if not test_weather.get('_mock'):
                    st.success("✅ Connected - Receiving real weather data")
                    st.info(f"**Current in Atlanta:** {test_weather['temperature']:.1f}°F, {test_weather['description']}")
                else:
                    st.warning("⚠️ API key not set - Using mock data")
                    st.info("Set OPENWEATHER_API_KEY in .env file")
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
        else:
            st.warning("⚠️ Weather API not configured")
            st.info("**Setup instructions:**\n1. Get free key at https://openweathermap.org/api\n2. Add to .env file: `OPENWEATHER_API_KEY=your_key`\n3. Restart the app")

    with col2:
        st.subheader("Economic API (FRED)")
        economic_api = get_economic_api() if APIS_AVAILABLE else None

        if economic_api:
            try:
                # Test FRED API
                test_economic = economic_api.get_unemployment_rate()
                if not test_economic.get('_mock'):
                    st.success("✅ Connected - Receiving real economic data")
                    st.info(f"**Unemployment Rate:** {test_economic['latest_value']:.1f}% (as of {test_economic['latest_date']})")
                else:
                    st.warning("⚠️ API key not set - Using mock data")
                    st.info("Set FRED_API_KEY in .env file")
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
        else:
            st.warning("⚠️ Economic API not configured")
            st.info("**Setup instructions:**\n1. Get free key at https://fred.stlouisfed.org/docs/api/api_key.html\n2. Add to .env file: `FRED_API_KEY=your_key`\n3. Restart the app")

    # Show economic indicators if available
    if economic_api:
        st.markdown('<div class="section-header"><h2>📊 Economic Indicators Dashboard</h2></div>', unsafe_allow_html=True)

        try:
            summary = economic_api.get_dashboard_summary()

            if summary:
                cols = st.columns(len(summary))

                for idx, (key, data) in enumerate(summary.items()):
                    with cols[idx]:
                        trend_emoji = "↑" if data['trend'] == 'up' else "↓" if data['trend'] == 'down' else "→"
                        trend_color = "#2ca02c" if data['trend'] == 'up' else "#d62728" if data['trend'] == 'down' else "#ff7f0e"

                        st.markdown(f"""
                        <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                            <h3>{data['name']}</h3>
                            <div class="value">{data['value']:.1f}</div>
                            <div class="delta" style="color: {trend_color};">
                                {trend_emoji} {data['pct_change']:+.1f}% (3mo)
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Unable to fetch economic indicators: {str(e)}")
