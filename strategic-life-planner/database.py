"""
Database setup and models for Strategic Life Planner
"""

import sqlite3
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'database.db')


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with all tables"""
    conn = get_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Life Dimensions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS life_dimensions (
            dimension_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dimension_name TEXT NOT NULL UNIQUE,
            description TEXT,
            icon TEXT
        )
    """)

    # Quarterly Plans Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quarterly_plans (
            plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quarter TEXT NOT NULL,
            year INTEGER NOT NULL,
            vision_statement TEXT,
            review_notes TEXT,
            reflection_worked TEXT,
            reflection_didnt_work TEXT,
            reflection_learnings TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, quarter, year)
        )
    """)

    # Objectives Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objectives (
            objective_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            dimension_id INTEGER NOT NULL,
            objective_text TEXT NOT NULL,
            priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')),
            target_date DATE,
            status TEXT CHECK(status IN ('Not Started', 'In Progress', 'At Risk', 'Completed')) DEFAULT 'Not Started',
            FOREIGN KEY (plan_id) REFERENCES quarterly_plans(plan_id),
            FOREIGN KEY (dimension_id) REFERENCES life_dimensions(dimension_id)
        )
    """)

    # KPIs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kpis (
            kpi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            objective_id INTEGER NOT NULL,
            kpi_name TEXT NOT NULL,
            current_value REAL,
            target_value REAL,
            unit TEXT,
            measurement_frequency TEXT CHECK(measurement_frequency IN ('Daily', 'Weekly', 'Monthly')),
            is_leading_indicator BOOLEAN DEFAULT 0,
            FOREIGN KEY (objective_id) REFERENCES objectives(objective_id)
        )
    """)

    # Levers Library Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS levers_library (
            lever_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dimension_id INTEGER NOT NULL,
            lever_name TEXT NOT NULL,
            description TEXT,
            typical_frequency TEXT,
            evidence_summary TEXT,
            difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5),
            FOREIGN KEY (dimension_id) REFERENCES life_dimensions(dimension_id)
        )
    """)

    # User Levers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_levers (
            user_lever_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            lever_id INTEGER NOT NULL,
            target_frequency TEXT,
            actual_frequency INTEGER DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (plan_id) REFERENCES quarterly_plans(plan_id),
            FOREIGN KEY (lever_id) REFERENCES levers_library(lever_id)
        )
    """)

    # Check-ins Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            dimension_scores TEXT,
            wins_text TEXT,
            challenges_text TEXT,
            energy_level INTEGER CHECK(energy_level BETWEEN 1 AND 10),
            mood TEXT,
            checkin_type TEXT CHECK(checkin_type IN ('Daily', 'Weekly')) DEFAULT 'Daily',
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, date, checkin_type)
        )
    """)

    # Daily Lever Tracking Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_lever_tracking (
            tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            checkin_id INTEGER NOT NULL,
            lever_id INTEGER NOT NULL,
            completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (checkin_id) REFERENCES checkins(checkin_id),
            FOREIGN KEY (lever_id) REFERENCES levers_library(lever_id)
        )
    """)

    # Sprints Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sprints (
            sprint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            sprint_number INTEGER NOT NULL,
            start_date DATE,
            end_date DATE,
            theme TEXT,
            focus_areas TEXT,
            status TEXT CHECK(status IN ('Not Started', 'In Progress', 'Completed')) DEFAULT 'Not Started',
            FOREIGN KEY (plan_id) REFERENCES quarterly_plans(plan_id)
        )
    """)

    # KPI History Table (for tracking changes over time)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kpi_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            kpi_id INTEGER NOT NULL,
            value REAL NOT NULL,
            recorded_date DATE NOT NULL,
            FOREIGN KEY (kpi_id) REFERENCES kpis(kpi_id)
        )
    """)

    conn.commit()
    conn.close()


def seed_life_dimensions():
    """Seed the life dimensions table"""
    conn = get_connection()
    cursor = conn.cursor()

    dimensions = [
        ('Career', 'Professional growth, achievements, and career progression', '💼'),
        ('Health', 'Physical and mental wellbeing, fitness, nutrition, and sleep', '🏃'),
        ('Finance', 'Financial planning, savings, investments, and wealth building', '💰'),
        ('Relationships', 'Family, friends, romantic relationships, and social connections', '❤️'),
        ('Personal Growth', 'Learning, skills development, hobbies, and self-improvement', '📚'),
        ('Impact', 'Contribution to community, mentorship, volunteering, and legacy', '🌟')
    ]

    for dim in dimensions:
        cursor.execute("""
            INSERT OR IGNORE INTO life_dimensions (dimension_name, description, icon)
            VALUES (?, ?, ?)
        """, dim)

    conn.commit()
    conn.close()


def load_levers_from_json():
    """Load levers from JSON file into database"""
    import json

    json_path = os.path.join(os.path.dirname(__file__), 'data', 'levers_library.json')

    if not os.path.exists(json_path):
        return

    with open(json_path, 'r') as f:
        levers_data = json.load(f)

    conn = get_connection()
    cursor = conn.cursor()

    # Get dimension name to ID mapping
    cursor.execute("SELECT dimension_id, dimension_name FROM life_dimensions")
    dimension_map = {row['dimension_name']: row['dimension_id'] for row in cursor.fetchall()}

    for lever in levers_data['levers']:
        dimension_id = dimension_map.get(lever['dimension'])
        if dimension_id:
            cursor.execute("""
                INSERT OR IGNORE INTO levers_library
                (dimension_id, lever_name, description, typical_frequency, evidence_summary, difficulty_level)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dimension_id,
                lever['name'],
                lever['description'],
                lever['typical_frequency'],
                lever['evidence_summary'],
                lever['difficulty_level']
            ))

    conn.commit()
    conn.close()


# Helper functions for database operations

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def get_all_dimensions() -> List[Dict]:
    """Get all life dimensions"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM life_dimensions ORDER BY dimension_id")
    dimensions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return dimensions


def get_current_plan(user_id: int) -> Optional[Dict]:
    """Get the most recent quarterly plan for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM quarterly_plans
        WHERE user_id = ?
        ORDER BY year DESC, quarter DESC
        LIMIT 1
    """, (user_id,))
    plan = cursor.fetchone()
    conn.close()
    return dict(plan) if plan else None


def get_objectives_by_plan(plan_id: int) -> List[Dict]:
    """Get all objectives for a plan"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, d.dimension_name, d.icon
        FROM objectives o
        JOIN life_dimensions d ON o.dimension_id = d.dimension_id
        WHERE o.plan_id = ?
        ORDER BY d.dimension_id, o.priority
    """, (plan_id,))
    objectives = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return objectives


def get_kpis_by_objective(objective_id: int) -> List[Dict]:
    """Get all KPIs for an objective"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kpis WHERE objective_id = ?", (objective_id,))
    kpis = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return kpis


def get_user_levers_by_plan(plan_id: int) -> List[Dict]:
    """Get all levers selected for a plan"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ul.*, ll.lever_name, ll.description, ll.difficulty_level, d.dimension_name
        FROM user_levers ul
        JOIN levers_library ll ON ul.lever_id = ll.lever_id
        JOIN life_dimensions d ON ll.dimension_id = d.dimension_id
        WHERE ul.plan_id = ?
    """, (plan_id,))
    levers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return levers


def get_levers_by_dimension(dimension_id: Optional[int] = None) -> List[Dict]:
    """Get levers, optionally filtered by dimension"""
    conn = get_connection()
    cursor = conn.cursor()

    if dimension_id:
        cursor.execute("""
            SELECT ll.*, d.dimension_name
            FROM levers_library ll
            JOIN life_dimensions d ON ll.dimension_id = d.dimension_id
            WHERE ll.dimension_id = ?
            ORDER BY ll.difficulty_level, ll.lever_name
        """, (dimension_id,))
    else:
        cursor.execute("""
            SELECT ll.*, d.dimension_name
            FROM levers_library ll
            JOIN life_dimensions d ON ll.dimension_id = d.dimension_id
            ORDER BY d.dimension_name, ll.difficulty_level
        """)

    levers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return levers


def create_user(name: str, email: str) -> int:
    """Create a new user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def create_quarterly_plan(user_id: int, quarter: str, year: int, **kwargs) -> int:
    """Create a new quarterly plan"""
    conn = get_connection()
    cursor = conn.cursor()

    fields = ['user_id', 'quarter', 'year']
    values = [user_id, quarter, year]

    for key, value in kwargs.items():
        if value is not None:
            fields.append(key)
            values.append(value)

    placeholders = ', '.join(['?' for _ in values])
    field_names = ', '.join(fields)

    cursor.execute(f"""
        INSERT INTO quarterly_plans ({field_names})
        VALUES ({placeholders})
    """, values)

    plan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return plan_id


def create_objective(plan_id: int, dimension_id: int, objective_text: str,
                     priority: str, target_date: Optional[str] = None) -> int:
    """Create a new objective"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO objectives (plan_id, dimension_id, objective_text, priority, target_date)
        VALUES (?, ?, ?, ?, ?)
    """, (plan_id, dimension_id, objective_text, priority, target_date))
    objective_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return objective_id


def create_kpi(objective_id: int, kpi_name: str, current_value: float,
               target_value: float, unit: str, measurement_frequency: str,
               is_leading_indicator: bool = False) -> int:
    """Create a new KPI"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO kpis (objective_id, kpi_name, current_value, target_value,
                         unit, measurement_frequency, is_leading_indicator)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (objective_id, kpi_name, current_value, target_value, unit,
          measurement_frequency, is_leading_indicator))
    kpi_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return kpi_id


def add_user_lever(plan_id: int, lever_id: int, target_frequency: str) -> int:
    """Add a lever to a user's plan"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_levers (plan_id, lever_id, target_frequency)
        VALUES (?, ?, ?)
    """, (plan_id, lever_id, target_frequency))
    user_lever_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_lever_id


def create_checkin(user_id: int, date_str: str, checkin_type: str = 'Daily', **kwargs) -> int:
    """Create a new check-in"""
    conn = get_connection()
    cursor = conn.cursor()

    fields = ['user_id', 'date', 'checkin_type']
    values = [user_id, date_str, checkin_type]

    for key, value in kwargs.items():
        if value is not None:
            fields.append(key)
            if key == 'dimension_scores' and isinstance(value, dict):
                values.append(json.dumps(value))
            else:
                values.append(value)

    placeholders = ', '.join(['?' for _ in values])
    field_names = ', '.join(fields)

    cursor.execute(f"""
        INSERT OR REPLACE INTO checkins ({field_names})
        VALUES ({placeholders})
    """, values)

    checkin_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return checkin_id


def update_kpi_value(kpi_id: int, new_value: float, date_str: Optional[str] = None):
    """Update a KPI value and record in history"""
    if date_str is None:
        date_str = date.today().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    # Update current value
    cursor.execute("UPDATE kpis SET current_value = ? WHERE kpi_id = ?", (new_value, kpi_id))

    # Add to history
    cursor.execute("""
        INSERT INTO kpi_history (kpi_id, value, recorded_date)
        VALUES (?, ?, ?)
    """, (kpi_id, new_value, date_str))

    conn.commit()
    conn.close()


def get_recent_checkins(user_id: int, limit: int = 7, checkin_type: str = 'Daily') -> List[Dict]:
    """Get recent check-ins for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM checkins
        WHERE user_id = ? AND checkin_type = ?
        ORDER BY date DESC
        LIMIT ?
    """, (user_id, checkin_type, limit))
    checkins = [dict(row) for row in cursor.fetchall()]

    # Parse dimension_scores JSON
    for checkin in checkins:
        if checkin.get('dimension_scores'):
            checkin['dimension_scores'] = json.loads(checkin['dimension_scores'])

    conn.close()
    return checkins


def get_kpi_history(kpi_id: int, limit: int = 30) -> List[Dict]:
    """Get historical values for a KPI"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM kpi_history
        WHERE kpi_id = ?
        ORDER BY recorded_date DESC
        LIMIT ?
    """, (kpi_id, limit))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    seed_life_dimensions()
    print("Database initialized successfully!")
