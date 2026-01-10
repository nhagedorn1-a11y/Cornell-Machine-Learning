"""
Seed sample data for testing - Nick's Q1 2026 Plan
"""

from database import *
from datetime import date, timedelta
import json

def seed_sample_data():
    """Create sample user journey for Nick"""

    print("Seeding sample data...")

    # Create user
    user_id = create_user(
        name="Nick Hagedorn",
        email="nick@example.com"
    )
    print(f"Created user: {user_id}")

    # Create Q1 2026 plan
    plan_id = create_quarterly_plan(
        user_id=user_id,
        quarter='Q1',
        year=2026,
        vision_statement="""By the end of 2026, I will have:
- Secured promotion to Director level with expanded team leadership
- Achieved optimal health: running 3x/week, lost 15 lbs, sleeping 7.5 hours consistently
- Built strong financial foundation: $25K saved, maxed 401k, diversified investments
- Deepened family bonds: weekly date nights, quality time with kids daily, regular family connections
- Completed Cornell EMBA with honors, read 12+ books, developed new leadership skills
- Made meaningful impact: mentoring 2 veterans, volunteering 5 hours/month, giving back to community""",
        reflection_worked="Strong focus on career development, consistent morning routine, family dinners",
        reflection_didnt_work="Inconsistent exercise due to travel, not enough sleep, delayed financial planning",
        reflection_learnings="Need to block time for health first, automate finances, be more intentional with family time"
    )
    print(f"Created quarterly plan: {plan_id}")

    # Get dimension IDs
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT dimension_id, dimension_name FROM life_dimensions")
    dim_map = {row['dimension_name']: row['dimension_id'] for row in cursor.fetchall()}
    conn.close()

    # Career objectives
    career_obj_1 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Career'],
        objective_text="Secure promotion to Director level by Q3 2026 through demonstrated leadership, strategic initiatives, and expanded team impact",
        priority='High',
        target_date='2026-09-30'
    )

    create_kpi(career_obj_1, "Strategic initiatives launched", 0, 3, "projects", "Monthly", True)
    create_kpi(career_obj_1, "Team size grown", 5, 12, "people", "Monthly", False)
    create_kpi(career_obj_1, "Leadership presentations delivered", 1, 8, "presentations", "Monthly", True)

    career_obj_2 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Career'],
        objective_text="Build executive presence through public speaking: deliver 6+ presentations to senior leadership and industry events",
        priority='High',
        target_date='2026-03-31'
    )

    create_kpi(career_obj_2, "Presentations delivered", 1, 6, "talks", "Weekly", True)
    create_kpi(career_obj_2, "LinkedIn thought leadership posts", 2, 12, "posts", "Weekly", True)

    # Health objectives
    health_obj_1 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Health'],
        objective_text="Run 3x per week consistently and lose 15 pounds through disciplined training and nutrition by end of Q2",
        priority='High',
        target_date='2026-06-30'
    )

    create_kpi(health_obj_1, "Weekly runs completed", 2, 3, "runs", "Weekly", True)
    create_kpi(health_obj_1, "Current weight", 200, 185, "lbs", "Weekly", False)
    create_kpi(health_obj_1, "Weekly mileage", 8, 15, "miles", "Weekly", True)

    health_obj_2 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Health'],
        objective_text="Improve sleep quality to average 7.5 hours nightly through consistent bedtime routine and sleep hygiene",
        priority='Medium',
        target_date='2026-03-31'
    )

    create_kpi(health_obj_2, "Average sleep hours", 6.2, 7.5, "hours", "Daily", False)
    create_kpi(health_obj_2, "Nights with 7+ hours", 3, 7, "nights/week", "Weekly", True)

    # Finance objectives
    finance_obj_1 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Finance'],
        objective_text="Save $25,000 for investment opportunities and max out 401k contributions for 2026",
        priority='High',
        target_date='2026-12-31'
    )

    create_kpi(finance_obj_1, "Investment savings", 3000, 25000, "$", "Monthly", False)
    create_kpi(finance_obj_1, "401k contribution", 2500, 23000, "$", "Monthly", True)
    create_kpi(finance_obj_1, "Monthly savings rate", 15, 25, "%", "Monthly", True)

    # Relationships objectives
    relationships_obj_1 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Relationships'],
        objective_text="Strengthen marriage through weekly date nights and daily meaningful connection time",
        priority='High',
        target_date='2026-03-31'
    )

    create_kpi(relationships_obj_1, "Date nights completed", 3, 12, "dates", "Weekly", True)
    create_kpi(relationships_obj_1, "Daily connection time", 15, 30, "minutes", "Daily", True)

    relationships_obj_2 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Relationships'],
        objective_text="Be fully present with kids for 30-60 minutes of quality time daily without phone distractions",
        priority='High',
        target_date='2026-03-31'
    )

    create_kpi(relationships_obj_2, "Quality time sessions", 5, 7, "days/week", "Weekly", True)
    create_kpi(relationships_obj_2, "Average daily minutes", 20, 45, "minutes", "Daily", False)

    # Personal Growth objectives
    growth_obj_1 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Personal Growth'],
        objective_text="Complete Cornell EMBA coursework with A- or better grades while maintaining work-life balance",
        priority='High',
        target_date='2026-05-15'
    )

    create_kpi(growth_obj_1, "Courses completed", 1, 4, "courses", "Monthly", False)
    create_kpi(growth_obj_1, "Study hours weekly", 8, 12, "hours", "Weekly", True)

    growth_obj_2 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Personal Growth'],
        objective_text="Read 12 books this year (3 per quarter) focused on leadership, strategy, and personal development",
        priority='Medium',
        target_date='2026-03-31'
    )

    create_kpi(growth_obj_2, "Books completed", 0, 3, "books", "Monthly", False)
    create_kpi(growth_obj_2, "Reading time daily", 15, 30, "minutes", "Daily", True)

    # Impact objectives
    impact_obj_1 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Impact'],
        objective_text="Mentor 2 veterans in career transition, providing monthly guidance and networking support",
        priority='Medium',
        target_date='2026-12-31'
    )

    create_kpi(impact_obj_1, "Active mentees", 1, 2, "people", "Monthly", False)
    create_kpi(impact_obj_1, "Mentoring sessions", 2, 8, "sessions", "Monthly", True)

    impact_obj_2 = create_objective(
        plan_id=plan_id,
        dimension_id=dim_map['Impact'],
        objective_text="Volunteer 5 hours per month with veteran organizations and contribute $500/month to charitable causes",
        priority='Medium',
        target_date='2026-03-31'
    )

    create_kpi(impact_obj_2, "Volunteer hours", 2, 5, "hours/month", "Monthly", True)
    create_kpi(impact_obj_2, "Charitable giving", 200, 500, "$/month", "Monthly", True)

    print("Created objectives and KPIs")

    # Select levers
    conn = get_connection()
    cursor = conn.cursor()

    # Get specific levers by name
    levers_to_add = [
        ("Weekly 1:1 with manager/mentor", "1x per week"),
        ("Publish LinkedIn thought leadership", "1x per week"),
        ("Skill development/learning", "1 hour daily"),
        ("Cardiovascular exercise", "3x per week"),
        ("Quality sleep (7-8 hours)", "7 nights per week"),
        ("Meditation/mindfulness practice", "10 min daily"),
        ("Automated savings (20% of income)", "Monthly"),
        ("Weekly date night with partner", "1x per week"),
        ("Quality time with children", "45 min daily"),
        ("Daily reading habit", "30 min daily"),
        ("Regular volunteering", "5 hours per month"),
        ("Mentor others", "2 mentees")
    ]

    for lever_name, frequency in levers_to_add:
        cursor.execute("SELECT lever_id FROM levers_library WHERE lever_name = ?", (lever_name,))
        result = cursor.fetchone()
        if result:
            add_user_lever(plan_id, result['lever_id'], frequency)

    conn.close()

    print("Added user levers")

    # Create sprints
    sprints_data = [
        {
            'number': 1,
            'theme': 'Foundation & Momentum',
            'focus_areas': [
                'Establish morning routine with exercise',
                'Set up automated savings and 401k max',
                'Plan and execute first date night',
                'Complete first leadership presentation',
                'Launch mentee search and outreach'
            ]
        },
        {
            'number': 2,
            'theme': 'Consistency & Habits',
            'focus_areas': [
                'Hit 3x weekly running target',
                'Maintain 7.5hr sleep average',
                'Deliver 2nd presentation to exec team',
                'Complete EMBA module 1',
                'Weekly family connection rituals'
            ]
        },
        {
            'number': 3,
            'theme': 'Leadership Visibility',
            'focus_areas': [
                'Present strategic initiative to C-suite',
                'Publish 2 LinkedIn thought pieces',
                'Host internal networking event',
                'Onboard first mentee officially',
                'Read book 1 of quarter'
            ]
        },
        {
            'number': 4,
            'theme': 'Health & Relationships',
            'focus_areas': [
                'Lose first 5 pounds',
                'Plan surprise date experience',
                'Daily phone-free kid time',
                'Volunteer for first vet event',
                'Meditation streak: 14 days'
            ]
        },
        {
            'number': 5,
            'theme': 'Growth & Impact',
            'focus_areas': [
                'Complete EMBA coursework ahead of schedule',
                'Secure 2nd mentee commitment',
                'Network with 3 directors for promotion insights',
                'Hit $8K savings milestone',
                'Read book 2 of quarter'
            ]
        },
        {
            'number': 6,
            'theme': 'Quarter Close Strong',
            'focus_areas': [
                'Deliver final Q1 presentation',
                'Complete book 3',
                'Review and celebrate Q1 wins with family',
                'Plan Q2 objectives',
                'Maintain all habit streaks through quarter end'
            ]
        }
    ]

    start_date = date(2026, 1, 1)

    conn = get_connection()
    cursor = conn.cursor()

    for sprint in sprints_data:
        sprint_end = start_date + timedelta(days=13)

        cursor.execute("""
            INSERT INTO sprints (plan_id, sprint_number, start_date, end_date, theme, focus_areas, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_id,
            sprint['number'],
            start_date.isoformat(),
            sprint_end.isoformat(),
            sprint['theme'],
            json.dumps(sprint['focus_areas']),
            'In Progress' if sprint['number'] == 1 else 'Not Started'
        ))

        start_date = sprint_end + timedelta(days=1)

    conn.commit()
    conn.close()

    print("Created sprints")

    # Add some sample check-ins (last 2 weeks)
    today = date.today()

    dimensions_list = ['Career', 'Health', 'Finance', 'Relationships', 'Personal Growth', 'Impact']

    # Weekly check-in from last week
    last_week = today - timedelta(days=7)
    create_checkin(
        user_id=user_id,
        date_str=last_week.isoformat(),
        checkin_type='Weekly',
        dimension_scores={
            'Career': 8,
            'Health': 6,
            'Finance': 7,
            'Relationships': 7,
            'Personal Growth': 8,
            'Impact': 6
        },
        wins_text="Delivered strong presentation to exec team, hit running goal 3x, great date night",
        challenges_text="Sleep still inconsistent, missed meditation twice, travel disrupted routine",
        energy_level=7
    )

    # Daily check-ins for last 5 days
    for i in range(5, 0, -1):
        checkin_date = today - timedelta(days=i)

        create_checkin(
            user_id=user_id,
            date_str=checkin_date.isoformat(),
            checkin_type='Daily',
            energy_level=7 + (i % 3),
            mood=['😊', '😐', '😊', '😊', '😐'][5-i],
            wins_text=[
                "Great 5-mile run this morning",
                "Quality time with kids - built Legos together",
                "Finished EMBA case study early",
                "Productive 1:1 with manager",
                "Read for 45 minutes before bed"
            ][5-i],
            challenges_text=[
                "Stayed up too late working",
                "Missed morning meditation",
                "Travel day - no exercise",
                "Stressful deadline",
                "Tired from poor sleep"
            ][5-i]
        )

    print("Created sample check-ins")

    # Update some KPI values to show progress
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT kpi_id, kpi_name FROM kpis LIMIT 8")
    sample_kpis = cursor.fetchall()

    progress_updates = {
        "Weekly runs completed": 2.5,
        "Current weight": 197,
        "Investment savings": 4200,
        "Date nights completed": 4,
        "Books completed": 1,
        "Presentations delivered": 2,
        "Average sleep hours": 6.8,
        "Study hours weekly": 10
    }

    for kpi in sample_kpis:
        if kpi['kpi_name'] in progress_updates:
            update_kpi_value(kpi['kpi_id'], progress_updates[kpi['kpi_name']], today.isoformat())

    conn.close()

    print("Updated KPI values")
    print("✅ Sample data seeded successfully!")
    print(f"\nUser ID: {user_id}")
    print(f"Plan ID: {plan_id}")
    print("\nYou can now run the app with: streamlit run app.py")


if __name__ == "__main__":
    # Initialize database first
    init_database()
    seed_life_dimensions()
    load_levers_from_json()

    # Seed sample data
    seed_sample_data()
