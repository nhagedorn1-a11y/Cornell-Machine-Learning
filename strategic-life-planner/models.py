"""
Business logic and data models for Strategic Life Planner
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
import json
from database import *


class QuarterlyPlanManager:
    """Manage quarterly plans and related data"""

    @staticmethod
    def get_current_quarter() -> Tuple[str, int]:
        """Get current quarter and year"""
        today = date.today()
        month = today.month
        year = today.year

        if month <= 3:
            quarter = 'Q1'
        elif month <= 6:
            quarter = 'Q2'
        elif month <= 9:
            quarter = 'Q3'
        else:
            quarter = 'Q4'

        return quarter, year

    @staticmethod
    def calculate_quarter_progress(quarter: str, year: int) -> float:
        """Calculate percentage of quarter completed"""
        today = date.today()
        current_quarter, current_year = QuarterlyPlanManager.get_current_quarter()

        if year > current_year or (year == current_year and quarter > current_quarter):
            return 0.0  # Future quarter

        if year < current_year or (year == current_year and quarter < current_quarter):
            return 100.0  # Past quarter

        # Current quarter - calculate actual progress
        quarter_starts = {
            'Q1': date(year, 1, 1),
            'Q2': date(year, 4, 1),
            'Q3': date(year, 7, 1),
            'Q4': date(year, 10, 1)
        }

        quarter_ends = {
            'Q1': date(year, 3, 31),
            'Q2': date(year, 6, 30),
            'Q3': date(year, 9, 30),
            'Q4': date(year, 12, 31)
        }

        start = quarter_starts[quarter]
        end = quarter_ends[quarter]
        total_days = (end - start).days + 1
        days_elapsed = (today - start).days + 1

        return min(100.0, max(0.0, (days_elapsed / total_days) * 100))

    @staticmethod
    def get_week_of_quarter(quarter: str, year: int) -> int:
        """Get current week number within the quarter (1-13)"""
        today = date.today()
        quarter_starts = {
            'Q1': date(year, 1, 1),
            'Q2': date(year, 4, 1),
            'Q3': date(year, 7, 1),
            'Q4': date(year, 10, 1)
        }

        if quarter not in quarter_starts:
            return 1

        start = quarter_starts[quarter]
        days_elapsed = (today - start).days
        week_num = (days_elapsed // 7) + 1

        return min(13, max(1, week_num))


class ObjectiveTracker:
    """Track and analyze objectives"""

    @staticmethod
    def calculate_objective_progress(objective_id: int) -> float:
        """Calculate progress toward an objective based on KPIs"""
        kpis = get_kpis_by_objective(objective_id)

        if not kpis:
            return 0.0

        total_progress = 0.0
        for kpi in kpis:
            current = kpi['current_value'] or 0
            target = kpi['target_value'] or 1

            if target == 0:
                progress = 0
            else:
                progress = min(100, (current / target) * 100)

            total_progress += progress

        return total_progress / len(kpis)

    @staticmethod
    def get_objectives_by_dimension(plan_id: int) -> Dict[str, List[Dict]]:
        """Group objectives by dimension"""
        objectives = get_objectives_by_plan(plan_id)
        grouped = {}

        for obj in objectives:
            dim_name = obj['dimension_name']
            if dim_name not in grouped:
                grouped[dim_name] = []

            # Add progress calculation
            obj['progress'] = ObjectiveTracker.calculate_objective_progress(obj['objective_id'])
            grouped[dim_name].append(obj)

        return grouped

    @staticmethod
    def get_status_color(status: str) -> str:
        """Get color for status indicator"""
        colors = {
            'Not Started': '⚪',
            'In Progress': '🟡',
            'At Risk': '🔴',
            'Completed': '🟢'
        }
        return colors.get(status, '⚪')

    @staticmethod
    def determine_status_from_progress(progress: float, target_date: Optional[str]) -> str:
        """Determine status based on progress and timeline"""
        if progress >= 100:
            return 'Completed'

        if not target_date:
            return 'In Progress' if progress > 0 else 'Not Started'

        try:
            target = datetime.fromisoformat(target_date).date()
            today = date.today()
            days_remaining = (target - today).days

            if days_remaining < 0:
                return 'At Risk'  # Past due

            # Calculate expected progress based on time
            # Simple linear expectation
            if days_remaining < 30 and progress < 70:
                return 'At Risk'

            return 'In Progress' if progress > 0 else 'Not Started'

        except (ValueError, TypeError):
            return 'In Progress' if progress > 0 else 'Not Started'


class DimensionAnalyzer:
    """Analyze dimension scores and trends"""

    @staticmethod
    def get_dimension_scores(user_id: int, days: int = 30) -> Dict[str, List[float]]:
        """Get dimension scores over time"""
        checkins = get_recent_checkins(user_id, limit=days, checkin_type='Weekly')

        dimension_scores = {}
        dimensions = get_all_dimensions()

        for dim in dimensions:
            dimension_scores[dim['dimension_name']] = []

        for checkin in reversed(checkins):  # Reverse to get chronological order
            if checkin.get('dimension_scores'):
                scores = checkin['dimension_scores']
                for dim_name, score in scores.items():
                    if dim_name in dimension_scores:
                        dimension_scores[dim_name].append(score)

        return dimension_scores

    @staticmethod
    def calculate_dimension_trend(scores: List[float]) -> str:
        """Calculate trend direction (improving, steady, declining)"""
        if len(scores) < 2:
            return '→'

        # Compare recent half vs. earlier half
        mid = len(scores) // 2
        earlier_avg = sum(scores[:mid]) / mid if mid > 0 else 0
        recent_avg = sum(scores[mid:]) / (len(scores) - mid) if len(scores) > mid else 0

        diff = recent_avg - earlier_avg

        if diff > 0.5:
            return '↗️'
        elif diff < -0.5:
            return '↘️'
        else:
            return '→'

    @staticmethod
    def get_latest_dimension_scores(user_id: int) -> Dict[str, float]:
        """Get most recent dimension scores"""
        checkins = get_recent_checkins(user_id, limit=1, checkin_type='Weekly')

        if not checkins or not checkins[0].get('dimension_scores'):
            # Return default scores
            dimensions = get_all_dimensions()
            return {dim['dimension_name']: 5.0 for dim in dimensions}

        return checkins[0]['dimension_scores']

    @staticmethod
    def get_dimension_status(score: float) -> str:
        """Get status indicator based on score"""
        if score >= 8:
            return '🟢'
        elif score >= 6:
            return '🟡'
        else:
            return '🔴'


class LeverAnalyzer:
    """Analyze lever usage and effectiveness"""

    @staticmethod
    def calculate_lever_consistency(user_id: int, lever_id: int, days: int = 30) -> float:
        """Calculate consistency percentage for a lever"""
        conn = get_connection()
        cursor = conn.cursor()

        # Get daily check-ins with this lever
        cursor.execute("""
            SELECT COUNT(*) as completed_count
            FROM daily_lever_tracking dlt
            JOIN checkins c ON dlt.checkin_id = c.checkin_id
            WHERE c.user_id = ? AND dlt.lever_id = ? AND dlt.completed = 1
                AND c.date >= date('now', '-' || ? || ' days')
        """, (user_id, lever_id, days))

        result = cursor.fetchone()
        completed = result['completed_count'] if result else 0

        conn.close()

        # Calculate percentage (assuming daily tracking)
        return (completed / days) * 100 if days > 0 else 0

    @staticmethod
    def get_lever_streak(user_id: int, lever_id: int) -> int:
        """Calculate current streak for a lever"""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT c.date, dlt.completed
            FROM checkins c
            LEFT JOIN daily_lever_tracking dlt ON c.checkin_id = dlt.checkin_id
                AND dlt.lever_id = ?
            WHERE c.user_id = ? AND c.checkin_type = 'Daily'
            ORDER BY c.date DESC
            LIMIT 90
        """, (lever_id, user_id))

        results = cursor.fetchall()
        conn.close()

        if not results:
            return 0

        streak = 0
        for row in results:
            if row['completed']:
                streak += 1
            else:
                break

        return streak

    @staticmethod
    def get_active_levers_for_plan(plan_id: int) -> List[Dict]:
        """Get all active levers with their stats"""
        user_levers = get_user_levers_by_plan(plan_id)

        # Get plan to find user_id
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM quarterly_plans WHERE plan_id = ?", (plan_id,))
        plan = cursor.fetchone()
        conn.close()

        if not plan:
            return []

        user_id = plan['user_id']

        for lever in user_levers:
            lever_id = lever['lever_id']
            lever['consistency'] = LeverAnalyzer.calculate_lever_consistency(user_id, lever_id, 30)
            lever['streak'] = LeverAnalyzer.get_lever_streak(user_id, lever_id)

        return user_levers


class InsightGenerator:
    """Generate insights from user data"""

    @staticmethod
    def generate_dimension_insights(user_id: int) -> List[str]:
        """Generate insights about dimension performance"""
        insights = []

        # Get recent dimension scores
        scores_history = DimensionAnalyzer.get_dimension_scores(user_id, days=30)

        for dim_name, scores in scores_history.items():
            if len(scores) >= 2:
                trend = DimensionAnalyzer.calculate_dimension_trend(scores)
                latest = scores[-1] if scores else 5

                if trend == '↗️' and latest >= 7:
                    insights.append(f"{dim_name} is trending up strongly ({latest}/10) - great work!")
                elif trend == '↘️' and latest <= 5:
                    insights.append(f"{dim_name} has declined to {latest}/10 - needs attention")
                elif latest >= 8:
                    insights.append(f"{dim_name} is performing excellently at {latest}/10")
                elif latest <= 4:
                    insights.append(f"{dim_name} is struggling at {latest}/10 - consider adjusting approach")

        return insights[:5]  # Limit to top 5 insights

    @staticmethod
    def generate_lever_insights(plan_id: int) -> List[str]:
        """Generate insights about lever consistency"""
        insights = []
        levers = LeverAnalyzer.get_active_levers_for_plan(plan_id)

        for lever in levers:
            consistency = lever.get('consistency', 0)
            streak = lever.get('streak', 0)
            name = lever['lever_name']

            if consistency >= 85:
                insights.append(f"🎉 {name}: {consistency:.0f}% consistency - excellent!")
            elif consistency < 50:
                insights.append(f"⚠️ {name}: Only {consistency:.0f}% consistency - needs focus")

            if streak >= 7:
                insights.append(f"🔥 {name}: {streak}-day streak!")

        return insights[:5]

    @staticmethod
    def generate_kpi_insights(plan_id: int) -> List[str]:
        """Generate insights about KPI progress"""
        insights = []
        objectives = get_objectives_by_plan(plan_id)

        for obj in objectives:
            kpis = get_kpis_by_objective(obj['objective_id'])
            for kpi in kpis:
                current = kpi['current_value'] or 0
                target = kpi['target_value'] or 1
                progress = (current / target * 100) if target > 0 else 0

                if progress >= 100:
                    insights.append(f"✅ {kpi['kpi_name']}: Target achieved!")
                elif progress >= 80:
                    insights.append(f"📈 {kpi['kpi_name']}: {progress:.0f}% complete - almost there!")
                elif progress < 30 and obj.get('target_date'):
                    try:
                        target_date = datetime.fromisoformat(obj['target_date']).date()
                        days_left = (target_date - date.today()).days
                        if days_left < 30:
                            insights.append(f"🚨 {kpi['kpi_name']}: Only {progress:.0f}% with {days_left} days left")
                    except:
                        pass

        return insights[:5]


class ProgressCalculator:
    """Calculate various progress metrics"""

    @staticmethod
    def calculate_overall_plan_progress(plan_id: int) -> float:
        """Calculate overall progress for a quarterly plan"""
        objectives = get_objectives_by_plan(plan_id)

        if not objectives:
            return 0.0

        total_progress = 0.0
        for obj in objectives:
            obj_progress = ObjectiveTracker.calculate_objective_progress(obj['objective_id'])
            total_progress += obj_progress

        return total_progress / len(objectives)

    @staticmethod
    def get_objectives_summary(plan_id: int) -> Dict[str, int]:
        """Get count of objectives by status"""
        objectives = get_objectives_by_plan(plan_id)

        summary = {
            'total': len(objectives),
            'not_started': 0,
            'in_progress': 0,
            'at_risk': 0,
            'completed': 0
        }

        for obj in objectives:
            status = obj['status'].lower().replace(' ', '_')
            if status in summary:
                summary[status] += 1

        return summary

    @staticmethod
    def calculate_time_remaining(quarter: str, year: int) -> int:
        """Calculate days remaining in quarter"""
        quarter_ends = {
            'Q1': date(year, 3, 31),
            'Q2': date(year, 6, 30),
            'Q3': date(year, 9, 30),
            'Q4': date(year, 12, 31)
        }

        end_date = quarter_ends.get(quarter)
        if not end_date:
            return 0

        today = date.today()
        days_remaining = (end_date - today).days

        return max(0, days_remaining)
