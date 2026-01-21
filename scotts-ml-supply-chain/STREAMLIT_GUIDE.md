# 🚀 Streamlit Dashboard - Complete Guide

## What You Get

A **weather-driven supply chain command center** with:
- 🌦️ Real-time weather alerts and demand predictions
- 📊 Executive dashboard with key metrics
- 🗺️ Interactive national deployment map
- 🤖 AI strategic advisor (GPT-4 or Claude integration)
- 📈 Analytics and insights
- 🎲 Scenario planning tools

---

## ✅ Windows Installation (Step-by-Step)

### Prerequisites

You should already have:
- ✅ Python 3.11+ installed
- ✅ pip working
- ✅ Project files downloaded

### Step 1: Navigate to Project

```powershell
cd "C:\Users\Nick\Desktop\Machine Learning\Cornell-Machine-Learning-claude-ml-commodity-ordering-xnRRS\scotts-ml-supply-chain"
```

### Step 2: Install Streamlit Dependencies

```powershell
pip install -r requirements_streamlit.txt
```

**This installs:**
- Streamlit (dashboard framework)
- Plotly (interactive charts)
- All ML libraries (if not already installed)
- Optional: OpenAI & Anthropic (for AI features)

**Expected time:** 2-3 minutes

### Step 3: Run the Dashboard

```powershell
streamlit run streamlit_app.py
```

**What happens:**
1. Streamlit server starts
2. Browser automatically opens to `http://localhost:8501`
3. You see the dashboard!

**If browser doesn't open:**
- Manually go to: http://localhost:8501

---

## 🎯 Quick Start Guide

### First Time Using the Dashboard

1. **Generate Sample Data**
   - Look in the left sidebar
   - Click "🎲 Generate Demo Data"
   - Wait 5 seconds for data generation

2. **Explore Weather Alerts** (Tab 1)
   - See 3 active weather-driven alerts
   - Each shows: Region, Forecast, Impact, Actions
   - Click "Execute" buttons to simulate actions

3. **View Executive Dashboard** (Tab 2)
   - See key metrics: Revenue, Inventory, Fill Rate
   - Interactive sales chart with weather overlay
   - Strategic actions summary

4. **Check Deployment Map** (Tab 3)
   - Interactive US map showing all locations
   - Color-coded by urgency (Red = High, Yellow = Normal, Green = Low)
   - Click regions for details

---

## 🤖 AI Integration (Optional but Powerful!)

### Get AI Strategic Guidance

#### Option 1: OpenAI (GPT-4)

**Step 1: Get API Key**
1. Go to: https://platform.openai.com/api-keys
2. Create account (if needed)
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

**Step 2: Add to Dashboard**
1. In sidebar, select "OpenAI (GPT-4)"
2. Paste your API key
3. You'll see "✅ OpenAI connected!"

**Cost:** ~$0.01-0.03 per query (very cheap for testing)

#### Option 2: Anthropic (Claude)

**Step 1: Get API Key**
1. Go to: https://console.anthropic.com/
2. Create account
3. Go to API Keys section
4. Generate new key
5. Copy the key

**Step 2: Add to Dashboard**
1. In sidebar, select "Anthropic (Claude)"
2. Paste your API key
3. You'll see "✅ Anthropic connected!"

**Cost:** Similar to OpenAI, very affordable

### Using the AI Advisor

Once connected, go to **"💬 AI Strategic Advisor"** tab:

**Ask questions like:**
- "What's my biggest risk in the next 30 days?"
- "Should I approve the $127K commodity order?"
- "Calculate ROI for the Atlanta inventory transfer"
- "What if there's a heatwave next week?"
- "Compare option A vs option B for me"

**AI can:**
- Analyze your weather alerts
- Calculate financial impacts
- Provide strategic recommendations
- Run scenario simulations
- Generate executive briefings

---

## 📊 Dashboard Features

### Tab 1: Weather Alert Center 🌦️

**What it shows:**
- Active weather alerts (heatwaves, early spring, etc.)
- Forecasted impact on demand
- Current inventory status
- Revenue at risk
- Recommended actions with deadlines

**Interactive elements:**
- Execute action buttons
- "Ask AI" section for weather analysis
- Priority indicators (🔴 Critical, 🟡 Warning, 🟢 Info)

### Tab 2: Executive Dashboard 📊

**Key metrics:**
- Revenue (with YoY comparison)
- Inventory value
- Fill rate percentage
- Alert count

**Charts:**
- Sales trend with temperature overlay
- Strategic actions table
- AI executive briefing (if API connected)

### Tab 3: Deployment Map 🗺️

**Interactive map showing:**
- All distribution center locations
- Current inventory vs target
- Priority regions color-coded
- Hover for details

**Regional breakdown table:**
- Current inventory
- Target inventory
- Gap (what's needed)
- Recommended shipments
- Priority level

### Tab 4: AI Strategic Advisor 💬

**Full chat interface with AI:**
- Ask any supply chain question
- Get strategic recommendations
- Financial analysis
- Scenario modeling
- Historical insights

**Quick action buttons:**
- Summarize all alerts
- Calculate total ROI
- Run what-if scenarios

### Tab 5: Analytics 📈

**Deep dive analysis:**
- Weather correlation charts
- Product performance matrix
- Demand drivers breakdown
- Historical patterns

**Shows which factors matter most:**
- Temperature impact: 87% correlation
- Rainfall impact: 43% correlation
- Etc.

### Tab 6: Scenario Planning 🎲

**Model "what if" scenarios:**
- Weather events (heatwave, cold snap, etc.)
- Competitor actions
- Price changes
- Supply disruptions
- Custom scenarios

**Get results:**
- Revenue impact
- Cost impact
- Net financial impact
- ROI calculations

---

## ⚙️ Configuration

### Sidebar Settings

**Forecast Horizon:**
- Slider: 7-180 days
- Default: 90 days
- Controls how far ahead to predict

**Service Level Target:**
- Slider: 90%-99%
- Default: 95%
- Higher = fewer stockouts, more inventory cost

### Data Sources

**Option 1: Generate Sample Data** *(Recommended for demo)*
- Click "Generate Demo Data"
- Creates realistic artificial data
- Includes seasonal patterns
- Weather correlations built-in

**Option 2: Upload CSV Files**
- Sales Data (CSV)
- Inventory Data (CSV)
- Weather Data (CSV)
- *Feature coming soon*

**Option 3: Connect to Database**
- Enter connection string
- Click Connect
- *Feature coming soon*

---

## 🎨 Customization

### Change Theme

**Light Theme (Default):**
- Good for presentations
- High contrast

**Dark Theme:**
- Click ⚙️ in top-right corner of Streamlit
- Settings → Theme → Dark

### Modify Dashboard

The dashboard is fully customizable:

**File:** `streamlit_app.py`

**Common modifications:**
1. **Add more weather alerts** (line 250)
2. **Change metrics displayed** (line 400)
3. **Customize AI prompts** (ai_advisor.py)
4. **Add new tabs** (line 180)

---

## 🐛 Troubleshooting

### Issue: "Streamlit command not found"

**Solution:**
```powershell
python -m streamlit run streamlit_app.py
```

### Issue: "ModuleNotFoundError: No module named 'plotly'"

**Solution:**
```powershell
pip install plotly
```

Or install all:
```powershell
pip install -r requirements_streamlit.txt
```

### Issue: Port 8501 already in use

**Solution 1:** Kill existing Streamlit process
```powershell
# Find process
netstat -ano | findstr :8501

# Kill it (replace PID with actual number)
taskkill /F /PID <PID>
```

**Solution 2:** Use different port
```powershell
streamlit run streamlit_app.py --server.port 8502
```

Then open: http://localhost:8502

### Issue: AI features not working

**Check:**
1. ✅ API key is correct (no extra spaces)
2. ✅ API key has credits/billing enabled
3. ✅ Library installed: `pip install openai` or `pip install anthropic`
4. ✅ Internet connection working

**Test API key:**
```python
# Test OpenAI
import openai
openai.api_key = "your-key-here"
print(openai.Model.list())  # Should list models

# Test Anthropic
import anthropic
client = anthropic.Anthropic(api_key="your-key-here")
print("API key works!")
```

### Issue: Dashboard is slow

**Solutions:**
1. **Reduce data size:**
   - Generate fewer products (line 27 in streamlit_app.py)
   - Shorter history (365 → 180 days)

2. **Close other browser tabs**

3. **Use Chrome or Edge** (better Streamlit performance than Firefox/Safari)

### Issue: Charts not displaying

**Solution:**
```powershell
pip install --upgrade plotly
```

Restart Streamlit after upgrade.

---

## 🚀 Advanced Features

### Deploy to Cloud (Streamlit Cloud)

**Free hosting for your dashboard:**

1. **Push code to GitHub** (if not already there)

2. **Go to:** https://streamlit.io/cloud

3. **Click "New app"**

4. **Connect GitHub repo:**
   - Repository: Your repo
   - Branch: main or your branch
   - Main file: streamlit_app.py

5. **Add secrets** (for API keys):
   - Settings → Secrets
   - Add your API keys

6. **Deploy!**
   - Get public URL: `yourapp.streamlit.app`
   - Share with anyone

**Benefits:**
- Free (for public repos)
- HTTPS automatically
- Updates when you push to GitHub
- No installation needed for users

### Package as Windows .exe

**Make standalone application:**

```powershell
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --windowed --add-data "streamlit_app.py;." --name "SupplyChainDashboard" streamlit_app.py

# Find exe in dist/ folder
```

**Note:** Streamlit apps are best run via web interface (browser). Executable packaging has limitations.

### Run on Network (LAN Access)

**Let others on your network access:**

```powershell
streamlit run streamlit_app.py --server.address 0.0.0.0
```

Then share your IP address:
- Find IP: `ipconfig` (look for IPv4)
- Share: `http://YOUR-IP:8501`

Others on same WiFi can access!

---

## 💡 Pro Tips

### Tip 1: Use AI for Complex Questions

Don't just ask "What should I do?"

**Instead:**
- "Compare the ROI of ordering now vs waiting 1 week"
- "What's the risk if we ignore the heatwave alert?"
- "Model a scenario where temperature is 15°F higher than forecast"

**AI gives better answers with specific questions!**

### Tip 2: Save Your Favorite Scenarios

When AI gives a good scenario analysis:
1. Copy the results
2. Paste into a document
3. Reference later for similar situations

### Tip 3: Export Data

**Download any table:**
- Hover over table
- Click download icon (top-right)
- Choose CSV or Excel

### Tip 4: Keyboard Shortcuts

- `R` = Rerun dashboard (refresh data)
- `C` = Clear cache
- `/` = Focus search (command palette)

### Tip 5: Bookmark Specific Tabs

Each tab has its own URL fragment:
- `http://localhost:8501#weather-alerts`
- `http://localhost:8501#ai-advisor`

Bookmark these for quick access!

---

## 📖 Next Steps

1. **✅ Run the dashboard** with sample data
2. **🤖 Add AI API key** for strategic guidance
3. **📊 Explore all 6 tabs** to see features
4. **🎲 Try scenario planning** with AI
5. **📤 Deploy to Streamlit Cloud** (optional)
6. **📁 Load your real data** (when ready)

---

## 🆘 Need Help?

**Common questions:**

**Q: Do I need AI to use this?**
A: No! AI is optional. The weather alerts and forecasting work without it.

**Q: How much does AI cost?**
A: Very cheap for testing: ~$0.01-0.03 per question. About $10 = 500-1000 queries.

**Q: Can multiple people use this?**
A: Yes! Deploy to Streamlit Cloud or run on network (see Advanced Features above).

**Q: Is my data secure?**
A: Sample data is generated locally. If you add API keys, they're only in your session (not stored).

**Q: Can I customize the dashboard?**
A: Yes! Edit `streamlit_app.py` - it's all Python code you can modify.

---

## 🎉 You're Ready!

**Start command:**
```powershell
streamlit run streamlit_app.py
```

**Then:**
1. Generate demo data
2. Explore weather alerts
3. Add AI key (optional)
4. Ask strategic questions!

**Enjoy your weather-powered supply chain command center! 🌦️💰**
