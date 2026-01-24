# 🚀 UI Quick Start Guide

## Welcome to the Demand Forecasting Platform!

This guide will get you up and running with the **rich, visually compelling UI** in just 2 minutes.

---

## 🎯 What You'll Get

- **Beautiful Dashboard** with real-time metrics and KPIs
- **Interactive Forecasting** with 30-day predictions and confidence intervals
- **Inventory Optimization** recommendations with ROI analysis
- **Advanced Analytics** with charts, trends, and insights
- **Weather Correlation** analysis
- **Dark Mode** modern UI with gradient cards

---

## ⚡ Quick Start (Windows)

### Option 1: One-Click Startup (Recommended)

1. Open File Explorer
2. Navigate to `Cornell-Machine-Learning\demand-forecasting-platform`
3. Double-click `start.bat`
4. Wait ~10 seconds for everything to load
5. Your browser will automatically open to the UI!

### Option 2: Manual Startup

```powershell
# 1. Open PowerShell
# 2. Navigate to project
cd C:\Users\<YourUsername>\Cornell-Machine-Learning\demand-forecasting-platform

# 3. Install UI dependencies
pip install streamlit pandas plotly requests

# 4. Start API (in first PowerShell window)
python simple_api.py

# 5. Start UI (in second PowerShell window)
streamlit run app.py
```

---

## 🐧 Quick Start (Linux/Mac)

```bash
# 1. Navigate to project
cd Cornell-Machine-Learning/demand-forecasting-platform

# 2. Make start script executable
chmod +x start.sh

# 3. Run startup script
./start.sh
```

---

## 🌐 Accessing the Platform

Once started, you'll have two services running:

| Service | URL | Description |
|---------|-----|-------------|
| **Web UI** | http://localhost:8501 | Main dashboard interface |
| **API Docs** | http://localhost:8001/docs | Interactive API documentation |

**Open your browser** and go to: **http://localhost:8501**

---

## 🎨 UI Features

### 🏠 Dashboard Page
- **4 KPI Cards** - Forecast Accuracy, Fill Rate, Inventory Turnover, Cost Savings
- **30-Day Forecast Chart** - Interactive Plotly chart with confidence intervals
- **Key Insights Panel** - Real-time alerts and recommendations
- **Performance Metrics** - Model comparison, inventory health, weekly trends

### 📈 Forecasting Page
- **Interactive Forecasting** - Configure horizon, confidence level, and model
- **Visual Predictions** - Beautiful charts with confidence bands
- **Detailed Tables** - Complete forecast data grid
- **CSV Export** - Download forecasts for Excel/analysis

### 📦 Inventory Optimization Page
- **Rebalancing Recommendations** - AI-driven transfer suggestions
- **Priority System** - HIGH/MEDIUM/LOW priority color coding
- **ROI Analysis** - Cost vs ROI visualizations
- **One-Click Actions** - Approve transfers and run optimizations

### 📊 Analytics Page
Four tabs of deep analytics:
- **Forecast Accuracy** - MAPE and RMSE trends over time
- **Inventory Health** - Turnover rates by category
- **Financial Impact** - Cost savings breakdown pie chart
- **Weather Correlation** - Temperature vs demand scatter plots

### ⚙️ Settings Page
- **System Information** - Platform version, environment, capabilities
- **Model Configuration** - Adjust forecast horizon, confidence levels
- **Optimization Settings** - Rebalance thresholds, safety stock
- **API Configuration** - Connection testing and setup

---

## 🎨 Visual Design

The UI features:
- **Modern Dark Theme** with Plotly Dark charts
- **Gradient Cards** - Purple, pink, cyan, green gradients
- **Smooth Animations** - Hover effects and transitions
- **Responsive Layout** - Works on desktop, tablet, and mobile
- **Interactive Charts** - Zoom, pan, hover tooltips
- **Color-Coded Data** - Priority levels, status indicators

---

## 🔧 Troubleshooting

### UI Won't Start

**Error:** `ModuleNotFoundError: No module named 'streamlit'`

**Solution:**
```powershell
pip install -r requirements-ui.txt
```

---

### Port Already in Use

**Error:** `Port 8501 is already in use`

**Solution 1 - Use different port:**
```powershell
streamlit run app.py --server.port 8502
```

**Solution 2 - Kill existing process:**
```powershell
# Windows
netstat -ano | findstr :8501
taskkill /PID <process_id> /F

# Linux/Mac
lsof -ti:8501 | xargs kill -9
```

---

### API Connection Failed

**Symptom:** Red "API Offline" badge in sidebar

**Solution:**
1. Make sure API is running:
   ```powershell
   python simple_api.py
   ```
2. Check API health at: http://localhost:8001/health
3. Verify API URL in Settings page

---

### Browser Doesn't Open Automatically

**Solution:**
Manually open your browser and navigate to:
- **http://localhost:8501** (UI)
- **http://127.0.0.1:8501** (if localhost doesn't work)

---

## 📱 Supported Browsers

- ✅ Google Chrome (Recommended)
- ✅ Microsoft Edge
- ✅ Mozilla Firefox
- ✅ Safari (Mac)

---

## 🎯 Next Steps

1. **Explore the Dashboard** - Check out the KPIs and forecast chart
2. **Generate a Forecast** - Go to Forecasting page and click "Generate Forecast"
3. **Review Recommendations** - Visit Inventory Optimization for transfer suggestions
4. **Dive into Analytics** - Explore the 4 analytics tabs
5. **Customize Settings** - Adjust parameters in the Settings page

---

## 💡 Tips for Best Experience

1. **Keep both API and UI running** - Start API first, then UI
2. **Use Chrome** for best performance and compatibility
3. **Full screen mode** (F11) for immersive experience
4. **Hover over charts** to see detailed data points
5. **Try different SKUs/locations** using the sidebar filters

---

## 🆘 Need Help?

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Verify both services are running (API + UI)
3. Check the console for error messages
4. Restart both services

**Still stuck?** Check the main [README.md](README.md) for more details.

---

## 🎉 Enjoy Your Forecasting Platform!

You now have a **production-grade, visually stunning** demand forecasting platform running locally. Explore the features, generate forecasts, and optimize your inventory!

**Built with ❤️ by the Supply Chain Intelligence Team**
