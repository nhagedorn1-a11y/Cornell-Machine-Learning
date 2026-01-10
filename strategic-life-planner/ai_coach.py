"""
AI Coaching integration using Claude API
"""

import os
from typing import Optional, List, Dict
import anthropic


class AICoach:
    """AI-powered coaching using Claude API"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI Coach with API key"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None

    def is_available(self) -> bool:
        """Check if AI coaching is available"""
        return self.client is not None

    def refine_objective(self, objective: str, dimension: str) -> str:
        """
        Refine a user's objective to make it SMART
        (Specific, Measurable, Achievable, Relevant, Time-bound)
        """
        if not self.is_available():
            return objective

        prompt = f"""The user wants to achieve: '{objective}'
This is in the {dimension} dimension of their life.

Make this objective SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
Return only the refined objective in a single sentence, no explanation or preamble."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"AI Coach error: {e}")
            return objective

    def generate_weekly_insights(
        self,
        dimension_scores: Dict[str, float],
        completed_levers: List[str],
        kpi_data: List[Dict],
        wins: str,
        challenges: str
    ) -> str:
        """Generate weekly insights based on user data"""
        if not self.is_available():
            return "AI insights unavailable. Please configure ANTHROPIC_API_KEY."

        # Format the data for the prompt
        scores_text = "\n".join([f"- {dim}: {score}/10" for dim, score in dimension_scores.items()])
        levers_text = "\n".join([f"- {lever}" for lever in completed_levers]) if completed_levers else "None logged"

        kpi_text = ""
        for kpi in kpi_data[:5]:  # Limit to 5 KPIs
            current = kpi.get('current_value', 0)
            target = kpi.get('target_value', 1)
            progress = (current / target * 100) if target > 0 else 0
            kpi_text += f"- {kpi.get('kpi_name', 'Unknown')}: {current}/{target} ({progress:.0f}%)\n"

        prompt = f"""You are an executive coach analyzing a high-performing professional's weekly progress.

**This Week's Data:**

Dimension Scores:
{scores_text}

Levers Completed:
{levers_text}

Key Performance Indicators:
{kpi_text}

Wins:
{wins if wins else 'None recorded'}

Challenges:
{challenges if challenges else 'None recorded'}

Generate 3-5 actionable insights in bullet points. Be:
- Specific and data-driven
- Encouraging but honest
- Focused on patterns and trends
- Actionable with concrete recommendations

Keep insights concise (1-2 sentences each)."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"AI Coach error: {e}")
            return f"Error generating insights: {str(e)}"

    def recommend_levers(
        self,
        objectives: List[Dict],
        available_levers: List[Dict],
        dimension: Optional[str] = None
    ) -> str:
        """Recommend levers based on objectives"""
        if not self.is_available():
            return "AI recommendations unavailable. Please configure ANTHROPIC_API_KEY."

        # Format objectives
        obj_text = "\n".join([
            f"- [{obj.get('dimension_name', 'Unknown')}] {obj.get('objective_text', '')}"
            for obj in objectives
        ])

        # Format available levers (limit to 20 for context)
        levers_by_dim = {}
        for lever in available_levers[:20]:
            dim = lever.get('dimension_name', 'Unknown')
            if dim not in levers_by_dim:
                levers_by_dim[dim] = []
            levers_by_dim[dim].append(lever['lever_name'])

        levers_text = ""
        for dim, lever_names in levers_by_dim.items():
            levers_text += f"\n{dim}:\n"
            levers_text += "\n".join([f"  - {name}" for name in lever_names])

        focus = f" Focus on {dimension} levers." if dimension else ""

        prompt = f"""User's quarterly objectives:
{obj_text}

Available levers from the library:
{levers_text}

Recommend the top 5-7 levers that would most effectively support these objectives.{focus}
For each lever, explain in one sentence why it's relevant.

Format as:
- **Lever Name**: Brief explanation of relevance"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"AI Coach error: {e}")
            return f"Error generating recommendations: {str(e)}"

    def suggest_sprint_focus(
        self,
        objectives: List[str],
        sprint_number: int,
        previous_results: Optional[str] = None
    ) -> Dict[str, any]:
        """Suggest theme and focus areas for a sprint"""
        if not self.is_available():
            return {
                'theme': f'Sprint {sprint_number}',
                'focus_areas': ['Review objectives', 'Set priorities', 'Take action']
            }

        obj_text = "\n".join([f"- {obj}" for obj in objectives])

        prev_context = ""
        if previous_results and sprint_number > 1:
            prev_context = f"\nPrevious sprint outcomes:\n{previous_results}\n"

        prompt = f"""User's quarterly objectives:
{obj_text}
{prev_context}
Current sprint: {sprint_number} of 6 (two-week sprint)

Suggest:
1. A compelling theme for this sprint (3-5 words)
2. 3-5 specific, actionable focus areas for the two weeks

Ensure focus areas are:
- Concrete and achievable in 2 weeks
- Aligned with quarterly objectives
- Build momentum toward goals

Format your response as:
THEME: [theme name]
FOCUS:
- [Focus area 1]
- [Focus area 2]
- [Focus area 3]"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.strip()

            # Parse response
            lines = response.split('\n')
            theme = 'Sprint Focus'
            focus_areas = []

            for line in lines:
                if line.startswith('THEME:'):
                    theme = line.replace('THEME:', '').strip()
                elif line.strip().startswith('-'):
                    focus_areas.append(line.strip()[1:].strip())

            return {
                'theme': theme,
                'focus_areas': focus_areas[:5]
            }

        except Exception as e:
            print(f"AI Coach error: {e}")
            return {
                'theme': f'Sprint {sprint_number}',
                'focus_areas': ['Review objectives', 'Set priorities', 'Take action']
            }

    def analyze_balance(self, dimension_scores: Dict[str, float]) -> str:
        """Analyze balance across life dimensions"""
        if not self.is_available():
            return "AI analysis unavailable."

        scores_text = "\n".join([f"- {dim}: {score}/10" for dim, score in dimension_scores.items()])

        prompt = f"""Analyze this person's life balance based on their dimension scores:

{scores_text}

Provide:
1. Overall assessment of balance (1-2 sentences)
2. Biggest strength (which dimension is thriving)
3. Biggest opportunity (which dimension needs attention)
4. One specific recommendation

Be encouraging but honest. Keep response to 4-5 sentences total."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"AI Coach error: {e}")
            return f"Error analyzing balance: {str(e)}"


# Singleton instance
_ai_coach = None


def get_ai_coach() -> AICoach:
    """Get or create AI coach instance"""
    global _ai_coach
    if _ai_coach is None:
        _ai_coach = AICoach()
    return _ai_coach
