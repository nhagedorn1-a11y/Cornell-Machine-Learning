"""
Main Streamlit Dashboard - Weather-Centric Supply Chain Command Center
With GPT/Claude AI Integration Sections
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supply_chain_optimizer import SupplyChainOptimizer

# Page configuration
st.set_page_config(
    page_title="Supply Chain Command Center",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .alert-critical {
        background-color: #ffe6e6;
        border-left: 5px solid #ff4444;
    }
    .alert-warning {
        background-color: #fff9e6;
        border-left: 5px solid #ffbb33;
    }
    .alert-info {
        background-color: #e6f7ff;
        border-left: 5px solid #44aaff;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .ai-chat-container {
        background-color: #f0f8ff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #4a90e2;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'optimizer' not in st.session_state:
    st.session_state.optimizer = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'ai_api_key' not in st.session_state:
    st.session_state.ai_api_key = None
if 'ai_provider' not in st.session_state:
    st.session_state.ai_provider = 'OpenAI'
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar - Configuration & AI Setup
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/1f77b4/ffffff?text=Weather+AI", use_column_width=True)
    st.title("⚙️ Configuration")

    # Data Source Section
    st.header("📊 Data Source")
    data_source = st.radio(
        "Select Data Source",
        ["Generate Sample Data", "Upload CSV Files", "Connect to Database"]
    )

    if data_source == "Generate Sample Data":
        if st.button("🎲 Generate Demo Data", use_container_width=True):
            with st.spinner("Generating realistic sample data..."):
                st.session_state.optimizer = SupplyChainOptimizer()
                st.session_state.optimizer.generate_sample_data(
                    num_stores=5,
                    num_products=10,
                    days_history=365
                )
                st.session_state.data_loaded = True
                st.success("✅ Sample data generated!")
                st.rerun()

    elif data_source == "Upload CSV Files":
        st.file_uploader("Sales Data (CSV)", type=['csv'], key='sales_upload')
        st.file_uploader("Inventory Data (CSV)", type=['csv'], key='inventory_upload')
        st.file_uploader("Weather Data (CSV)", type=['csv'], key='weather_upload')

    else:  # Database
        st.text_input("Database Connection String", type="password")
        st.button("🔌 Connect", use_container_width=True)

    st.divider()

    # AI Integration Section
    st.header("🤖 AI Assistant")
    st.markdown("**Interactive Strategic Guidance**")

    ai_provider = st.selectbox(
        "AI Provider",
        ["OpenAI (GPT-4)", "Anthropic (Claude)", "None"]
    )

    if ai_provider != "None":
        api_key = st.text_input(
            f"{ai_provider} API Key",
            type="password",
            help="Your API key will be stored securely in session state only"
        )

        if api_key:
            st.session_state.ai_api_key = api_key
            st.session_state.ai_provider = ai_provider
            st.success(f"✅ {ai_provider} connected!")
        else:
            st.info("💡 Enter your API key to enable AI-powered insights")

    st.divider()

    # Settings
    st.header("🎛️ Settings")
    forecast_horizon = st.slider("Forecast Horizon (days)", 7, 180, 90)
    service_level = st.slider("Service Level Target", 0.90, 0.99, 0.95, 0.01)

    st.divider()

    # Quick Stats (if data loaded)
    if st.session_state.data_loaded and st.session_state.optimizer:
        st.header("📈 Quick Stats")
        optimizer = st.session_state.optimizer
        st.metric("Sales Records", f"{len(optimizer.sales_data):,}")
        st.metric("Products", optimizer.sales_data['product_sku'].nunique())
        st.metric("Locations", optimizer.sales_data['store_id'].nunique())

# Main Content
if not st.session_state.data_loaded:
    # Welcome Screen
    st.markdown('<h1 class="main-header">🌦️ Weather-Driven Supply Chain Command Center</h1>', unsafe_allow_html=True)

    st.markdown("""
    ### Welcome to the Future of Supply Chain Management

    This platform uses **weather forecasting** and **AI-powered analytics** to predict demand
    and optimize your supply chain **before** events happen.

    #### Key Features:
    - 🌡️ **Weather Intelligence**: 14-day forecasts driving demand predictions
    - 🤖 **AI Strategic Advisor**: Chat with GPT-4 or Claude about your supply chain
    - 📊 **Real-Time Alerts**: Get notified of demand surges before they happen
    - 🗺️ **National Deployment**: Optimize inventory across all locations
    - 💰 **ROI Tracking**: Every recommendation shows financial impact

    #### Get Started:
    1. Generate sample data from the sidebar (or upload your own)
    2. Optionally add your OpenAI or Claude API key for AI insights
    3. Explore the weather-driven recommendations

    ---
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("**🎯 For Executives**\nStrategic overview and financial impact")

    with col2:
        st.success("**📦 For Operations**\nActionable inventory and procurement orders")

    with col3:
        st.warning("**🌦️ For Planning**\nWeather-driven demand predictions")

    st.stop()

# Main Dashboard (Data Loaded)
optimizer = st.session_state.optimizer

st.markdown('<h1 class="main-header">🌦️ Supply Chain Command Center</h1>', unsafe_allow_html=True)

# Create tabs for different views
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌦️ Weather Alerts",
    "📊 Executive Dashboard",
    "🗺️ Deployment Map",
    "💬 AI Strategic Advisor",
    "📈 Analytics",
    "⚙️ Scenario Planning"
])

# TAB 1: Weather Alert Center
with tab1:
    st.header("⚡ Weather Alert Center - What's Coming & What It Means")

    # Generate weather alerts (sample data)
    alerts = [
        {
            'severity': 'critical',
            'region': 'Southeast (GA, FL, SC, AL)',
            'event': 'HEATWAVE DETECTED',
            'forecast': '8 days of 92-98°F starting March 18',
            'impact': '+280% demand for cooling products',
            'inventory_status': 'INSUFFICIENT (will stockout March 21)',
            'revenue_at_risk': '$1.2M',
            'actions': [
                'Order 4,500 units cooling products by March 12 (6-day lead time)',
                'Transfer 2,100 units from Seattle DC → Atlanta DC',
                'Increase digital ad spend 35% in affected regions',
                'Alert store managers: Staff up for surge'
            ]
        },
        {
            'severity': 'warning',
            'region': 'Midwest (OH, IN, IL, MI)',
            'event': 'EARLY SPRING SIGNAL',
            'forecast': 'Consistent 70°F+ temps, last frost March 28 (2 weeks early)',
            'impact': 'Planting season starts early → lawn care surge +40%',
            'inventory_status': 'Opportunity for additional revenue',
            'revenue_at_risk': '$3.4M opportunity',
            'actions': [
                'Advance fertilizer shipments by 14 days',
                'Order grass seed: +35% vs standard spring plan',
                'Notify buyers: Lock in commodity prices NOW',
                'Marketing: Launch "Early Spring Sale" campaign'
            ]
        },
        {
            'severity': 'info',
            'region': 'Pacific Northwest (WA, OR)',
            'event': 'DELAYED SEASON',
            'forecast': 'Cooler temps, rain through April',
            'impact': 'Outdoor products demand delayed 3-4 weeks',
            'inventory_status': 'Can reduce inventory (save carrying costs)',
            'revenue_at_risk': '$45K savings opportunity',
            'actions': [
                'Transfer 1,800 units from Seattle → Phoenix, Atlanta',
                'Delay Seattle restocks by 3 weeks',
                'Reduce Seattle ad spend 40% until May'
            ]
        }
    ]

    # Display alerts
    for alert in alerts:
        severity_class = f"alert-{alert['severity']}"
        severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🟢"}[alert['severity']]

        st.markdown(f"""
        <div class="alert-box {severity_class}">
            <h3>{severity_emoji} {alert['event'].upper()}</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.write(f"**Region:** {alert['region']}")
            st.write(f"**Forecast:** {alert['forecast']}")
            st.write(f"**Historical Impact:** {alert['impact']}")
            st.write(f"**Current Inventory:** {alert['inventory_status']}")

            st.write("**👉 Recommended Actions:**")
            for i, action in enumerate(alert['actions'], 1):
                st.write(f"{i}. {action}")

        with col2:
            st.metric("Revenue Impact", alert['revenue_at_risk'])

            if alert['severity'] == 'critical':
                if st.button(f"🚀 Execute All Actions", key=f"execute_{alert['region']}"):
                    st.success("✅ Actions queued for execution!")
            elif alert['severity'] == 'warning':
                if st.button(f"✅ Approve Plan", key=f"approve_{alert['region']}"):
                    st.success("✅ Plan approved!")
            else:
                if st.button(f"📦 Transfer Inventory", key=f"transfer_{alert['region']}"):
                    st.success("✅ Transfer initiated!")

        st.divider()

    # AI Insight Section for Weather Alerts
    if st.session_state.ai_api_key:
        st.subheader("🤖 AI Weather Analysis")

        with st.expander("💬 Ask AI About These Weather Alerts", expanded=False):
            st.markdown("""
            <div class="ai-chat-container">
                <p><strong>AI Assistant Ready</strong> - Ask questions like:</p>
                <ul>
                    <li>"What's the financial risk if we ignore the heatwave alert?"</li>
                    <li>"Should we prioritize the Southeast or Midwest opportunity?"</li>
                    <li>"How confident are these weather predictions?"</li>
                    <li>"What happened last time we had similar weather patterns?"</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            user_question = st.text_input("Ask the AI:", key="weather_ai_question")

            if user_question:
                with st.spinner(f"Consulting {st.session_state.ai_provider}..."):
                    # Placeholder for AI integration
                    st.info(f"🤖 {st.session_state.ai_provider} Response:")
                    st.write("""
                    **AI Analysis:** Based on historical data, the Southeast heatwave alert
                    represents the highest priority. The $1.2M revenue at risk combined with
                    only 6 days to respond creates urgency. I recommend:

                    1. **Immediate action on cooling products** (ROI: 25x)
                    2. **Midwest early spring is lower risk** but higher reward ($3.4M opportunity)
                    3. **Pacific Northwest transfer** is a cost-saving optimization

                    Priority: Southeast > Midwest > PNW

                    *[This is a placeholder. Connect your API key to get real AI responses]*
                    """)

# TAB 2: Executive Dashboard
with tab2:
    st.header("📊 Executive Overview - Strategic Intelligence")

    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "💰 Revenue",
            "$47.3M",
            "+18% YoY",
            delta_color="normal"
        )
        st.caption("✅ On Target")

    with col2:
        st.metric(
            "📦 Inventory",
            "$12.8M",
            "-$2.1M vs Plan",
            delta_color="inverse"
        )
        st.caption("✅ Optimized")

    with col3:
        st.metric(
            "🎯 Fill Rate",
            "94.2%",
            "+2.3%",
            delta_color="normal"
        )
        st.caption("🟡 Below 95% Target")

    with col4:
        st.metric(
            "⚠️ Alerts",
            "3 Critical",
            "12 Warning"
        )
        st.caption("🔴 Review Required")

    st.divider()

    # Sales Trend Chart
    st.subheader("📈 Sales Trend with Weather Overlay")

    # Generate sample chart data
    dates = pd.date_range(start='2025-01-01', periods=90, freq='D')
    sales_data = pd.DataFrame({
        'date': dates,
        'sales': np.random.normal(1000, 200, 90) + np.sin(np.arange(90) / 15) * 300,
        'temperature': np.random.normal(60, 15, 90)
    })

    # Create dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=sales_data['date'], y=sales_data['sales'],
                   name="Sales ($)", line=dict(color='#1f77b4', width=3)),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=sales_data['date'], y=sales_data['temperature'],
                   name="Temperature (°F)", line=dict(color='#ff7f0e', width=2, dash='dash')),
        secondary_y=True
    )

    fig.update_layout(
        title="Sales Correlation with Temperature",
        hovermode='x unified',
        height=400
    )

    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Sales ($)", secondary_y=False)
    fig.update_yaxes(title_text="Temperature (°F)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Strategic Actions Summary
    st.subheader("🎬 Strategic Actions This Week")

    actions_df = pd.DataFrame([
        {
            'Priority': '🔴 URGENT',
            'Action': 'Order $127K in commodities',
            'Deadline': 'March 15',
            'Revenue Impact': '$890K at risk'
        },
        {
            'Priority': '🟡 HIGH',
            'Action': 'Transfer 2,400 units Chicago → Atlanta',
            'Deadline': 'March 20',
            'Revenue Impact': '$180K protected'
        },
        {
            'Priority': '🟢 MEDIUM',
            'Action': 'Increase digital ad spend 25%',
            'Deadline': 'March 18',
            'Revenue Impact': '$320K expected return'
        }
    ])

    st.dataframe(actions_df, use_container_width=True, hide_index=True)

    # AI Executive Summary Section
    if st.session_state.ai_api_key:
        st.divider()
        st.subheader("🤖 AI Executive Summary")

        with st.expander("💬 Get AI Strategic Briefing", expanded=False):
            st.markdown("""
            <div class="ai-chat-container">
                <p><strong>Generate custom executive briefings with AI</strong></p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("📝 Generate Executive Briefing", use_container_width=True):
                with st.spinner("AI is analyzing your supply chain..."):
                    st.success("📄 Executive Briefing Generated")
                    st.markdown("""
                    **Strategic Summary - Week of March 10, 2026**

                    **Key Findings:**
                    - Weather patterns indicate 3 significant demand events in next 14 days
                    - $4.6M in value at stake (revenue protection + cost savings)
                    - ROI on recommended actions: 23x average

                    **Critical Decision Required:**
                    Southeast heatwave preparation needs $127K investment by March 15.
                    Delay = $890K revenue loss. **Recommend immediate approval.**

                    **Opportunities:**
                    Early Midwest spring presents $3.4M upside. Position inventory now.

                    *[Connect API for full AI-generated briefings]*
                    """)

# TAB 3: Deployment Map
with tab3:
    st.header("🗺️ National Deployment Map - Inventory Intelligence")

    st.info("📍 **Interactive Map**: Click regions for detailed inventory recommendations")

    # Create sample map data
    locations = pd.DataFrame({
        'City': ['Seattle', 'Portland', 'Chicago', 'Columbus', 'Atlanta', 'Phoenix', 'Dallas'],
        'lat': [47.6, 45.5, 41.9, 40.0, 33.7, 33.4, 32.8],
        'lon': [-122.3, -122.7, -87.6, -83.0, -84.4, -112.1, -96.8],
        'Inventory': [1850, 1420, 1680, 2100, 1240, 980, 1560],
        'Demand_Forecast': [2800, 2100, 3750, 3900, 4650, 4200, 3300],
        'Status': ['Low Priority', 'Low Priority', 'Normal', 'Normal', 'HIGH PRIORITY', 'HIGH PRIORITY', 'Normal']
    })

    # Color code by status
    locations['Color'] = locations['Status'].map({
        'HIGH PRIORITY': '#ff4444',
        'Normal': '#ffbb33',
        'Low Priority': '#44ff44'
    })

    locations['Size'] = locations['Demand_Forecast'] / 100

    fig = px.scatter_mapbox(
        locations,
        lat='lat',
        lon='lon',
        size='Size',
        color='Status',
        hover_name='City',
        hover_data={
            'Inventory': True,
            'Demand_Forecast': True,
            'Status': True,
            'lat': False,
            'lon': False,
            'Size': False
        },
        color_discrete_map={
            'HIGH PRIORITY': '#ff4444',
            'Normal': '#ffbb33',
            'Low Priority': '#44ff44'
        },
        zoom=3,
        height=500
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        title="Regional Demand Forecast vs Current Inventory"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Regional Breakdown Table
    st.subheader("📊 Regional Inventory Targets")

    regional_data = pd.DataFrame([
        {
            'Region': '📍 Atlanta DC',
            'Current': 1240,
            'Target': 4650,
            'Gap': -3410,
            'Action': 'SHIP 3,410 units by March 28',
            'Priority': '🔴 HIGH'
        },
        {
            'Region': '📍 Phoenix DC',
            'Current': 980,
            'Target': 4200,
            'Gap': -3220,
            'Action': 'SHIP 3,220 units by March 28',
            'Priority': '🔴 HIGH'
        },
        {
            'Region': '📍 Columbus DC',
            'Current': 2100,
            'Target': 3900,
            'Gap': -1800,
            'Action': 'SHIP 1,800 units by April 5',
            'Priority': '🟡 NORMAL'
        },
        {
            'Region': '📍 Seattle DC',
            'Current': 1850,
            'Target': 2800,
            'Gap': -950,
            'Action': 'SHIP 950 units by April 10',
            'Priority': '🟢 LOW'
        }
    ])

    st.dataframe(regional_data, use_container_width=True, hide_index=True)

# TAB 4: AI Strategic Advisor (Main AI Chat Interface)
with tab4:
    st.header("💬 AI Strategic Advisor - Interactive Supply Chain Guidance")

    if not st.session_state.ai_api_key:
        st.warning("⚠️ Please configure your AI API key in the sidebar to use this feature")

        st.markdown("""
        ### What You Can Do With AI Advisor:

        **Ask Strategic Questions:**
        - "What's my biggest risk in the next 30 days?"
        - "Should I approve the $127K commodity order?"
        - "How do I prepare for an early spring season?"

        **Get Financial Analysis:**
        - "Calculate ROI for the Atlanta transfer"
        - "What's the cost of delaying this decision?"
        - "Compare scenario A vs scenario B"

        **Scenario Planning:**
        - "What if there's a polar vortex?"
        - "Model a 20% price increase on commodities"
        - "Simulate competitor stockout scenario"

        **Historical Insights:**
        - "What happened last time we had this weather pattern?"
        - "Show me similar situations from past years"
        - "What did we do right/wrong in Q2 2025?"
        """)

    else:
        # AI Chat Interface
        st.success(f"✅ {st.session_state.ai_provider} Connected - AI Advisor Ready")

        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        user_input = st.chat_input("Ask your AI advisor anything about your supply chain...")

        if user_input:
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # Display user message
            with st.chat_message("user"):
                st.write(user_input)

            # Generate AI response (placeholder)
            with st.chat_message("assistant"):
                with st.spinner(f"Consulting {st.session_state.ai_provider}..."):
                    # TODO: Integrate actual API call here
                    ai_response = f"""
                    **AI Analysis:** Great question! Based on your current supply chain data:

                    {user_input}

                    Here's my recommendation:
                    1. Prioritize weather-driven actions in Southeast (highest ROI: 25x)
                    2. Early spring Midwest opportunity worth $3.4M
                    3. Consider commodity price hedging given forecasted demand

                    Would you like me to generate a detailed financial model for this scenario?

                    *[This is a placeholder response. API integration coming next]*
                    """

                    st.write(ai_response)

                    # Add AI response to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": ai_response
                    })

        st.divider()

        # Quick Action Buttons
        st.subheader("⚡ Quick AI Queries")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📊 Summarize All Alerts", use_container_width=True):
                st.info("AI will analyze all weather alerts and prioritize actions...")

        with col2:
            if st.button("💰 Calculate Total ROI", use_container_width=True):
                st.info("AI will compute financial impact of all recommendations...")

        with col3:
            if st.button("🎲 Run What-If Scenario", use_container_width=True):
                st.info("AI will help you model alternative scenarios...")

# TAB 5: Analytics Deep Dive
with tab5:
    st.header("📈 Analytics & Insights")

    st.subheader("🌡️ Weather Correlation Analysis")

    # Weather correlation chart
    correlation_data = pd.DataFrame({
        'Factor': ['Temperature', 'Rainfall', 'Growing Degree Days', 'Weekend Effect', 'Paycheck Cycle'],
        'Correlation': [0.87, 0.43, 0.78, 0.52, 0.38]
    })

    fig = px.bar(
        correlation_data,
        x='Correlation',
        y='Factor',
        orientation='h',
        title='Weather & Seasonal Factors - Correlation with Demand',
        color='Correlation',
        color_continuous_scale='RdYlGn'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info("""
    💡 **Key Insight**: Temperature is 87% predictive of demand
    - Every 10°F increase = +35% sales
    - 70°F is threshold (demand accelerates above this)
    - Use 14-day temp forecast as PRIMARY planning input
    """)

    st.divider()

    # Product performance
    st.subheader("📦 Product Performance")

    product_data = pd.DataFrame({
        'Product': [f'Product {i}' for i in range(1, 11)],
        'Sales': np.random.randint(50000, 200000, 10),
        'Margin': np.random.uniform(0.25, 0.55, 10),
        'Inventory_Days': np.random.randint(15, 60, 10)
    })

    fig = px.scatter(
        product_data,
        x='Sales',
        y='Margin',
        size='Inventory_Days',
        hover_data=['Product'],
        title='Product Portfolio Analysis',
        labels={'Margin': 'Profit Margin', 'Sales': 'Total Sales ($)'}
    )

    st.plotly_chart(fig, use_container_width=True)

# TAB 6: Scenario Planning
with tab6:
    st.header("🎲 Scenario Planning - What-If Analysis")

    st.markdown("""
    Model different scenarios to understand risks and opportunities.
    AI can help you explore "what if" questions about your supply chain.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Define Scenario")

        scenario_type = st.selectbox(
            "Scenario Type",
            [
                "Weather Event",
                "Competitor Action",
                "Price Change",
                "Supply Disruption",
                "Demand Surge",
                "Custom Scenario"
            ]
        )

        if scenario_type == "Weather Event":
            event = st.selectbox(
                "Weather Event",
                ["Heatwave", "Cold Snap", "Early Spring", "Late Frost", "Drought", "Heavy Rain"]
            )

            severity = st.slider("Severity (1-10)", 1, 10, 7)
            duration = st.slider("Duration (days)", 1, 30, 7)

        if st.button("🚀 Run Scenario Simulation", use_container_width=True):
            with st.spinner("AI is simulating scenario..."):
                st.session_state.scenario_result = {
                    'type': scenario_type,
                    'revenue_impact': np.random.uniform(-2000000, 5000000),
                    'cost_impact': np.random.uniform(50000, 500000),
                    'inventory_impact': np.random.uniform(-1000000, 2000000)
                }

    with col2:
        st.subheader("📊 Scenario Results")

        if 'scenario_result' in st.session_state:
            result = st.session_state.scenario_result

            st.metric("Revenue Impact", f"${result['revenue_impact']:,.0f}")
            st.metric("Cost Impact", f"${result['cost_impact']:,.0f}")
            st.metric("Inventory Impact", f"${result['inventory_impact']:,.0f}")

            net_impact = result['revenue_impact'] - result['cost_impact']
            st.metric(
                "Net Financial Impact",
                f"${net_impact:,.0f}",
                delta=f"{(net_impact/result['cost_impact']*100):.1f}% ROI"
            )

            st.success("✅ Scenario simulation complete!")

            if st.session_state.ai_api_key:
                st.info("💬 Ask AI: 'What should I do to prepare for this scenario?'")
        else:
            st.info("👈 Configure and run a scenario to see results")

# Footer
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🌦️ Weather data updated every 6 hours")

with col2:
    st.caption("🤖 AI-powered insights & recommendations")

with col3:
    st.caption("📊 Real-time supply chain intelligence")
