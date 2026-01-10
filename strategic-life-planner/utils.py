"""
Utility functions for Strategic Life Planner
"""

import streamlit as st
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def apply_custom_css():
    """Apply McKinsey-style custom CSS"""
    st.markdown("""
    <style>
        /* McKinsey color palette */
        :root {
            --primary-navy: #003D5B;
            --secondary-teal: #00A3A1;
            --accent-gold: #F4B942;
            --status-green: #2D9B4B;
            --status-yellow: #F4B942;
            --status-red: #D9534F;
            --bg-light: #F5F7FA;
        }

        /* Main container styling */
        .main {
            background-color: white;
        }

        /* Headers */
        h1 {
            color: var(--primary-navy);
            font-weight: 700;
            padding-bottom: 1rem;
            border-bottom: 3px solid var(--accent-gold);
        }

        h2 {
            color: var(--primary-navy);
            font-weight: 600;
            margin-top: 2rem;
        }

        h3 {
            color: var(--secondary-teal);
            font-weight: 600;
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-navy);
        }

        [data-testid="stMetricLabel"] {
            font-weight: 600;
            color: #666;
        }

        /* Cards */
        .dimension-card {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .dimension-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            border-color: var(--secondary-teal);
        }

        /* Buttons */
        .stButton > button {
            background-color: var(--secondary-teal);
            color: white;
            font-weight: 600;
            border-radius: 4px;
            border: none;
            padding: 0.5rem 2rem;
        }

        .stButton > button:hover {
            background-color: var(--primary-navy);
        }

        /* Progress bars */
        .stProgress > div > div {
            background-color: var(--secondary-teal);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: var(--bg-light);
        }

        /* Success/Info boxes */
        .stSuccess {
            background-color: #e8f5e9;
            border-left: 4px solid var(--status-green);
        }

        .stInfo {
            background-color: #e3f2fd;
            border-left: 4px solid var(--secondary-teal);
        }

        .stWarning {
            background-color: #fff8e1;
            border-left: 4px solid var(--status-yellow);
        }

        /* Tables */
        .dataframe {
            font-size: 0.9rem;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            background-color: var(--bg-light);
            border-radius: 4px;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)


def create_dimension_radar_chart(dimension_scores: Dict[str, float], title: str = "Life Balance Overview") -> go.Figure:
    """Create a radar chart for life dimension scores"""
    dimensions = list(dimension_scores.keys())
    scores = list(dimension_scores.values())

    # Close the plot by repeating the first value
    dimensions_plot = dimensions + [dimensions[0]]
    scores_plot = scores + [scores[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores_plot,
        theta=dimensions_plot,
        fill='toself',
        fillcolor='rgba(0, 163, 161, 0.3)',
        line=dict(color='#00A3A1', width=2),
        name='Current Scores'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=10)
            )
        ),
        showlegend=False,
        title=dict(text=title, x=0.5, font=dict(size=16, color='#003D5B')),
        height=400,
        margin=dict(t=80, b=40, l=40, r=40)
    )

    return fig


def create_kpi_progress_chart(kpi_history: List[Dict], kpi_name: str) -> go.Figure:
    """Create a line chart for KPI progress over time"""
    if not kpi_history:
        return None

    df = pd.DataFrame(kpi_history)
    df['recorded_date'] = pd.to_datetime(df['recorded_date'])
    df = df.sort_values('recorded_date')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['recorded_date'],
        y=df['value'],
        mode='lines+markers',
        line=dict(color='#00A3A1', width=3),
        marker=dict(size=8, color='#003D5B'),
        name=kpi_name
    ))

    fig.update_layout(
        title=dict(text=f"{kpi_name} Progress", font=dict(size=14)),
        xaxis_title="Date",
        yaxis_title="Value",
        height=300,
        margin=dict(t=40, b=40, l=40, r=40),
        hovermode='x unified'
    )

    return fig


def create_lever_heatmap(user_id: int, lever_ids: List[int], days: int = 30) -> go.Figure:
    """Create a GitHub-style contribution heatmap for levers"""
    from database import get_connection
    import json

    # This is a simplified version - would need actual daily tracking data
    # For MVP, showing a placeholder
    dates = pd.date_range(end=date.today(), periods=days)
    data = []

    for lever_id in lever_ids[:5]:  # Limit to 5 levers for display
        # Generate sample data (would be replaced with real data)
        values = [1 if i % 3 != 0 else 0 for i in range(days)]
        data.append(values)

    fig = go.Figure(data=go.Heatmap(
        z=data,
        x=dates,
        y=[f"Lever {i+1}" for i in range(len(data))],
        colorscale=[[0, '#eee'], [1, '#00A3A1']],
        showscale=False
    ))

    fig.update_layout(
        title="Lever Consistency (Last 30 Days)",
        height=250,
        margin=dict(t=40, b=40, l=100, r=40)
    )

    return fig


def create_dimension_trend_chart(dimension_scores_history: Dict[str, List[float]]) -> go.Figure:
    """Create a multi-line chart showing dimension trends over time"""
    fig = go.Figure()

    colors = {
        'Career': '#003D5B',
        'Health': '#00A3A1',
        'Finance': '#F4B942',
        'Relationships': '#D9534F',
        'Personal Growth': '#2D9B4B',
        'Impact': '#9C27B0'
    }

    for dimension, scores in dimension_scores_history.items():
        if scores:
            fig.add_trace(go.Scatter(
                y=scores,
                mode='lines+markers',
                name=dimension,
                line=dict(width=2, color=colors.get(dimension, '#666')),
                marker=dict(size=6)
            ))

    fig.update_layout(
        title="Dimension Trends Over Time",
        xaxis_title="Week",
        yaxis_title="Score (1-10)",
        yaxis=dict(range=[0, 10]),
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def format_date(date_obj: any) -> str:
    """Format date for display"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj).date()
        except:
            return date_obj

    if isinstance(date_obj, (date, datetime)):
        return date_obj.strftime("%B %d, %Y")

    return str(date_obj)


def get_priority_color(priority: str) -> str:
    """Get color for priority badge"""
    colors = {
        'High': '🔴',
        'Medium': '🟡',
        'Low': '🟢'
    }
    return colors.get(priority, '⚪')


def calculate_days_until(target_date: str) -> Optional[int]:
    """Calculate days until target date"""
    try:
        target = datetime.fromisoformat(target_date).date()
        today = date.today()
        delta = (target - today).days
        return delta
    except:
        return None


def format_duration(days: int) -> str:
    """Format duration in human-readable format"""
    if days < 0:
        return f"{abs(days)} days overdue"
    elif days == 0:
        return "Today"
    elif days == 1:
        return "Tomorrow"
    elif days < 7:
        return f"{days} days"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''}"
    else:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''}"


def get_status_badge(status: str) -> str:
    """Get HTML badge for status"""
    colors = {
        'Not Started': ('#666', '⚪'),
        'In Progress': ('#F4B942', '🟡'),
        'At Risk': ('#D9534F', '🔴'),
        'Completed': ('#2D9B4B', '🟢')
    }

    color, emoji = colors.get(status, ('#666', '⚪'))

    return f"{emoji} {status}"


def create_progress_bar_html(progress: float, height: str = "20px") -> str:
    """Create custom HTML progress bar"""
    color = '#2D9B4B' if progress >= 80 else '#F4B942' if progress >= 50 else '#D9534F'

    return f"""
    <div style="background-color: #eee; border-radius: 10px; height: {height}; width: 100%; overflow: hidden;">
        <div style="background-color: {color}; height: 100%; width: {progress}%;
                    border-radius: 10px; transition: width 0.3s ease;
                    display: flex; align-items: center; justify-content: center;
                    color: white; font-weight: bold; font-size: 12px;">
            {progress:.0f}%
        </div>
    </div>
    """


def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1  # Default user for MVP

    if 'current_plan_id' not in st.session_state:
        st.session_state.current_plan_id = None

    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1

    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {}


def display_metric_card(label: str, value: str, delta: Optional[str] = None, emoji: str = ""):
    """Display a metric in a card format"""
    st.markdown(f"""
    <div class="dimension-card">
        <h4 style="color: #666; margin: 0; font-size: 0.9rem;">{emoji} {label}</h4>
        <p style="font-size: 2rem; font-weight: 700; color: #003D5B; margin: 0.5rem 0;">{value}</p>
        {f'<p style="color: #00A3A1; margin: 0; font-size: 0.9rem;">{delta}</p>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def get_quarter_dates(quarter: str, year: int) -> tuple:
    """Get start and end dates for a quarter"""
    quarter_dates = {
        'Q1': (date(year, 1, 1), date(year, 3, 31)),
        'Q2': (date(year, 4, 1), date(year, 6, 30)),
        'Q3': (date(year, 7, 1), date(year, 9, 30)),
        'Q4': (date(year, 10, 1), date(year, 12, 31))
    }
    return quarter_dates.get(quarter, (date(year, 1, 1), date(year, 3, 31)))


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def export_plan_to_text(plan_data: Dict) -> str:
    """Export quarterly plan to formatted text"""
    output = []
    output.append(f"QUARTERLY PLAN: {plan_data.get('quarter')} {plan_data.get('year')}")
    output.append("=" * 60)
    output.append("")

    if plan_data.get('vision_statement'):
        output.append("VISION:")
        output.append(plan_data['vision_statement'])
        output.append("")

    output.append("OBJECTIVES:")
    # Would iterate through objectives and format them

    return "\n".join(output)
