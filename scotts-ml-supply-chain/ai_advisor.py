"""
AI Advisor Integration Module
Supports both OpenAI (GPT-4) and Anthropic (Claude) APIs
"""

import os
from typing import List, Dict, Optional
import json


class AIAdvisor:
    """
    Unified interface for AI assistants (GPT-4 or Claude)
    Provides supply chain strategic guidance
    """

    def __init__(self, provider: str = "OpenAI", api_key: Optional[str] = None):
        """
        Initialize AI Advisor

        Args:
            provider: "OpenAI" or "Anthropic"
            api_key: API key for the chosen provider
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")

        if not self.api_key:
            raise ValueError(f"No API key provided for {provider}")

        self.system_prompt = self._get_system_prompt()
        self.conversation_history = []

    def _get_system_prompt(self) -> str:
        """System prompt that defines the AI's role"""
        return """You are a Supply Chain Strategic Advisor AI specializing in weather-driven
        demand forecasting and inventory optimization for retail businesses.

        Your expertise includes:
        - Analyzing weather patterns and their impact on product demand
        - Financial analysis (ROI, cost-benefit, risk assessment)
        - Inventory optimization strategies
        - Procurement timing and commodity ordering
        - Multi-channel distribution (e-commerce + brick & mortar)
        - Scenario planning and what-if analysis

        You have access to the user's supply chain data including:
        - Real-time weather forecasts (14-day rolling)
        - Historical sales patterns
        - Current inventory levels across all locations
        - Demand predictions by product and region
        - Commodity prices and lead times

        Provide:
        - Specific, actionable recommendations with deadlines
        - Financial impact calculations (revenue, cost, ROI)
        - Risk assessments
        - Priority rankings
        - Alternative scenarios when applicable

        Be concise but thorough. Use data to support recommendations.
        Format responses with clear headers, bullet points, and metrics."""

    def chat(self, user_message: str, context: Optional[Dict] = None) -> str:
        """
        Send message to AI and get response

        Args:
            user_message: User's question or prompt
            context: Optional context data (sales data, weather alerts, etc.)

        Returns:
            AI's response as string
        """

        # Add context to message if provided
        if context:
            enhanced_message = self._enhance_message_with_context(user_message, context)
        else:
            enhanced_message = user_message

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": enhanced_message
        })

        # Get response based on provider
        if self.provider == "OpenAI":
            response = self._call_openai(enhanced_message)
        elif self.provider == "Anthropic":
            response = self._call_claude(enhanced_message)
        else:
            response = "Error: Invalid provider"

        # Add response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        return response

    def _enhance_message_with_context(self, message: str, context: Dict) -> str:
        """Add relevant context data to user message"""

        context_str = "\n\n**Current Supply Chain Context:**\n"

        if 'weather_alerts' in context:
            context_str += f"\n**Weather Alerts:** {len(context['weather_alerts'])} active alerts\n"
            for alert in context['weather_alerts'][:3]:  # Top 3 alerts
                context_str += f"- {alert.get('event', 'N/A')}: {alert.get('region', 'N/A')}\n"

        if 'inventory_status' in context:
            context_str += f"\n**Inventory Status:**\n{context['inventory_status']}\n"

        if 'recent_sales' in context:
            context_str += f"\n**Recent Performance:**\n{context['recent_sales']}\n"

        return f"{message}\n{context_str}"

    def _call_openai(self, message: str) -> str:
        """Call OpenAI GPT-4 API"""
        try:
            import openai
            openai.api_key = self.api_key

            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history
                ],
                temperature=0.7,
                max_tokens=1500
            )

            return response.choices[0].message.content

        except ImportError:
            return """
            ⚠️ **OpenAI library not installed**

            To use GPT-4, install: `pip install openai`

            Then restart the app and enter your API key.
            """

        except Exception as e:
            return f"❌ **OpenAI API Error:** {str(e)}\n\nPlease check your API key and try again."

    def _call_claude(self, message: str) -> str:
        """Call Anthropic Claude API"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1500,
                system=self.system_prompt,
                messages=self.conversation_history
            )

            return response.content[0].text

        except ImportError:
            return """
            ⚠️ **Anthropic library not installed**

            To use Claude, install: `pip install anthropic`

            Then restart the app and enter your API key.
            """

        except Exception as e:
            return f"❌ **Claude API Error:** {str(e)}\n\nPlease check your API key and try again."

    def analyze_weather_alerts(self, alerts: List[Dict]) -> str:
        """Analyze weather alerts and provide strategic guidance"""

        alerts_summary = json.dumps(alerts, indent=2)

        prompt = f"""
        I have the following weather alerts for my supply chain:

        {alerts_summary}

        Please analyze these alerts and provide:
        1. Priority ranking (which to address first)
        2. Financial impact assessment
        3. Specific action recommendations with deadlines
        4. Risk if we ignore each alert
        5. Your overall strategic recommendation
        """

        return self.chat(prompt)

    def calculate_roi(self, investment: float, revenue_impact: float,
                     time_horizon_days: int = 30) -> str:
        """Calculate and explain ROI for an investment"""

        prompt = f"""
        Help me analyze this investment decision:

        - Investment Required: ${investment:,.2f}
        - Expected Revenue Impact: ${revenue_impact:,.2f}
        - Time Horizon: {time_horizon_days} days

        Please provide:
        1. ROI calculation and what it means
        2. Payback period
        3. Risk assessment
        4. Recommendation (approve/reject/modify)
        5. What could go wrong (downside scenarios)
        """

        return self.chat(prompt)

    def scenario_planning(self, scenario_type: str, parameters: Dict) -> str:
        """Help with what-if scenario planning"""

        params_str = json.dumps(parameters, indent=2)

        prompt = f"""
        I want to model this scenario for my supply chain:

        Scenario Type: {scenario_type}
        Parameters: {params_str}

        Please help me understand:
        1. What would likely happen (demand, inventory, revenue)
        2. How to prepare
        3. Financial impact (best case, worst case, most likely)
        4. Key actions to take now
        5. Early warning signs to watch for
        """

        return self.chat(prompt)

    def compare_alternatives(self, option_a: Dict, option_b: Dict) -> str:
        """Compare two alternative strategies"""

        prompt = f"""
        I'm deciding between two options:

        **Option A:**
        {json.dumps(option_a, indent=2)}

        **Option B:**
        {json.dumps(option_b, indent=2)}

        Please provide:
        1. Detailed comparison (pros/cons of each)
        2. Which is better and why
        3. Under what conditions would the other option be better
        4. Risk analysis for each
        5. Your recommendation
        """

        return self.chat(prompt)

    def executive_briefing(self, data_summary: Dict) -> str:
        """Generate executive briefing"""

        prompt = f"""
        Generate a concise executive briefing for senior leadership based on this data:

        {json.dumps(data_summary, indent=2)}

        Format:
        - **Key Findings** (3-5 bullet points)
        - **Critical Decisions Required** (what needs approval)
        - **Opportunities** (revenue/savings potential)
        - **Risks** (what keeps you up at night)
        - **Recommendation** (one clear strategic direction)

        Keep it under 300 words. Focus on business impact, not technical details.
        """

        return self.chat(prompt)

    def explain_to_non_technical(self, technical_content: str) -> str:
        """Translate technical jargon to plain English"""

        prompt = f"""
        Explain this to a non-technical executive:

        {technical_content}

        Use:
        - Plain English (no jargon)
        - Business terms (revenue, cost, risk)
        - Analogies when helpful
        - Clear action items
        """

        return self.chat(prompt)

    def reset_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []


# Quick test function
def test_ai_advisor():
    """Test the AI advisor (requires API key)"""
    try:
        # Test with dummy data
        advisor = AIAdvisor(provider="OpenAI", api_key="test-key")
        print("AI Advisor initialized successfully")

        print("\nSystem Prompt:")
        print(advisor.system_prompt)

    except Exception as e:
        print(f"Initialization test: {e}")


if __name__ == "__main__":
    test_ai_advisor()
