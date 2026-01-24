# 🔑 API Setup Guide - Connect Real Data

This guide will walk you through setting up **real weather and economic data** for your demand forecasting platform.

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Get Your API Keys

You need two free API keys:

#### 1️⃣ OpenWeather API (Weather Data)
**Free tier:** 1,000 calls/day, current weather + 5-day forecast

1. Go to: https://home.openweathermap.org/users/sign_up
2. Sign up for a free account (use your email)
3. Verify your email
4. Go to: https://home.openweathermap.org/api_keys
5. Copy your API key (looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

#### 2️⃣ FRED API (Economic Data)
**Free tier:** Unlimited calls, 800,000+ economic indicators

1. Go to: https://fredaccount.stlouisfed.org/login/secure/
2. Create a free account
3. Go to: https://fred.stlouisfed.org/docs/api/api_key.html
4. Click "Request API Key"
5. Fill out the form (just say "academic research" or "personal project")
6. Copy your API key (looks like: `1234567890abcdef1234567890abcdef`)

---

### Step 2: Create .env File

**Windows PowerShell:**
```powershell
# Navigate to project folder
cd C:\Users\<YourUsername>\Cornell-Machine-Learning\demand-forecasting-platform

# Copy the example file
Copy-Item .env.example .env

# Open .env in Notepad
notepad .env
```

**Mac/Linux:**
```bash
# Navigate to project folder
cd Cornell-Machine-Learning/demand-forecasting-platform

# Copy the example file
cp .env.example .env

# Open .env in your editor
nano .env
# or
code .env  # if you have VS Code
```

---

### Step 3: Paste Your API Keys

In the `.env` file, find these lines:

```bash
OPENWEATHER_API_KEY=your_openweather_api_key_here
FRED_API_KEY=your_fred_api_key_here
```

**Replace with your actual keys:**

```bash
OPENWEATHER_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
FRED_API_KEY=1234567890abcdef1234567890abcdef
```

**Save the file** (Ctrl+S in Notepad, Ctrl+O then Enter in nano)

---

### Step 4: Restart the App

**Stop the current app** (press Ctrl+C in both PowerShell windows)

**Start it again:**

```powershell
# Window 1: Start API
python simple_api.py

# Window 2: Start UI
streamlit run app.py
```

---

### Step 5: Verify It's Working

1. Open http://localhost:8501
2. Go to **"⚙️ Settings"** page (in sidebar)
3. Scroll down to **"External API Status"** section
4. You should see:
   - ✅ **Weather API:** "Connected - Receiving real weather data"
   - ✅ **Economic API:** "Connected - Receiving real economic data"
5. You'll also see **real economic indicators** at the bottom (Unemployment Rate, CPI, etc.)

---

## 🎯 What Real Data You'll Get

### Weather Data:
- **Current weather** for 5 DC locations (Atlanta, Chicago, NYC, LA, Seattle)
- **Temperature, humidity, wind speed, precipitation**
- **5-day forecast** with 3-hour intervals
- **Weather Impact** tab shows real temperature vs demand correlation

### Economic Data:
- **Unemployment Rate** (updated monthly)
- **Consumer Price Index (CPI)** (inflation)
- **GDP** (quarterly)
- **Consumer Sentiment** (monthly)
- **Retail Sales** (monthly)
- All displayed in Settings page with 3-month trends

---

## 🔧 Troubleshooting

### "Weather API: Connection failed"

**Problem:** API key is invalid or not active yet

**Solutions:**
1. OpenWeather keys take **10 minutes to activate** after creation - wait and retry
2. Check you copied the entire key (no spaces at start/end)
3. Make sure you're using the **free tier API key** (not the professional key)
4. Check your `.env` file is in the correct location: `demand-forecasting-platform/.env`

### "Economic API: Connection failed"

**Problem:** FRED API key is invalid

**Solutions:**
1. FRED keys usually activate **immediately**
2. Make sure you **requested and confirmed** the API key on their website
3. Check you copied the entire key correctly
4. Verify at: https://fred.stlouisfed.org/docs/api/fred/

### "Using simulated weather data"

**Problem:** App is running but not using real data

**Solutions:**
1. Make sure `.env` file exists (not `.env.example`)
2. Check API keys are correct in `.env`
3. **Restart both the API and UI** after changing `.env`
4. Check Windows didn't add `.txt` extension: file should be `.env` not `.env.txt`

### "No module named 'services.data_connectors'"

**Problem:** New connector files not found

**Solution:**
```powershell
# Pull the latest code
git pull origin claude/ml-commodity-ordering-xnRRS

# Restart both API and UI
```

---

## 🎨 Where Real Data Appears

Once connected, real data will show up in:

### 1. Analytics Page → Weather Correlation Tab
- Real 5-day temperature forecast
- Temperature vs demand correlation with real temps
- Shows which city you're viewing

### 2. Settings Page
- **API Status** section shows connection status
- **Current weather** for Atlanta
- **Latest economic indicators** with real values
- 5 economic metric cards with 3-month trends

### 3. Future Enhancements (Coming Soon)
- Dashboard page will use real weather for demand predictions
- Forecasting page will factor in real economic indicators
- Historical weather correlation in ML models

---

## 💡 Pro Tips

1. **Check API Limits:**
   - OpenWeather: 1,000 calls/day on free tier (plenty for this app)
   - FRED: Unlimited (truly unlimited!)

2. **API Keys are FREE forever** - no credit card required

3. **Keep your .env file private** - it's already in `.gitignore`

4. **Test in Settings page** before expecting data elsewhere

5. **Refresh the Streamlit page** (R key) after API keys are working to see live data

---

## 📸 How to Know It's Working

**Settings page should show:**

```
Weather API (OpenWeather)
✅ Connected - Receiving real weather data
Current in Atlanta: 72.4°F, partly cloudy

Economic API (FRED)
✅ Connected - Receiving real economic data
Unemployment Rate: 3.7% (as of 2026-01-01)
```

**Below that, you'll see 5 cards:**
- Unemployment Rate: 3.7% ↓ -0.2% (3mo)
- Consumer Price Index: 309.2 ↑ +1.1% (3mo)
- GDP: $28,452.3B ↑ +0.8% (3mo)
- Consumer Sentiment: 69.7 ↓ -2.3% (3mo)
- Retail Sales: $709,234M ↑ +0.5% (3mo)

---

## 🆘 Still Having Issues?

1. **Double-check your API keys** in the `.env` file
2. **Restart both API and UI** completely
3. **Wait 10 minutes** for OpenWeather key to activate (if brand new)
4. **Check Settings page** for specific error messages
5. **Make sure you're in the right directory** when starting the app

---

## ✅ Checklist

- [ ] Created OpenWeather account
- [ ] Got OpenWeather API key
- [ ] Created FRED account
- [ ] Got FRED API key
- [ ] Created `.env` file (not `.env.example`)
- [ ] Pasted both API keys into `.env`
- [ ] Saved `.env` file
- [ ] Restarted API server
- [ ] Restarted Streamlit UI
- [ ] Checked Settings page for green checkmarks
- [ ] Saw real economic data at bottom of Settings

---

🎉 **Once you see green checkmarks, you're done! Your platform is now using real-world data!**
