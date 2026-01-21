# Install Python on Windows - RIGHT NOW

## 🚨 You're seeing this error:
```
pip : The term 'pip' is not recognized
```

**This means: Python is NOT installed on your computer.**

---

## ✅ **SOLUTION: Install Python (5 Minutes)**

### **METHOD 1: Microsoft Store** (EASIEST - Do This!)

#### **Step 1: Open Microsoft Store**
1. Click **Start Menu** (Windows icon)
2. Type: `store`
3. Click **Microsoft Store** app

#### **Step 2: Search for Python**
1. In search box (top right), type: `Python 3.11`
2. Click on **"Python 3.11"**
   - Look for the one by "Python Software Foundation"
   - Should have blue/yellow snake logo

#### **Step 3: Install**
1. Click **"Get"** or **"Install"** button
2. Wait 2-3 minutes (it's downloading)
3. When done, it says **"Launch"** or **"Installed"**

#### **Step 4: Close PowerShell**
- Close your current PowerShell window completely
- Open a **NEW** PowerShell window (important!)

#### **Step 5: Verify Python Works**
In NEW PowerShell:
```powershell
python --version
```

**Expected output:**
```
Python 3.11.7
```

✅ **If you see this, Python is installed! Continue to Step 6.**

❌ **If you still get "not recognized", try METHOD 2 below.**

#### **Step 6: Install Required Packages**
```powershell
pip install numpy pandas scikit-learn scipy joblib
```

**This will take 2-3 minutes.** You'll see packages downloading.

#### **Step 7: Verify Packages Installed**
```powershell
python -c "import numpy, pandas, sklearn; print('Success!')"
```

**Expected output:**
```
Success!
```

✅ **Done! Now jump to "RUN THE DEMO" section below.**

---

## 📋 **METHOD 2: Download from Python.org** (If Store doesn't work)

### **Step 1: Download**
1. Go to: https://www.python.org/downloads/
2. You'll see a big yellow button: **"Download Python 3.11.x"**
3. Click it
4. Save file (e.g., `python-3.11.7-amd64.exe`) to Downloads folder

### **Step 2: Run Installer**
1. Open your **Downloads** folder
2. Double-click `python-3.11.7-amd64.exe`
3. **CRITICAL:** At bottom of installer, check the box:
   ```
   ☑️ Add Python 3.11 to PATH
   ```
   **DO NOT SKIP THIS!**
4. Click **"Install Now"** (big button)
5. Wait 2-3 minutes
6. Click **"Close"** when finished

### **Step 3: Restart PowerShell**
- Close all PowerShell windows
- Open a **NEW** PowerShell
- This is important! Windows needs to reload PATH

### **Step 4: Verify**
```powershell
python --version
```

**Expected:**
```
Python 3.11.7
```

### **Step 5: Install Packages**
```powershell
pip install numpy pandas scikit-learn scipy joblib
```

---

## 🚀 **RUN THE DEMO** (After Python is Installed)

### **Step 1: Navigate to Project**
```powershell
cd C:\Users\Nick\Cornell-Machine-Learning\scotts-ml-supply-chain
```

**Tip:** Adjust path if your project is in a different location.

### **Step 2: Run Demo**
```powershell
python examples\simple_demo.py
```

**Expected:** Demo runs for ~10 seconds and generates output.

---

## 🆘 **TROUBLESHOOTING**

### **Problem: "python: command not found" after installing**

**Cause:** PowerShell needs to be restarted.

**Solution:**
1. Close PowerShell completely
2. Open NEW PowerShell
3. Try `python --version` again

---

### **Problem: "pip: command not found" but Python works**

**Cause:** pip might not be in PATH.

**Solution:** Use `python -m pip` instead:
```powershell
python -m pip install numpy pandas scikit-learn scipy joblib
```

---

### **Problem: Microsoft Store says "This app can't run on your PC"**

**Cause:** Your Windows version might be too old.

**Solution:**
1. Check Windows version: Press `Windows + R`, type `winver`, press Enter
2. Need: Windows 10 (version 1607 or later) or Windows 11
3. If too old, use METHOD 2 (Python.org)

---

### **Problem: Installation stuck at "Resolving" or hangs**

**Solution:**
1. Press `Ctrl + C` to cancel
2. Try alternative command:
   ```powershell
   pip install --no-cache-dir numpy pandas scikit-learn scipy joblib
   ```

---

### **Problem: "Access is denied" or permission errors**

**Solution:** Run PowerShell as Administrator:
1. Press `Windows Key`
2. Type: `PowerShell`
3. Right-click **Windows PowerShell**
4. Click **"Run as Administrator"**
5. Try installation again

---

## ✅ **VERIFICATION CHECKLIST**

Run these commands in order. Each should succeed:

```powershell
# 1. Check Python installed
python --version
# ✅ Should show: Python 3.11.x

# 2. Check pip installed
pip --version
# ✅ Should show: pip 24.x from ...

# 3. Check packages installed
python -c "import numpy; print('NumPy:', numpy.__version__)"
# ✅ Should show: NumPy: 2.x.x

python -c "import pandas; print('Pandas:', pandas.__version__)"
# ✅ Should show: Pandas: 2.x.x

python -c "import sklearn; print('Scikit-learn:', sklearn.__version__)"
# ✅ Should show: Scikit-learn: 1.x.x

# 4. All together
python -c "import numpy, pandas, sklearn, scipy, joblib; print('✅ All packages working!')"
# ✅ Should show: ✅ All packages working!
```

**If all 4 checks pass, you're ready to run the demo! 🎉**

---

## 🎯 **YOUR EXACT COMMANDS (Copy-Paste After Installing Python)**

```powershell
# Step 1: Install packages
pip install numpy pandas scikit-learn scipy joblib

# Step 2: Navigate to project
cd C:\Users\Nick\Cornell-Machine-Learning\scotts-ml-supply-chain

# Step 3: Run demo
python examples\simple_demo.py

# Step 4: View outputs
dir demo_output

# Step 5: Open results in Excel
start excel demo_output\demand_forecast.csv
```

---

## 📊 **WHAT YOU'LL SEE**

After `python examples\simple_demo.py`:

```
================================================================================
SCOTTS MIRACLE-GRO ML SUPPLY CHAIN OPTIMIZER - SIMPLIFIED DEMO
================================================================================

Step 1: Initialize System
✅ Supply Chain Optimizer initialized

Step 2: Generate Artificial Data
✅ Generated sample data:
   - 17,934 sales records
   - 50 inventory records
   - 365 weather records

[... 8 more steps with optimization results ...]

Step 8: Export Results
✅ Saved demand_forecast.csv
✅ Saved inventory_policies.csv
✅ Saved inventory_status.csv

DEMO COMPLETE!
```

**Runtime:** 10 seconds
**Outputs:** 3 CSV files in `demo_output\` folder

---

## 🔗 **QUICK LINKS**

### **Download Python:**
- **Microsoft Store:** Press Windows Key → Type "store" → Search "Python 3.11"
- **Python.org:** https://www.python.org/downloads/

### **Check if Already Installed:**
```powershell
# This tells you if Python is installed and where:
where python
```

**If it shows a path like:**
```
C:\Users\Nick\AppData\Local\Programs\Python\Python311\python.exe
```
Then Python IS installed! Just install packages with pip.

**If it says:**
```
INFO: Could not find files for the given pattern(s).
```
Then Python is NOT installed. Follow METHOD 1 or METHOD 2 above.

---

## 💡 **PRO TIP: Upgrade pip First**

After installing Python, upgrade pip before installing packages:

```powershell
python -m pip install --upgrade pip
```

Then install packages:
```powershell
pip install numpy pandas scikit-learn scipy joblib
```

This ensures you have the latest pip version and avoids some errors.

---

## 🎉 **YOU'RE ALMOST THERE!**

**Summary:**
1. ✅ Install Python 3.11 (Microsoft Store or Python.org)
2. ✅ Close and reopen PowerShell
3. ✅ Run: `pip install numpy pandas scikit-learn scipy joblib`
4. ✅ Run: `python examples\simple_demo.py`

**Time:** 7 minutes total (5 min install + 2 min packages)

**Result:** Working ML system generating supply chain recommendations!

---

## 🆘 **STILL STUCK?**

After trying both methods, if you still get errors, run this diagnostic:

```powershell
# Copy ALL the output and share it:
python --version
pip --version
where python
echo $env:PATH
```

This will help identify what's wrong!

---

**Once Python is installed, the demo will work perfectly on your Windows machine! 🚀**
