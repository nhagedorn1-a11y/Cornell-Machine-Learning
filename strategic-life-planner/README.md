# 🎯 Strategic Life Planner

A McKinsey-style quarterly life and wellness planning application for high-performing professionals. Plan, track, and optimize across all six life dimensions with AI-powered coaching.

![Strategic Life Planner](https://img.shields.io/badge/Status-Beta_MVP-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)

## 🌟 Features

### Core Capabilities

- **📊 Executive Dashboard**: Real-time view of progress across all life dimensions
- **🗓️ Quarterly Planning Wizard**: 7-step guided planning process with AI assistance
- **✅ Daily Check-ins**: 2-minute daily tracking of habits and progress
- **📝 Weekly Reviews**: Comprehensive 10-minute reflection and planning
- **🔧 Lever Library**: 48 evidence-based actions across 6 life dimensions
- **📈 Analytics & Insights**: Trends, correlations, and AI-generated recommendations
- **🤖 AI Coach**: Claude-powered objective refinement and personalized insights

### Six Life Dimensions

1. **💼 Career**: Professional growth and achievements
2. **🏃 Health**: Physical and mental wellbeing
3. **💰 Finance**: Wealth building and financial planning
4. **❤️ Relationships**: Family, friends, and connections
5. **📚 Personal Growth**: Learning and skill development
6. **🌟 Impact**: Community contribution and legacy

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Anthropic API key (optional, for AI features)

### Installation

1. **Clone the repository**:
```bash
cd strategic-life-planner
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (optional for AI features):
```bash
# Create .env file
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

4. **Initialize database with sample data**:
```bash
python seed_sample_data.py
```

5. **Run the application**:
```bash
streamlit run app.py
```

6. **Open your browser**:
The app will automatically open at `http://localhost:8501`

## 📖 Usage Guide

### Creating Your First Quarterly Plan

1. Navigate to **🗓️ Quarterly Planning** in the sidebar
2. Complete the 7-step wizard:
   - **Step 1**: Reflect on previous quarter
   - **Step 2**: Define your 1-year vision
   - **Step 3**: Set 1-3 SMART objectives per dimension
   - **Step 4**: Define 2-4 KPIs per objective
   - **Step 5**: Select 5-10 action levers
   - **Step 6**: Plan 6 two-week sprints
   - **Step 7**: Review and commit

### Daily Workflow

**Morning** (2 minutes):
- Complete daily check-in
- Review today's lever targets
- Set intentions

**Evening** (2 minutes):
- Mark completed levers
- Log quick win or challenge
- Rate energy and mood

### Weekly Workflow

**Sunday Planning** (10 minutes):
- Complete weekly review
- Rate each life dimension (1-10)
- Update KPI values
- Reflect on wins and challenges
- Generate AI insights
- Plan adjustments for next week

### Dashboard Insights

The Executive Dashboard shows:
- Overall quarterly progress
- Current week and days remaining
- Dimension scores with trend arrows
- Active objectives with progress bars
- Key metrics (KPIs)
- AI-generated insights
- Recent activity feed

## 🏗️ Project Structure

```
strategic-life-planner/
├── app.py                      # Main Streamlit application
├── database.py                 # SQLite setup and queries
├── models.py                   # Business logic and calculations
├── ai_coach.py                 # Claude API integration
├── utils.py                    # Helper functions and UI components
├── seed_sample_data.py         # Sample data generator
├── requirements.txt            # Python dependencies
├── data/
│   ├── levers_library.json    # Pre-populated 48 levers
│   └── database.db            # SQLite database (auto-created)
└── assets/
    └── style.css              # Custom CSS (optional)
```

## 🎨 Design Philosophy

### McKinsey-Inspired Aesthetics

- **Professional**: Clean, executive-friendly interface
- **Data-Driven**: Metrics, charts, and progress tracking
- **Actionable**: Focus on concrete next steps
- **Holistic**: Balance across all life dimensions

### Color Palette

- **Primary Navy**: #003D5B (headers, key text)
- **Secondary Teal**: #00A3A1 (buttons, accents)
- **Accent Gold**: #F4B942 (highlights, warnings)
- **Status Colors**: Green (#2D9B4B), Yellow (#F4B942), Red (#D9534F)

## 🤖 AI Features

### Available with ANTHROPIC_API_KEY

1. **Objective Refinement**: Make objectives SMART with one click
2. **Weekly Insights**: Personalized analysis of progress and patterns
3. **Lever Recommendations**: AI suggests best levers for your objectives
4. **Sprint Planning**: AI generates sprint themes and focus areas
5. **Balance Analysis**: AI assesses life balance and recommends adjustments

### Without API Key

The app works fully without AI, you just won't get:
- Automated objective refinement
- AI-generated insights
- Intelligent recommendations

## 📊 Sample Data

The app includes sample data for **Nick Hagedorn** (Cornell EMBA, veteran, Scotts):

- **Q1 2026 Plan** with objectives across all 6 dimensions
- **Career**: Director promotion, executive presentations
- **Health**: Run 3x/week, lose 15 lbs, improve sleep
- **Finance**: Save $25K, max 401k
- **Relationships**: Weekly date nights, daily kids time
- **Personal Growth**: Complete EMBA, read 12 books
- **Impact**: Mentor 2 veterans, volunteer 5 hrs/month

To use sample data:
```bash
python seed_sample_data.py
```

## 🔧 Configuration

### Database

SQLite database auto-created at `data/database.db`

### Environment Variables

Create a `.env` file:
```env
ANTHROPIC_API_KEY=your_api_key_here
```

Get an API key at: https://console.anthropic.com/

## 📈 Analytics Features

### Dimension Trends
- Multi-line chart showing scores over time
- Trend indicators (↗️ improving, → steady, ↘️ declining)
- Radar chart for life balance visualization

### KPI Tracking
- Progress bars with current vs. target
- Historical line charts
- On-track/at-risk status indicators
- Automatic progress calculations

### Lever Consistency
- Percentage completion rates
- Current streak tracking
- GitHub-style heatmaps (coming soon)
- Correlation with outcomes

## 🛠️ Technical Stack

- **Frontend**: Streamlit (Python web framework)
- **Database**: SQLite with Python sqlite3
- **AI**: Anthropic Claude API (Haiku 3.5)
- **Charts**: Plotly for interactive visualizations
- **Data**: Pandas for data manipulation

## 📱 Deployment

### Streamlit Cloud (Recommended)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Add `ANTHROPIC_API_KEY` to secrets
5. Deploy!

### Local Network

```bash
streamlit run app.py --server.address 0.0.0.0
```

### Docker (Future)

Coming soon: Dockerfile for containerized deployment

## 🎯 Roadmap

### v1.0 (Current - Beta MVP)
- ✅ Quarterly planning wizard
- ✅ Executive dashboard
- ✅ Daily/weekly check-ins
- ✅ Lever library (48 levers)
- ✅ Analytics and insights
- ✅ AI coaching features

### v1.1 (Next)
- [ ] Sprint progress tracking
- [ ] Enhanced mobile responsiveness
- [ ] Export plan to PDF
- [ ] Email reminders for check-ins
- [ ] Advanced correlation analysis

### v2.0 (Future)
- [ ] Team/family shared planning
- [ ] Accountability partner matching
- [ ] Native mobile app (iOS/Android)
- [ ] Integration with fitness trackers
- [ ] Advanced ML predictions
- [ ] API for third-party tools

## 🤝 Contributing

This is a beta MVP. Feedback and contributions welcome!

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Evidence-based levers**: Curated from research in psychology, productivity, and wellness
- **McKinsey methodology**: Inspired by strategic planning frameworks
- **AI coaching**: Powered by Anthropic Claude
- **Target audience**: High-performing professionals (EMBA students, executives, entrepreneurs)

## 📧 Support

For questions or issues:
- Open an issue on GitHub
- Email: support@example.com
- Documentation: See inline code comments

## 🎓 Designed For

- **Cornell EMBA students** balancing school, career, and life
- **Military veterans** transitioning to civilian leadership roles
- **Executives** seeking holistic life optimization
- **Entrepreneurs** managing multiple priorities
- **Anyone** committed to intentional, data-driven personal growth

---

**Built with ❤️ for strategic thinkers who execute**

*Version: 1.0.0-beta*
*Last Updated: January 2026*
