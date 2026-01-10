"""
Strategic Life Planner - McKinsey-style Quarterly Planning Application
"""

import streamlit as st
import os
from datetime import date, datetime, timedelta
import json

# Import local modules
from database import *
from models import *
from ai_coach import get_ai_coach
from utils import *

# Page configuration
st.set_page_config(
    page_title="Strategic Life Planner",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
apply_custom_css()

# Initialize database
if not os.path.exists(DATABASE_PATH):
    init_database()
    seed_life_dimensions()
    load_levers_from_json()

# Initialize session state
init_session_state()


def main():
    """Main application entry point"""

    # Sidebar navigation
    with st.sidebar:
        st.title("🎯 Strategic Life Planner")

        # User info
        user = get_user_by_id(st.session_state.user_id)
        if user:
            st.write(f"**{user['name']}**")
            st.write(user['email'])
        else:
            st.warning("No user profile found")

        st.markdown("---")

        # Navigation
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "🗓️ Quarterly Planning", "✅ Daily Check-in",
             "📝 Weekly Review", "🔧 Lever Library", "📈 Analytics & Insights"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Current plan info
        current_plan = get_current_plan(st.session_state.user_id)
        if current_plan:
            st.session_state.current_plan_id = current_plan['plan_id']
            quarter = current_plan['quarter']
            year = current_plan['year']

            st.write(f"**Current Plan:** {quarter} {year}")

            progress = QuarterlyPlanManager.calculate_quarter_progress(quarter, year)
            st.progress(progress / 100)
            st.caption(f"{progress:.0f}% through quarter")

            days_left = ProgressCalculator.calculate_time_remaining(quarter, year)
            st.caption(f"{days_left} days remaining")
        else:
            st.info("No active quarterly plan")
            if st.button("Create Your First Plan"):
                page = "🗓️ Quarterly Planning"

        st.markdown("---")
        st.caption("💡 Powered by Claude AI")

    # Route to appropriate page
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "🗓️ Quarterly Planning":
        show_quarterly_planning()
    elif page == "✅ Daily Check-in":
        show_daily_checkin()
    elif page == "📝 Weekly Review":
        show_weekly_review()
    elif page == "🔧 Lever Library":
        show_lever_library()
    elif page == "📈 Analytics & Insights":
        show_analytics()


def show_dashboard():
    """Executive Dashboard - Main view"""
    st.title("📊 Executive Dashboard")

    current_plan = get_current_plan(st.session_state.user_id)

    if not current_plan:
        st.warning("No active quarterly plan. Create one to get started!")
        if st.button("Create Quarterly Plan"):
            st.session_state.page = "🗓️ Quarterly Planning"
            st.rerun()
        return

    plan_id = current_plan['plan_id']
    quarter = current_plan['quarter']
    year = current_plan['year']

    # Top section - Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        week_num = QuarterlyPlanManager.get_week_of_quarter(quarter, year)
        st.metric("Current Week", f"Week {week_num}/13")

    with col2:
        overall_progress = ProgressCalculator.calculate_overall_plan_progress(plan_id)
        st.metric("Overall Progress", f"{overall_progress:.0f}%")

    with col3:
        obj_summary = ProgressCalculator.get_objectives_summary(plan_id)
        st.metric("Objectives", f"{obj_summary['completed']}/{obj_summary['total']}")

    with col4:
        days_left = ProgressCalculator.calculate_time_remaining(quarter, year)
        st.metric("Days Remaining", days_left)

    st.markdown("---")

    # Middle section - Dimension cards
    st.subheader("Life Dimensions")

    dimensions = get_all_dimensions()
    objectives_by_dim = ObjectiveTracker.get_objectives_by_dimension(plan_id)
    latest_scores = DimensionAnalyzer.get_latest_dimension_scores(st.session_state.user_id)

    # Display in 2 columns
    for i in range(0, len(dimensions), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            if i + j < len(dimensions):
                dim = dimensions[i + j]
                dim_name = dim['dimension_name']
                icon = dim['icon']

                with col:
                    with st.container():
                        st.markdown(f"### {icon} {dim_name}")

                        # Current score
                        score = latest_scores.get(dim_name, 5.0)
                        status_emoji = DimensionAnalyzer.get_dimension_status(score)
                        st.write(f"{status_emoji} Current Score: **{score}/10**")

                        # Objectives for this dimension
                        dim_objectives = objectives_by_dim.get(dim_name, [])

                        if dim_objectives:
                            for obj in dim_objectives[:2]:  # Show top 2
                                progress = obj.get('progress', 0)
                                status_badge = get_status_badge(obj['status'])

                                with st.expander(f"{status_badge} {obj['objective_text'][:50]}..."):
                                    st.write(f"**Priority:** {get_priority_color(obj['priority'])} {obj['priority']}")

                                    if obj['target_date']:
                                        days_until = calculate_days_until(obj['target_date'])
                                        if days_until is not None:
                                            st.write(f"**Target:** {format_duration(days_until)}")

                                    st.progress(progress / 100)
                                    st.caption(f"{progress:.0f}% complete")

                                    # Show KPIs
                                    kpis = get_kpis_by_objective(obj['objective_id'])
                                    if kpis:
                                        st.write("**Key Metrics:**")
                                        for kpi in kpis[:2]:
                                            current = kpi['current_value'] or 0
                                            target = kpi['target_value'] or 1
                                            st.write(f"• {kpi['kpi_name']}: {current}/{target} {kpi['unit']}")
                        else:
                            st.caption("No objectives set for this dimension")

                        st.markdown("---")

    # Bottom section - Activity feed and insights
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("💡 AI Insights")

        with st.spinner("Generating insights..."):
            insights = []
            insights.extend(InsightGenerator.generate_dimension_insights(st.session_state.user_id))
            insights.extend(InsightGenerator.generate_lever_insights(plan_id))
            insights.extend(InsightGenerator.generate_kpi_insights(plan_id))

            if insights:
                for insight in insights[:6]:
                    st.info(insight)
            else:
                st.write("Complete check-ins to generate insights!")

    with col2:
        st.subheader("🎯 Recent Activity")

        recent_checkins = get_recent_checkins(st.session_state.user_id, limit=5)

        if recent_checkins:
            for checkin in recent_checkins:
                checkin_date = checkin['date']
                energy = checkin.get('energy_level', 'N/A')
                mood = checkin.get('mood', '😊')

                with st.expander(f"{mood} {checkin_date} - Energy: {energy}/10"):
                    if checkin.get('wins_text'):
                        st.write(f"**Win:** {checkin['wins_text']}")
                    if checkin.get('challenges_text'):
                        st.write(f"**Challenge:** {checkin['challenges_text']}")
        else:
            st.write("No recent activity. Start with a daily check-in!")

    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Daily Check-in", use_container_width=True):
            st.session_state.page = "✅ Daily Check-in"
            st.rerun()

    with col2:
        if st.button("📝 Weekly Review", use_container_width=True):
            st.session_state.page = "📝 Weekly Review"
            st.rerun()

    with col3:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "📈 Analytics & Insights"
            st.rerun()


def show_quarterly_planning():
    """Quarterly Planning Wizard"""
    st.title("🗓️ Quarterly Planning Wizard")

    # Initialize wizard data
    if 'wizard_data' not in st.session_state:
        st.session_state.wizard_data = {}

    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1

    # Progress indicator
    progress = (st.session_state.wizard_step - 1) / 6
    st.progress(progress)
    st.write(f"**Step {st.session_state.wizard_step} of 7**")
    st.markdown("---")

    # Step routing
    if st.session_state.wizard_step == 1:
        wizard_step_1_reflection()
    elif st.session_state.wizard_step == 2:
        wizard_step_2_vision()
    elif st.session_state.wizard_step == 3:
        wizard_step_3_objectives()
    elif st.session_state.wizard_step == 4:
        wizard_step_4_kpis()
    elif st.session_state.wizard_step == 5:
        wizard_step_5_levers()
    elif st.session_state.wizard_step == 6:
        wizard_step_6_sprints()
    elif st.session_state.wizard_step == 7:
        wizard_step_7_review()


def wizard_step_1_reflection():
    """Step 1: Quarterly Reflection"""
    st.subheader("Step 1: Quarterly Reflection")
    st.write("Reflect on your previous quarter to carry forward learnings.")

    worked = st.text_area(
        "What worked last quarter?",
        value=st.session_state.wizard_data.get('reflection_worked', ''),
        height=100,
        placeholder="Key wins, successful strategies, positive habits..."
    )

    didnt_work = st.text_area(
        "What didn't work? Why?",
        value=st.session_state.wizard_data.get('reflection_didnt_work', ''),
        height=100,
        placeholder="Challenges, failed approaches, obstacles..."
    )

    learnings = st.text_area(
        "Key learnings to carry forward",
        value=st.session_state.wizard_data.get('reflection_learnings', ''),
        height=100,
        placeholder="Insights, patterns, adjustments for next quarter..."
    )

    col1, col2 = st.columns([1, 5])

    with col2:
        if st.button("Next: Vision Alignment →", use_container_width=True):
            st.session_state.wizard_data['reflection_worked'] = worked
            st.session_state.wizard_data['reflection_didnt_work'] = didnt_work
            st.session_state.wizard_data['reflection_learnings'] = learnings
            st.session_state.wizard_step = 2
            st.rerun()


def wizard_step_2_vision():
    """Step 2: Vision Alignment"""
    st.subheader("Step 2: Vision Alignment")
    st.write("Define your 1-year vision across all life dimensions.")

    # Show current dimension scores if available
    latest_scores = DimensionAnalyzer.get_latest_dimension_scores(st.session_state.user_id)

    if latest_scores and any(score > 0 for score in latest_scores.values()):
        st.write("**Current Life Balance:**")
        fig = create_dimension_radar_chart(latest_scores)
        st.plotly_chart(fig, use_container_width=True)

    vision = st.text_area(
        "Your 1-year vision across all life dimensions",
        value=st.session_state.wizard_data.get('vision_statement', ''),
        height=150,
        placeholder="Where do you want to be in 1 year across Career, Health, Finance, Relationships, Personal Growth, and Impact?"
    )

    # Quarter selection
    current_quarter, current_year = QuarterlyPlanManager.get_current_quarter()

    col1, col2 = st.columns(2)

    with col1:
        quarter = st.selectbox(
            "Select Quarter",
            ['Q1', 'Q2', 'Q3', 'Q4'],
            index=['Q1', 'Q2', 'Q3', 'Q4'].index(st.session_state.wizard_data.get('quarter', current_quarter))
        )

    with col2:
        year = st.number_input(
            "Year",
            min_value=current_year,
            max_value=current_year + 2,
            value=st.session_state.wizard_data.get('year', current_year)
        )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 1
            st.rerun()

    with col2:
        if st.button("Next: Set Objectives →", use_container_width=True):
            st.session_state.wizard_data['vision_statement'] = vision
            st.session_state.wizard_data['quarter'] = quarter
            st.session_state.wizard_data['year'] = year
            st.session_state.wizard_step = 3
            st.rerun()


def wizard_step_3_objectives():
    """Step 3: Set Objectives"""
    st.subheader("Step 3: Set Objectives by Dimension")
    st.write("Define 1-3 SMART objectives for each life dimension.")

    dimensions = get_all_dimensions()

    # Initialize objectives in wizard data
    if 'objectives' not in st.session_state.wizard_data:
        st.session_state.wizard_data['objectives'] = {}

    ai_coach = get_ai_coach()

    for dim in dimensions:
        dim_name = dim['dimension_name']
        icon = dim['icon']

        with st.expander(f"{icon} {dim_name}", expanded=True):
            st.caption(dim['description'])

            # Get existing objectives for this dimension
            if dim_name not in st.session_state.wizard_data['objectives']:
                st.session_state.wizard_data['objectives'][dim_name] = []

            objectives_list = st.session_state.wizard_data['objectives'][dim_name]

            # Add objective button
            if st.button(f"+ Add Objective", key=f"add_obj_{dim_name}"):
                objectives_list.append({
                    'text': '',
                    'priority': 'Medium',
                    'target_date': None
                })

            # Display and edit existing objectives
            for i, obj in enumerate(objectives_list):
                col1, col2 = st.columns([4, 1])

                with col1:
                    obj_text = st.text_input(
                        f"Objective {i+1}",
                        value=obj['text'],
                        key=f"obj_{dim_name}_{i}",
                        placeholder="Make this specific and measurable..."
                    )
                    obj['text'] = obj_text

                with col2:
                    # AI refinement button
                    if ai_coach.is_available() and obj_text:
                        if st.button("✨ Refine", key=f"refine_{dim_name}_{i}"):
                            with st.spinner("Refining..."):
                                refined = ai_coach.refine_objective(obj_text, dim_name)
                                obj['text'] = refined
                                st.rerun()

                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    priority = st.selectbox(
                        "Priority",
                        ['High', 'Medium', 'Low'],
                        index=['High', 'Medium', 'Low'].index(obj['priority']),
                        key=f"priority_{dim_name}_{i}"
                    )
                    obj['priority'] = priority

                with col2:
                    target = st.date_input(
                        "Target Date",
                        value=obj['target_date'],
                        key=f"target_{dim_name}_{i}"
                    )
                    obj['target_date'] = target

                with col3:
                    if st.button("🗑️", key=f"delete_{dim_name}_{i}"):
                        objectives_list.pop(i)
                        st.rerun()

                st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 2
            st.rerun()

    with col2:
        if st.button("Next: Define KPIs →", use_container_width=True):
            st.session_state.wizard_step = 4
            st.rerun()


def wizard_step_4_kpis():
    """Step 4: Define KPIs"""
    st.subheader("Step 4: Define Key Performance Indicators")
    st.write("Add 2-4 measurable KPIs for each objective.")

    # Initialize KPIs in wizard data
    if 'kpis' not in st.session_state.wizard_data:
        st.session_state.wizard_data['kpis'] = {}

    dimensions = get_all_dimensions()

    for dim in dimensions:
        dim_name = dim['dimension_name']
        objectives = st.session_state.wizard_data.get('objectives', {}).get(dim_name, [])

        if not objectives or not any(obj['text'] for obj in objectives):
            continue

        with st.expander(f"{dim['icon']} {dim_name}", expanded=False):
            for i, obj in enumerate(objectives):
                if not obj['text']:
                    continue

                st.write(f"**Objective:** {obj['text']}")

                obj_key = f"{dim_name}_{i}"
                if obj_key not in st.session_state.wizard_data['kpis']:
                    st.session_state.wizard_data['kpis'][obj_key] = []

                kpis_list = st.session_state.wizard_data['kpis'][obj_key]

                # Add KPI button
                if st.button(f"+ Add KPI", key=f"add_kpi_{obj_key}"):
                    kpis_list.append({
                        'name': '',
                        'current': 0,
                        'target': 0,
                        'unit': '',
                        'frequency': 'Weekly',
                        'is_leading': False
                    })

                # Display KPIs
                for j, kpi in enumerate(kpis_list):
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        kpi['name'] = st.text_input(
                            "KPI Name",
                            value=kpi['name'],
                            key=f"kpi_name_{obj_key}_{j}",
                            placeholder="e.g., Weekly workouts completed"
                        )

                    with col2:
                        kpi['current'] = st.number_input(
                            "Current",
                            value=float(kpi['current']),
                            key=f"kpi_current_{obj_key}_{j}"
                        )

                    with col3:
                        kpi['target'] = st.number_input(
                            "Target",
                            value=float(kpi['target']),
                            key=f"kpi_target_{obj_key}_{j}"
                        )

                    with col4:
                        kpi['unit'] = st.text_input(
                            "Unit",
                            value=kpi['unit'],
                            key=f"kpi_unit_{obj_key}_{j}",
                            placeholder="lbs, hrs, $"
                        )

                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        kpi['frequency'] = st.selectbox(
                            "Frequency",
                            ['Daily', 'Weekly', 'Monthly'],
                            index=['Daily', 'Weekly', 'Monthly'].index(kpi['frequency']),
                            key=f"kpi_freq_{obj_key}_{j}"
                        )

                    with col2:
                        kpi['is_leading'] = st.checkbox(
                            "Leading Indicator",
                            value=kpi['is_leading'],
                            key=f"kpi_leading_{obj_key}_{j}"
                        )

                    with col3:
                        if st.button("🗑️", key=f"delete_kpi_{obj_key}_{j}"):
                            kpis_list.pop(j)
                            st.rerun()

                    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 3
            st.rerun()

    with col2:
        if st.button("Next: Select Levers →", use_container_width=True):
            st.session_state.wizard_step = 5
            st.rerun()


def wizard_step_5_levers():
    """Step 5: Select Levers"""
    st.subheader("Step 5: Select Action Levers")
    st.write("Choose 5-10 evidence-based levers to focus on this quarter.")

    # Initialize selected levers
    if 'selected_levers' not in st.session_state.wizard_data:
        st.session_state.wizard_data['selected_levers'] = []

    # Get AI recommendations
    ai_coach = get_ai_coach()

    if ai_coach.is_available():
        if st.button("✨ Get AI Recommendations"):
            with st.spinner("Analyzing your objectives..."):
                # Collect all objectives
                all_objectives = []
                for dim_name, objs in st.session_state.wizard_data.get('objectives', {}).items():
                    for obj in objs:
                        if obj['text']:
                            all_objectives.append({
                                'dimension_name': dim_name,
                                'objective_text': obj['text']
                            })

                levers = get_levers_by_dimension()
                recommendations = ai_coach.recommend_levers(all_objectives, levers)
                st.info(recommendations)

    # Display levers by dimension
    dimensions = get_all_dimensions()

    for dim in dimensions:
        levers = get_levers_by_dimension(dim['dimension_id'])

        if levers:
            with st.expander(f"{dim['icon']} {dim['dimension_name']} ({len(levers)} levers)", expanded=False):
                for lever in levers:
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        is_selected = any(
                            sl['lever_id'] == lever['lever_id']
                            for sl in st.session_state.wizard_data['selected_levers']
                        )

                        if st.checkbox(
                            f"**{lever['lever_name']}** (Difficulty: {'⭐' * lever['difficulty_level']})",
                            value=is_selected,
                            key=f"lever_{lever['lever_id']}"
                        ):
                            if not is_selected:
                                st.session_state.wizard_data['selected_levers'].append({
                                    'lever_id': lever['lever_id'],
                                    'name': lever['lever_name'],
                                    'target_frequency': lever['typical_frequency']
                                })
                        else:
                            if is_selected:
                                st.session_state.wizard_data['selected_levers'] = [
                                    sl for sl in st.session_state.wizard_data['selected_levers']
                                    if sl['lever_id'] != lever['lever_id']
                                ]

                        st.caption(f"{lever['description']}")
                        st.caption(f"💡 {lever['evidence_summary']}")

                    with col2:
                        st.caption(f"Typical: {lever['typical_frequency']}")

    # Show selected levers
    st.markdown("---")
    st.write(f"**Selected Levers: {len(st.session_state.wizard_data['selected_levers'])}**")

    if st.session_state.wizard_data['selected_levers']:
        for i, lever in enumerate(st.session_state.wizard_data['selected_levers']):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"✓ {lever['name']}")

            with col2:
                lever['target_frequency'] = st.text_input(
                    "Target",
                    value=lever['target_frequency'],
                    key=f"freq_{i}",
                    label_visibility="collapsed"
                )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 4
            st.rerun()

    with col2:
        if st.button("Next: Plan Sprints →", use_container_width=True):
            st.session_state.wizard_step = 6
            st.rerun()


def wizard_step_6_sprints():
    """Step 6: Sprint Planning"""
    st.subheader("Step 6: Sprint Planning")
    st.write("Define 6 two-week sprints for the quarter.")

    # Initialize sprints
    if 'sprints' not in st.session_state.wizard_data:
        quarter = st.session_state.wizard_data.get('quarter', 'Q1')
        year = st.session_state.wizard_data.get('year', 2026)
        start_date, end_date = get_quarter_dates(quarter, year)

        # Create 6 sprints
        st.session_state.wizard_data['sprints'] = []
        current_start = start_date

        for i in range(6):
            sprint_end = current_start + timedelta(days=13)
            st.session_state.wizard_data['sprints'].append({
                'number': i + 1,
                'start_date': current_start,
                'end_date': sprint_end,
                'theme': f'Sprint {i + 1}',
                'focus_areas': []
            })
            current_start = sprint_end + timedelta(days=1)

    ai_coach = get_ai_coach()

    for sprint in st.session_state.wizard_data['sprints']:
        with st.expander(f"Sprint {sprint['number']}: {format_date(sprint['start_date'])} - {format_date(sprint['end_date'])}", expanded=False):

            # AI suggestion
            if ai_coach.is_available():
                if st.button(f"✨ Get AI Suggestions", key=f"sprint_ai_{sprint['number']}"):
                    with st.spinner("Generating sprint plan..."):
                        all_obj_texts = []
                        for dim_objs in st.session_state.wizard_data.get('objectives', {}).values():
                            all_obj_texts.extend([obj['text'] for obj in dim_objs if obj['text']])

                        prev_results = None
                        if sprint['number'] > 1:
                            prev_sprint = st.session_state.wizard_data['sprints'][sprint['number'] - 2]
                            prev_results = f"Theme: {prev_sprint['theme']}\nFocus: {', '.join(prev_sprint['focus_areas'])}"

                        suggestion = ai_coach.suggest_sprint_focus(
                            all_obj_texts,
                            sprint['number'],
                            prev_results
                        )

                        sprint['theme'] = suggestion['theme']
                        sprint['focus_areas'] = suggestion['focus_areas']
                        st.rerun()

            sprint['theme'] = st.text_input(
                "Sprint Theme",
                value=sprint['theme'],
                key=f"sprint_theme_{sprint['number']}",
                placeholder="3-5 word theme"
            )

            st.write("**Focus Areas (3-5):**")

            # Add focus area button
            if st.button("+ Add Focus Area", key=f"add_focus_{sprint['number']}"):
                sprint['focus_areas'].append('')

            # Display focus areas
            for i, focus in enumerate(sprint['focus_areas']):
                col1, col2 = st.columns([5, 1])

                with col1:
                    sprint['focus_areas'][i] = st.text_input(
                        f"Focus {i+1}",
                        value=focus,
                        key=f"focus_{sprint['number']}_{i}",
                        label_visibility="collapsed"
                    )

                with col2:
                    if st.button("🗑️", key=f"del_focus_{sprint['number']}_{i}"):
                        sprint['focus_areas'].pop(i)
                        st.rerun()

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 5
            st.rerun()

    with col2:
        if st.button("Next: Review & Commit →", use_container_width=True):
            st.session_state.wizard_step = 7
            st.rerun()


def wizard_step_7_review():
    """Step 7: Review & Commit"""
    st.subheader("Step 7: Review & Commit")
    st.write("Review your quarterly plan and commit to execution.")

    # Summary display
    quarter = st.session_state.wizard_data.get('quarter', 'Q1')
    year = st.session_state.wizard_data.get('year', 2026)

    st.write(f"## {quarter} {year} Strategic Plan")

    # Vision
    st.write("### 🎯 Vision")
    st.info(st.session_state.wizard_data.get('vision_statement', 'Not set'))

    # Objectives summary
    st.write("### 📋 Objectives Summary")
    total_objectives = 0
    for dim_name, objs in st.session_state.wizard_data.get('objectives', {}).items():
        valid_objs = [obj for obj in objs if obj['text']]
        if valid_objs:
            total_objectives += len(valid_objs)
            st.write(f"**{dim_name}:** {len(valid_objs)} objective(s)")

    # Levers summary
    st.write("### 🔧 Action Levers")
    levers_count = len(st.session_state.wizard_data.get('selected_levers', []))
    st.write(f"**{levers_count} levers selected**")

    # Commitment statement
    st.write("### ✍️ Commitment")
    commitment = st.text_area(
        "Write your commitment statement",
        placeholder="I commit to...",
        height=100
    )

    # Validate and save
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.wizard_step = 6
            st.rerun()

    with col2:
        if st.button("✅ Save & Activate Plan", use_container_width=True, type="primary"):
            with st.spinner("Creating your quarterly plan..."):
                # Save to database
                save_quarterly_plan()
                st.success("✅ Quarterly plan created successfully!")
                st.balloons()

                # Reset wizard
                st.session_state.wizard_step = 1
                st.session_state.wizard_data = {}

                # Wait and redirect
                import time
                time.sleep(2)
                st.rerun()


def save_quarterly_plan():
    """Save the quarterly plan to database"""
    data = st.session_state.wizard_data

    # Create quarterly plan
    plan_id = create_quarterly_plan(
        user_id=st.session_state.user_id,
        quarter=data['quarter'],
        year=data['year'],
        vision_statement=data.get('vision_statement', ''),
        reflection_worked=data.get('reflection_worked', ''),
        reflection_didnt_work=data.get('reflection_didnt_work', ''),
        reflection_learnings=data.get('reflection_learnings', '')
    )

    # Get dimension map
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dimension_id, dimension_name FROM life_dimensions")
    dim_map = {row['dimension_name']: row['dimension_id'] for row in cursor.fetchall()}
    conn.close()

    # Save objectives and KPIs
    for dim_name, objectives in data.get('objectives', {}).items():
        dimension_id = dim_map.get(dim_name)
        if not dimension_id:
            continue

        for i, obj in enumerate(objectives):
            if not obj['text']:
                continue

            # Create objective
            obj_id = create_objective(
                plan_id=plan_id,
                dimension_id=dimension_id,
                objective_text=obj['text'],
                priority=obj['priority'],
                target_date=obj['target_date'].isoformat() if obj['target_date'] else None
            )

            # Create KPIs for this objective
            obj_key = f"{dim_name}_{i}"
            kpis = data.get('kpis', {}).get(obj_key, [])

            for kpi in kpis:
                if kpi['name']:
                    create_kpi(
                        objective_id=obj_id,
                        kpi_name=kpi['name'],
                        current_value=kpi['current'],
                        target_value=kpi['target'],
                        unit=kpi['unit'],
                        measurement_frequency=kpi['frequency'],
                        is_leading_indicator=kpi['is_leading']
                    )

    # Save selected levers
    for lever in data.get('selected_levers', []):
        add_user_lever(
            plan_id=plan_id,
            lever_id=lever['lever_id'],
            target_frequency=lever['target_frequency']
        )

    # Save sprints
    conn = get_connection()
    cursor = conn.cursor()

    for sprint in data.get('sprints', []):
        cursor.execute("""
            INSERT INTO sprints (plan_id, sprint_number, start_date, end_date, theme, focus_areas)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            plan_id,
            sprint['number'],
            sprint['start_date'].isoformat(),
            sprint['end_date'].isoformat(),
            sprint['theme'],
            json.dumps(sprint['focus_areas'])
        ))

    conn.commit()
    conn.close()


def show_daily_checkin():
    """Daily Check-in Interface"""
    st.title("✅ Daily Check-in")
    st.write("Quick 2-minute check-in to track your daily progress")

    current_plan = get_current_plan(st.session_state.user_id)

    if not current_plan:
        st.warning("Create a quarterly plan first!")
        return

    # Check if already checked in today
    today = date.today().isoformat()
    existing_checkins = get_recent_checkins(st.session_state.user_id, limit=1)

    if existing_checkins and existing_checkins[0]['date'] == today and existing_checkins[0]['checkin_type'] == 'Daily':
        st.success("✅ You've already completed today's check-in!")

        if st.button("Update Today's Check-in"):
            # Allow editing
            pass
        else:
            return

    # Date
    checkin_date = st.date_input("Date", value=date.today())

    # Energy level
    energy = st.slider("Energy Level", 1, 10, 5, help="How energized do you feel today?")

    # Mood
    moods = ['😊 Great', '😐 Okay', '😞 Struggling', '😫 Exhausted']
    mood = st.select_slider("Mood", options=moods)
    mood_emoji = mood.split()[0]

    # Lever tracking
    st.subheader("Today's Levers")
    st.write("Did you complete these activities today?")

    user_levers = get_user_levers_by_plan(current_plan['plan_id'])
    completed_levers = []

    if user_levers:
        for lever in user_levers:
            completed = st.checkbox(
                f"{lever['lever_name']} ({lever['target_frequency']})",
                key=f"lever_{lever['lever_id']}"
            )
            if completed:
                completed_levers.append(lever['lever_id'])
    else:
        st.info("No levers selected for this quarter")

    # Quick wins and challenges
    col1, col2 = st.columns(2)

    with col1:
        win = st.text_area(
            "🎉 Quick Win (optional)",
            placeholder="One thing that went well today...",
            height=80
        )

    with col2:
        challenge = st.text_area(
            "⚠️ Challenge (optional)",
            placeholder="One thing that was difficult...",
            height=80
        )

    # Submit
    if st.button("💾 Save Check-in", use_container_width=True, type="primary"):
        # Create check-in
        checkin_id = create_checkin(
            user_id=st.session_state.user_id,
            date_str=checkin_date.isoformat(),
            checkin_type='Daily',
            energy_level=energy,
            mood=mood_emoji,
            wins_text=win,
            challenges_text=challenge
        )

        # Save lever completions
        conn = get_connection()
        cursor = conn.cursor()

        for lever in user_levers:
            completed = lever['lever_id'] in completed_levers
            cursor.execute("""
                INSERT INTO daily_lever_tracking (checkin_id, lever_id, completed)
                VALUES (?, ?, ?)
            """, (checkin_id, lever['lever_id'], completed))

        conn.commit()
        conn.close()

        st.success("✅ Check-in saved successfully!")
        st.balloons()


def show_weekly_review():
    """Weekly Review Form"""
    st.title("📝 Weekly Review")
    st.write("Comprehensive 10-minute weekly reflection and planning")

    current_plan = get_current_plan(st.session_state.user_id)

    if not current_plan:
        st.warning("Create a quarterly plan first!")
        return

    plan_id = current_plan['plan_id']

    # Week selection
    review_date = st.date_input("Review Date", value=date.today())

    # Dimension ratings
    st.subheader("Rate Each Life Dimension (1-10)")

    dimensions = get_all_dimensions()
    dimension_scores = {}

    cols = st.columns(2)
    for i, dim in enumerate(dimensions):
        with cols[i % 2]:
            score = st.slider(
                f"{dim['icon']} {dim['dimension_name']}",
                1, 10, 5,
                key=f"dim_score_{dim['dimension_id']}",
                help=dim['description']
            )
            dimension_scores[dim['dimension_name']] = score

    # Show radar chart
    fig = create_dimension_radar_chart(dimension_scores, "This Week's Balance")
    st.plotly_chart(fig, use_container_width=True)

    # Objective progress
    st.subheader("Objective Progress This Week")

    objectives = get_objectives_by_plan(plan_id)

    progressed_objectives = []
    for obj in objectives:
        progressed = st.checkbox(
            f"{obj['objective_text'][:80]}",
            key=f"obj_progress_{obj['objective_id']}"
        )
        if progressed:
            progressed_objectives.append(obj['objective_id'])
            notes = st.text_input(
                "Progress notes",
                key=f"obj_notes_{obj['objective_id']}",
                placeholder="What did you accomplish?"
            )

    # KPI updates
    st.subheader("Update Key Metrics")

    for obj in objectives[:3]:  # Limit to top 3 objectives
        kpis = get_kpis_by_objective(obj['objective_id'])

        if kpis:
            st.write(f"**{obj['objective_text'][:50]}...**")

            for kpi in kpis:
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"{kpi['kpi_name']}")

                with col2:
                    new_value = st.number_input(
                        "New value",
                        value=float(kpi['current_value'] or 0),
                        key=f"kpi_update_{kpi['kpi_id']}",
                        label_visibility="collapsed"
                    )

                    if new_value != kpi['current_value']:
                        update_kpi_value(kpi['kpi_id'], new_value, review_date.isoformat())

    # Reflection
    st.subheader("Weekly Reflection")

    col1, col2 = st.columns(2)

    with col1:
        biggest_win = st.text_area(
            "🎉 Biggest Win This Week",
            placeholder="What are you most proud of?",
            height=100
        )

    with col2:
        biggest_challenge = st.text_area(
            "⚠️ Biggest Challenge This Week",
            placeholder="What was most difficult?",
            height=100
        )

    next_week_changes = st.text_area(
        "📋 What needs to change next week?",
        placeholder="Adjustments, priorities, new approaches...",
        height=100
    )

    # AI Insights
    st.subheader("💡 AI-Generated Insights")

    ai_coach = get_ai_coach()

    if st.button("✨ Generate Weekly Insights"):
        if ai_coach.is_available():
            with st.spinner("Analyzing your week..."):
                # Collect data
                kpi_data = []
                for obj in objectives[:5]:
                    for kpi in get_kpis_by_objective(obj['objective_id']):
                        kpi_data.append(kpi)

                completed_lever_names = []
                # Get lever completions from recent check-ins
                # Simplified for MVP

                insights = ai_coach.generate_weekly_insights(
                    dimension_scores=dimension_scores,
                    completed_levers=completed_lever_names,
                    kpi_data=kpi_data,
                    wins=biggest_win,
                    challenges=biggest_challenge
                )

                st.info(insights)
        else:
            st.warning("AI insights require ANTHROPIC_API_KEY to be configured")

    # Save
    if st.button("💾 Save Weekly Review", use_container_width=True, type="primary"):
        # Create weekly check-in
        review_notes = f"Win: {biggest_win}\nChallenge: {biggest_challenge}\nChanges: {next_week_changes}"

        checkin_id = create_checkin(
            user_id=st.session_state.user_id,
            date_str=review_date.isoformat(),
            checkin_type='Weekly',
            dimension_scores=dimension_scores,
            wins_text=biggest_win,
            challenges_text=biggest_challenge
        )

        st.success("✅ Weekly review saved!")
        st.balloons()


def show_lever_library():
    """Lever Library Browser"""
    st.title("🔧 Lever Library")
    st.write("Browse evidence-based levers for personal and professional growth")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        dimensions = get_all_dimensions()
        dim_options = ['All Dimensions'] + [d['dimension_name'] for d in dimensions]
        selected_dim = st.selectbox("Filter by Dimension", dim_options)

    with col2:
        difficulty_filter = st.selectbox("Difficulty", ['All', '⭐ Easy', '⭐⭐ Moderate', '⭐⭐⭐ Challenging'])

    with col3:
        search = st.text_input("🔍 Search", placeholder="Search levers...")

    # Get levers
    if selected_dim == 'All Dimensions':
        levers = get_levers_by_dimension()
    else:
        dim_id = next((d['dimension_id'] for d in dimensions if d['dimension_name'] == selected_dim), None)
        levers = get_levers_by_dimension(dim_id) if dim_id else []

    # Apply filters
    if difficulty_filter != 'All':
        diff_level = difficulty_filter.count('⭐')
        levers = [l for l in levers if l['difficulty_level'] == diff_level]

    if search:
        levers = [
            l for l in levers
            if search.lower() in l['lever_name'].lower() or search.lower() in l['description'].lower()
        ]

    st.write(f"**{len(levers)} levers found**")
    st.markdown("---")

    # Display levers
    for lever in levers:
        with st.expander(f"**{lever['lever_name']}** ({'⭐' * lever['difficulty_level']})"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**Dimension:** {lever['dimension_name']}")
                st.write(lever['description'])
                st.write(f"**💡 Evidence:** {lever['evidence_summary']}")

            with col2:
                st.write(f"**Typical Frequency:**")
                st.write(lever['typical_frequency'])
                st.write(f"**Difficulty:**")
                st.write('⭐' * lever['difficulty_level'])


def show_analytics():
    """Analytics & Insights Page"""
    st.title("📈 Analytics & Insights")

    current_plan = get_current_plan(st.session_state.user_id)

    if not current_plan:
        st.warning("Create a quarterly plan to view analytics!")
        return

    plan_id = current_plan['plan_id']

    # Time range selector
    time_range = st.selectbox("Time Range", ['Last 7 days', 'Last 30 days', 'Quarter to date'])

    days_map = {
        'Last 7 days': 7,
        'Last 30 days': 30,
        'Quarter to date': 90
    }
    days = days_map[time_range]

    # Dimension trends
    st.subheader("Dimension Trends")

    scores_history = DimensionAnalyzer.get_dimension_scores(st.session_state.user_id, days)

    if scores_history and any(scores_history.values()):
        fig = create_dimension_trend_chart(scores_history)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Complete weekly reviews to see dimension trends")

    # KPI Progress
    st.subheader("Key Performance Indicators")

    objectives = get_objectives_by_plan(plan_id)

    for obj in objectives[:3]:
        st.write(f"**{obj['objective_text']}**")

        kpis = get_kpis_by_objective(obj['objective_id'])

        for kpi in kpis:
            col1, col2 = st.columns([2, 1])

            with col1:
                current = kpi['current_value'] or 0
                target = kpi['target_value'] or 1
                progress = (current / target * 100) if target > 0 else 0

                st.write(f"{kpi['kpi_name']}: {current}/{target} {kpi['unit']}")
                st.progress(min(1.0, progress / 100))

            with col2:
                st.metric("Progress", f"{progress:.0f}%")

            # Show history chart if available
            history = get_kpi_history(kpi['kpi_id'], limit=30)
            if len(history) > 1:
                fig = create_kpi_progress_chart(history, kpi['kpi_name'])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

    # Lever consistency
    st.subheader("Lever Consistency")

    user_levers = get_user_levers_by_plan(plan_id)

    if user_levers:
        for lever in user_levers[:8]:
            consistency = LeverAnalyzer.calculate_lever_consistency(
                st.session_state.user_id,
                lever['lever_id'],
                days
            )
            streak = LeverAnalyzer.get_lever_streak(
                st.session_state.user_id,
                lever['lever_id']
            )

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"**{lever['lever_name']}**")
                st.progress(consistency / 100)

            with col2:
                st.metric("Consistency", f"{consistency:.0f}%")

            with col3:
                st.metric("Streak", f"{streak} days")

    # Overall insights
    st.subheader("Insights Summary")

    all_insights = []
    all_insights.extend(InsightGenerator.generate_dimension_insights(st.session_state.user_id))
    all_insights.extend(InsightGenerator.generate_lever_insights(plan_id))
    all_insights.extend(InsightGenerator.generate_kpi_insights(plan_id))

    if all_insights:
        for insight in all_insights[:10]:
            st.info(insight)
    else:
        st.write("Complete more check-ins to generate insights!")


# Run the app
if __name__ == "__main__":
    main()
