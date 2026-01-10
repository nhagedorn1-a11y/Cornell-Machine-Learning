"""
Utility functions for Strategic Life Planner - Spotify Edition
WeChat data richness + Spotify aesthetics
"""

import streamlit as st
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def apply_spotify_theme():
    """Apply Spotify-inspired dark theme with modern aesthetics"""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Circular+Std:wght@300;400;500;700;900&display=swap');

        /* Spotify color palette */
        :root {
            --spotify-green: #1DB954;
            --spotify-dark: #121212;
            --spotify-darkgrey: #181818;
            --spotify-grey: #282828;
            --spotify-lightgrey: #B3B3B3;
            --spotify-white: #FFFFFF;
            --spotify-accent: #1ED760;
            --spotify-blue: #2E77D0;
            --spotify-purple: #8E44AD;
            --spotify-red: #E74C3C;
            --spotify-orange: #E67E22;
        }

        /* Global styling */
        * {
            font-family: 'Circular Std', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        /* Main app background */
        .main {
            background: linear-gradient(180deg, #121212 0%, #181818 100%);
            color: var(--spotify-white);
        }

        .stApp {
            background: linear-gradient(180deg, #121212 0%, #181818 100%);
        }

        /* Sidebar - Spotify left nav style */
        [data-testid="stSidebar"] {
            background-color: #000000;
            padding-top: 1rem;
        }

        [data-testid="stSidebar"] > div:first-child {
            background-color: #000000;
        }

        /* Headers - Spotify style */
        h1 {
            color: var(--spotify-white);
            font-weight: 900;
            font-size: 3rem;
            letter-spacing: -0.04em;
            margin-bottom: 1.5rem;
            padding-bottom: 0;
            border: none;
        }

        h2 {
            color: var(--spotify-white);
            font-weight: 700;
            font-size: 1.5rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }

        h3 {
            color: var(--spotify-white);
            font-weight: 600;
            font-size: 1.2rem;
        }

        /* Album/Dimension cards - Spotify playlist cards */
        .spotify-card {
            background: var(--spotify-grey);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.3s cubic-bezier(0.3, 0, 0.4, 1);
            cursor: pointer;
            border: none;
        }

        .spotify-card:hover {
            background: #2A2A2A;
            transform: scale(1.02);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        }

        .dimension-album {
            background: linear-gradient(135deg, var(--spotify-grey) 0%, #1a1a1a 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            border: 1px solid #282828;
        }

        .dimension-album:hover {
            background: linear-gradient(135deg, #2A2A2A 0%, #1f1f1f 100%);
            border-color: var(--spotify-green);
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(29, 185, 84, 0.2);
        }

        /* Buttons - Spotify green */
        .stButton > button {
            background-color: var(--spotify-green);
            color: var(--spotify-dark);
            font-weight: 700;
            border-radius: 500px;
            border: none;
            padding: 0.75rem 2rem;
            font-size: 0.875rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            transition: all 0.2s;
        }

        .stButton > button:hover {
            background-color: var(--spotify-accent);
            transform: scale(1.04);
            box-shadow: 0 4px 16px rgba(29, 185, 84, 0.4);
        }

        .stButton > button:active {
            transform: scale(0.96);
        }

        /* Progress bars - Spotify style */
        .stProgress > div > div {
            background-color: var(--spotify-green);
            border-radius: 4px;
        }

        .stProgress > div {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 2.5rem;
            font-weight: 900;
            color: var(--spotify-white);
        }

        [data-testid="stMetricLabel"] {
            font-weight: 600;
            color: var(--spotify-lightgrey);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.1em;
        }

        [data-testid="stMetricDelta"] {
            color: var(--spotify-green);
        }

        /* Input fields */
        .stTextInput input, .stTextArea textarea {
            background-color: var(--spotify-grey);
            color: var(--spotify-white);
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 0.75rem;
        }

        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color: var(--spotify-green);
            box-shadow: 0 0 0 1px var(--spotify-green);
        }

        /* Selectbox */
        .stSelectbox > div > div {
            background-color: var(--spotify-grey);
            color: var(--spotify-white);
            border: 1px solid #404040;
        }

        /* Slider */
        .stSlider > div > div > div {
            background-color: var(--spotify-green);
        }

        /* Success/Info boxes - Spotify style */
        .stSuccess {
            background-color: rgba(29, 185, 84, 0.1);
            border-left: 4px solid var(--spotify-green);
            color: var(--spotify-white);
        }

        .stInfo {
            background-color: rgba(46, 119, 208, 0.1);
            border-left: 4px solid var(--spotify-blue);
            color: var(--spotify-white);
        }

        .stWarning {
            background-color: rgba(230, 126, 34, 0.1);
            border-left: 4px solid var(--spotify-orange);
            color: var(--spotify-white);
        }

        /* Expanders - like Spotify dropdowns */
        .streamlit-expanderHeader {
            background-color: var(--spotify-grey);
            border-radius: 8px;
            font-weight: 600;
            color: var(--spotify-white);
            padding: 1rem;
        }

        .streamlit-expanderHeader:hover {
            background-color: #2A2A2A;
        }

        .streamlit-expanderContent {
            background-color: var(--spotify-darkgrey);
            border-radius: 0 0 8px 8px;
        }

        /* Radio buttons */
        .stRadio > div {
            background-color: transparent;
        }

        .stRadio label {
            color: var(--spotify-white);
            padding: 0.75rem 1rem;
            border-radius: 4px;
            transition: background-color 0.2s;
        }

        .stRadio label:hover {
            background-color: var(--spotify-grey);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            background-color: transparent;
        }

        .stTabs [data-baseweb="tab"] {
            color: var(--spotify-lightgrey);
            font-weight: 700;
            font-size: 0.875rem;
            background-color: transparent;
            border: none;
            padding: 0.5rem 0;
        }

        .stTabs [aria-selected="true"] {
            color: var(--spotify-white);
            border-bottom: 2px solid var(--spotify-green);
        }

        /* Checkbox */
        .stCheckbox {
            color: var(--spotify-white);
        }

        /* Playing now bar */
        .playing-bar {
            background: linear-gradient(90deg, var(--spotify-green) 0%, var(--spotify-accent) 100%);
            height: 4px;
            border-radius: 2px;
            margin: 0.5rem 0;
        }

        /* Stats card - like Spotify Wrapped */
        .stat-card {
            background: linear-gradient(135deg, #1DB954 0%, #1ED760 100%);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(29, 185, 84, 0.3);
        }

        /* Pill badges */
        .pill-badge {
            background-color: rgba(29, 185, 84, 0.2);
            color: var(--spotify-green);
            padding: 0.25rem 0.75rem;
            border-radius: 500px;
            font-size: 0.75rem;
            font-weight: 700;
            display: inline-block;
            margin: 0.25rem;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


def create_dimension_album_card(dimension_name: str, icon: str, score: float,
                                 objectives_count: int, trend: str = "→") -> str:
    """Create Spotify album-style card for dimensions"""

    # Color based on score
    if score >= 8:
        color = "#1DB954"
        status = "Thriving"
    elif score >= 6:
        color = "#1ED760"
        status = "Good"
    elif score >= 4:
        color = "#E67E22"
        status = "Needs Focus"
    else:
        color = "#E74C3C"
        status = "Critical"

    return f"""
    <div class="dimension-album">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
            <div style="font-size: 3rem;">{icon}</div>
            <div style="flex: 1;">
                <h3 style="margin: 0; font-size: 1.5rem; font-weight: 700;">{dimension_name}</h3>
                <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 0.25rem;">
                    <span class="pill-badge">{status}</span>
                    <span style="color: #B3B3B3; font-size: 0.875rem;">{objectives_count} objectives</span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 2.5rem; font-weight: 900; color: {color};">{score:.1f}</div>
                <div style="font-size: 1.5rem;">{trend}</div>
            </div>
        </div>
    </div>
    """


def create_spotify_progress_bar(progress: float, color: str = "#1DB954", height: str = "6px") -> str:
    """Create Spotify-style progress bar (like song progress)"""
    return f"""
    <div style="background-color: rgba(255, 255, 255, 0.1); border-radius: 4px; height: {height}; width: 100%; overflow: hidden; margin: 0.5rem 0;">
        <div style="background: linear-gradient(90deg, {color} 0%, {color}dd 100%);
                    height: 100%; width: {progress}%; border-radius: 4px;
                    transition: width 0.3s cubic-bezier(0.3, 0, 0.4, 1);
                    box-shadow: 0 0 10px {color}66;">
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #B3B3B3; margin-top: 0.25rem;">
        <span>{progress:.0f}% complete</span>
        <span>{100-progress:.0f}% remaining</span>
    </div>
    """


def create_lever_playlist_item(lever_name: str, frequency: str, completed: int,
                                target: int, streak: int = 0) -> str:
    """Create Spotify playlist-style item for levers"""

    completion_rate = (completed / target * 100) if target > 0 else 0

    # Determine status color
    if completion_rate >= 90:
        status_color = "#1DB954"
        status_icon = "🔥"
    elif completion_rate >= 70:
        status_color = "#1ED760"
        status_icon = "✅"
    elif completion_rate >= 50:
        status_color = "#E67E22"
        status_icon = "⚠️"
    else:
        status_color = "#E74C3C"
        status_icon = "❌"

    return f"""
    <div class="spotify-card">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 1.5rem;">{status_icon}</div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: #FFFFFF; margin-bottom: 0.25rem;">{lever_name}</div>
                <div style="font-size: 0.75rem; color: #B3B3B3;">{frequency}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: 700; color: {status_color};">{completed}/{target}</div>
                {f'<div style="font-size: 0.75rem; color: #1DB954;">🔥 {streak} day streak</div>' if streak > 0 else ''}
            </div>
        </div>
        <div style="background-color: rgba(255,255,255,0.1); height: 3px; border-radius: 2px; margin-top: 0.75rem; overflow: hidden;">
            <div style="background-color: {status_color}; height: 100%; width: {completion_rate}%; border-radius: 2px;"></div>
        </div>
    </div>
    """


def create_wechat_moment_card(date_str: str, content: str, mood: str = "😊",
                               energy: int = 7, likes: int = 0, comments: int = 0) -> str:
    """Create WeChat Moments-style activity card"""
    return f"""
    <div class="spotify-card" style="padding: 1.5rem;">
        <div style="display: flex; gap: 1rem;">
            <div style="font-size: 2rem;">{mood}</div>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-weight: 600; color: #B3B3B3; font-size: 0.875rem;">{date_str}</div>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <span style="font-size: 0.875rem;">⚡ {energy}/10</span>
                    </div>
                </div>
                <div style="color: #FFFFFF; line-height: 1.6; margin-bottom: 1rem;">{content}</div>
                <div style="display: flex; gap: 1.5rem; color: #B3B3B3; font-size: 0.875rem;">
                    <span>❤️ {likes}</span>
                    <span>💬 {comments}</span>
                </div>
            </div>
        </div>
    </div>
    """


def create_stats_wrapped_card(stat_value: str, stat_label: str, rank: str = "",
                               gradient: str = "linear-gradient(135deg, #1DB954 0%, #1ED760 100%)") -> str:
    """Create Spotify Wrapped-style stat card"""
    return f"""
    <div style="background: {gradient}; border-radius: 16px; padding: 2rem; text-align: center;
                box-shadow: 0 8px 32px rgba(29, 185, 84, 0.3); margin-bottom: 1rem;">
        <div style="font-size: 3rem; font-weight: 900; color: #000000; margin-bottom: 0.5rem;">
            {stat_value}
        </div>
        <div style="font-size: 1rem; font-weight: 700; color: #000000; text-transform: uppercase;
                    letter-spacing: 0.1em; margin-bottom: 0.5rem;">
            {stat_label}
        </div>
        {f'<div style="font-size: 0.875rem; color: #000000; opacity: 0.8;">{rank}</div>' if rank else ''}
    </div>
    """


def create_mini_app_card(app_name: str, icon: str, description: str, action_text: str = "Open") -> str:
    """Create WeChat mini-program style app card"""
    return f"""
    <div class="spotify-card" style="text-align: center; padding: 1.5rem;">
        <div style="font-size: 3rem; margin-bottom: 0.75rem;">{icon}</div>
        <div style="font-weight: 700; font-size: 1rem; color: #FFFFFF; margin-bottom: 0.5rem;">{app_name}</div>
        <div style="font-size: 0.875rem; color: #B3B3B3; margin-bottom: 1rem; min-height: 2.5rem;">{description}</div>
        <div style="background-color: rgba(29, 185, 84, 0.2); color: #1DB954; padding: 0.5rem 1rem;
                    border-radius: 500px; font-weight: 700; font-size: 0.875rem; cursor: pointer;
                    transition: all 0.2s; display: inline-block;">
            {action_text} →
        </div>
    </div>
    """


def create_dimension_radar_chart_spotify(dimension_scores: Dict[str, float],
                                         title: str = "Your Life Balance") -> go.Figure:
    """Create Spotify-styled radar chart"""
    dimensions = list(dimension_scores.keys())
    scores = list(dimension_scores.values())

    dimensions_plot = dimensions + [dimensions[0]]
    scores_plot = scores + [scores[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=scores_plot,
        theta=dimensions_plot,
        fill='toself',
        fillcolor='rgba(29, 185, 84, 0.3)',
        line=dict(color='#1DB954', width=3),
        marker=dict(size=8, color='#1ED760'),
        name='Your Scores'
    ))

    fig.update_layout(
        polar=dict(
            bgcolor='#181818',
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=10, color='#B3B3B3'),
                gridcolor='#282828'
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color='#FFFFFF'),
                gridcolor='#282828'
            )
        ),
        showlegend=False,
        title=dict(text=title, x=0.5, font=dict(size=18, color='#FFFFFF', family='Circular Std')),
        height=450,
        margin=dict(t=80, b=40, l=40, r=40),
        paper_bgcolor='#121212',
        plot_bgcolor='#181818'
    )

    return fig


def create_kpi_trend_chart_spotify(kpi_history: List[Dict], kpi_name: str) -> go.Figure:
    """Create Spotify-styled KPI trend chart"""
    if not kpi_history:
        return None

    df = pd.DataFrame(kpi_history)
    df['recorded_date'] = pd.to_datetime(df['recorded_date'])
    df = df.sort_values('recorded_date')

    fig = go.Figure()

    # Area chart for more visual impact
    fig.add_trace(go.Scatter(
        x=df['recorded_date'],
        y=df['value'],
        mode='lines',
        fill='tozeroy',
        fillcolor='rgba(29, 185, 84, 0.2)',
        line=dict(color='#1DB954', width=3),
        name=kpi_name
    ))

    # Add markers for data points
    fig.add_trace(go.Scatter(
        x=df['recorded_date'],
        y=df['value'],
        mode='markers',
        marker=dict(size=10, color='#1ED760', line=dict(color='#1DB954', width=2)),
        showlegend=False
    ))

    fig.update_layout(
        title=dict(text=kpi_name, font=dict(size=16, color='#FFFFFF')),
        xaxis=dict(
            title="",
            gridcolor='#282828',
            color='#B3B3B3'
        ),
        yaxis=dict(
            title="",
            gridcolor='#282828',
            color='#B3B3B3'
        ),
        height=300,
        margin=dict(t=40, b=40, l=40, r=40),
        hovermode='x unified',
        paper_bgcolor='#121212',
        plot_bgcolor='#181818'
    )

    return fig


def create_dimension_trends_spotify(dimension_scores_history: Dict[str, List[float]]) -> go.Figure:
    """Create Spotify-styled multi-line dimension trends"""
    fig = go.Figure()

    colors = {
        'Career': '#1DB954',
        'Health': '#1ED760',
        'Finance': '#FFD700',
        'Relationships': '#FF6B9D',
        'Personal Growth': '#9D4EDD',
        'Impact': '#2E77D0'
    }

    for dimension, scores in dimension_scores_history.items():
        if scores:
            color = colors.get(dimension, '#1DB954')
            fig.add_trace(go.Scatter(
                y=scores,
                mode='lines+markers',
                name=dimension,
                line=dict(width=3, color=color),
                marker=dict(size=8, color=color)
            ))

    fig.update_layout(
        title=dict(text="All Dimensions Over Time", font=dict(size=18, color='#FFFFFF')),
        xaxis=dict(
            title="Week",
            gridcolor='#282828',
            color='#B3B3B3'
        ),
        yaxis=dict(
            title="Score",
            range=[0, 10],
            gridcolor='#282828',
            color='#B3B3B3'
        ),
        height=400,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0.5)',
            font=dict(color='#FFFFFF')
        ),
        paper_bgcolor='#121212',
        plot_bgcolor='#181818'
    )

    return fig


def init_session_state():
    """Initialize session state with Spotify/WeChat features"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 1

    if 'current_plan_id' not in st.session_state:
        st.session_state.current_plan_id = None

    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1

    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {}

    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'  # Default to Spotify dark theme

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Home'


# Keep existing utility functions
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
    """Get badge for status"""
    colors = {
        'Not Started': '⚪',
        'In Progress': '🟡',
        'At Risk': '🔴',
        'Completed': '🟢'
    }
    return f"{colors.get(status, '⚪')} {status}"


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
