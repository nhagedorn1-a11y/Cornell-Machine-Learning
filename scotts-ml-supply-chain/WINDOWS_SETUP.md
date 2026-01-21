# Windows Setup Guide

## 🪟 Running the Scotts ML Optimizer on Windows

You're seeing this error because Python isn't installed on your Windows machine:
```
Python was not found; run without arguments to install from the Microsoft Store
```

Here's how to fix it:

---

## ✅ **OPTION 1: Install from Microsoft Store** (Easiest - Recommended)

### **Step 1: Open Microsoft Store**
1. Press `Windows Key` on your keyboard
2. Type: `Microsoft Store`
3. Press `Enter`

### **Step 2: Search for Python**
1. In Microsoft Store, search for: `Python 3.11`
2. Look for **"Python 3.11"** (official version from Python Software Foundation)
3. Click **"Get"** or **"Install"**
4. Wait 2-3 minutes for installation

### **Step 3: Verify Installation**
Open PowerShell and type:
```powershell
python --version
```

You should see:
```
Python 3.11.x
```

### **Step 4: Install Required Packages**
```powershell
pip install numpy pandas scikit-learn scipy joblib
```

Wait 1-2 minutes for installation.

### **Step 5: Navigate to Project**
```powershell
cd Cornell-Machine-Learning\scotts-ml-supply-chain
```

### **Step 6: Run the Demo**
```powershell
python examples\simple_demo.py
```

**✅ You should see the demo output in 10 seconds!**

---

## ✅ **OPTION 2: Install from Python.org** (More Control)

### **Step 1: Download Python**
1. Go to: https://www.python.org/downloads/
2. Click **"Download Python 3.11.x"** (yellow button)
3. Save the installer (e.g., `python-3.11.7-amd64.exe`)

### **Step 2: Run Installer**
1. Double-click the downloaded file
2. **IMPORTANT:** Check ☑️ **"Add Python to PATH"** (bottom of installer)
3. Click **"Install Now"**
4. Wait 2-3 minutes
5. Click **"Close"** when done

### **Step 3: Verify Installation**
Open **NEW** PowerShell window (close old one) and type:
```powershell
python --version
```

You should see:
```
Python 3.11.7
```

### **Step 4: Install Packages**
```powershell
pip install numpy pandas scikit-learn scipy joblib
```

### **Step 5: Run the Demo**
```powershell
cd Cornell-Machine-Learning\scotts-ml-supply-chain
python examples\simple_demo.py
```

---

## 🔧 **Troubleshooting**

### **Problem 1: "python: command not found" after installation**

**Solution:** Close PowerShell completely and open a NEW window. Windows needs to refresh the PATH.

```powershell
# Close PowerShell, then reopen and try:
python --version
```

---

### **Problem 2: "'pip' is not recognized as an internal or external command"**

**Solution:** Use `python -m pip` instead:

```powershell
python -m pip install numpy pandas scikit-learn scipy joblib
```

---

### **Problem 3: Microsoft Store installation hangs**

**Solution:** Use Option 2 (Python.org) instead.

---

### **Problem 4: "Access Denied" or permission errors**

**Solution:** Run PowerShell as Administrator:
1. Right-click PowerShell icon
2. Select **"Run as Administrator"**
3. Try installation again

---

### **Problem 5: Wrong Python version (e.g., Python 2.7)**

**Solution:** Uninstall old Python first:
1. Open **Settings** → **Apps**
2. Find **Python 2.7** or old Python
3. Click **Uninstall**
4. Then install Python 3.11 (Option 1 or 2)

---

## 📂 **File Path Differences: Windows vs Linux**

### **Linux/Mac:**
```bash
cd /home/user/Cornell-Machine-Learning/scotts-ml-supply-chain
python3 examples/simple_demo.py
```

### **Windows:**
```powershell
cd C:\Users\Nick\Cornell-Machine-Learning\scotts-ml-supply-chain
python examples\simple_demo.py
```

**Key Differences:**
- Windows uses backslashes `\` instead of forward slashes `/`
- Windows uses drive letters `C:\` instead of `/home/`
- Windows uses `python` instead of `python3`

---

## 🚀 **Quick Start for Windows**

### **One-Line Install (PowerShell)**

If Python is already installed:
```powershell
pip install numpy pandas scikit-learn scipy joblib
```

### **Run the Demo**
```powershell
# Navigate to project (adjust path to your location)
cd C:\Users\Nick\Cornell-Machine-Learning\scotts-ml-supply-chain

# Run simplified demo
python examples\simple_demo.py

# OR run actionable guidance demo
python examples\actionable_guidance_demo.py
```

---

## 📊 **Expected Output**

After running `python examples\simple_demo.py`, you should see:

```
================================================================================
SCOTTS MIRACLE-GRO ML SUPPLY CHAIN OPTIMIZER - SIMPLIFIED DEMO
================================================================================

Step 1: Initialize System
--------------------------------------------------------------------------------
✅ Supply Chain Optimizer initialized

Step 2: Generate Artificial Data
--------------------------------------------------------------------------------
Generating sample data for prototype...
✅ Generated sample data:
   - 17,934 sales records
   - 50 inventory records
   - 365 weather records

[... continues with optimization results ...]

Step 8: Export Results
--------------------------------------------------------------------------------
✅ Saved demand_forecast.csv
✅ Saved inventory_policies.csv
✅ Saved inventory_status.csv

DEMO COMPLETE!
```

**Runtime:** ~10 seconds

**Output Files:** Located in `demo_output\` folder

---

## 💡 **Tips for Windows Users**

### **1. Use Tab Completion**
```powershell
# Type first few letters, then press Tab:
cd Cor[Tab]  → cd Cornell-Machine-Learning
```

### **2. View Output Files**
```powershell
# List files
dir demo_output

# View in Notepad
notepad demo_output\demand_forecast.csv

# View in Excel (if installed)
start excel demo_output\demand_forecast.csv
```

### **3. Copy Output**
```powershell
# Right-click in PowerShell to copy text
# Or redirect to file:
python examples\simple_demo.py > results.txt
```

### **4. Check Python Location**
```powershell
where python
# Shows: C:\Users\Nick\AppData\Local\Programs\Python\Python311\python.exe
```

---

## 🎯 **After Installation**

### **Verify Everything Works:**

```powershell
# 1. Check Python
python --version
# Expected: Python 3.11.x

# 2. Check pip
pip --version
# Expected: pip 24.x from ...

# 3. Check packages
python -c "import numpy, pandas, sklearn; print('✅ All packages installed')"
# Expected: ✅ All packages installed

# 4. Navigate to project
cd C:\Users\Nick\Cornell-Machine-Learning\scotts-ml-supply-chain

# 5. Run demo
python examples\simple_demo.py
# Expected: Full demo output in 10 seconds
```

**If all 5 steps work, you're ready!** ✅

---

## 📁 **Where Are the Files?**

After running the demo:

```powershell
# Output files are here:
C:\Users\Nick\Cornell-Machine-Learning\scotts-ml-supply-chain\demo_output\
```

**Files created:**
- `demand_forecast.csv` (7 KB)
- `inventory_policies.csv` (1 KB)
- `inventory_status.csv` (214 bytes)

**Open in Excel:**
```powershell
cd demo_output
start demand_forecast.csv
```

---

## 🆘 **Still Having Issues?**

### **Check Windows Version:**
```powershell
winver
```
**Requirement:** Windows 10 or Windows 11

### **Check .NET Framework:**
Python requires .NET Framework 4.5+
- Usually pre-installed on Windows 10/11
- If missing, download from Microsoft

### **Check Antivirus:**
Some antivirus software blocks Python:
- Temporarily disable antivirus
- Try installation again
- Re-enable antivirus after installation

### **Alternative: Use Windows Subsystem for Linux (WSL)**

If Windows installation keeps failing:

```powershell
# Install WSL (one-time setup)
wsl --install

# Restart computer

# Open Ubuntu terminal
wsl

# Then follow Linux instructions:
cd /mnt/c/Users/Nick/Cornell-Machine-Learning/scotts-ml-supply-chain
python3 examples/simple_demo.py
```

---

## 📧 **Your Specific Error**

You saw:
```
PS C:\Users\Nick> python3 examples/actionable_guidance_demo.py
Python was not found
```

**This means:**
1. Python is NOT installed on your system
2. OR Python is installed but not in PATH
3. OR You're using `python3` instead of `python` on Windows

**Fix:**
- Install Python (Option 1 or 2 above)
- Use `python` (not `python3`) on Windows
- Open NEW PowerShell after installation

**Corrected command:**
```powershell
python examples\actionable_guidance_demo.py
```
(Note: `python` not `python3`, and `\` not `/`)

---

## ✅ **Summary: 3 Steps to Success**

### **Step 1: Install Python**
- Microsoft Store: Search "Python 3.11", click Install
- OR Python.org: Download installer, check "Add to PATH"

### **Step 2: Install Packages**
```powershell
pip install numpy pandas scikit-learn scipy joblib
```

### **Step 3: Run Demo**
```powershell
cd C:\Users\Nick\Cornell-Machine-Learning\scotts-ml-supply-chain
python examples\simple_demo.py
```

**Expected Result:** Demo completes in 10 seconds with 3 CSV output files

---

## 🎉 **You're Ready!**

Once Python is installed, the system works identically on Windows, Mac, and Linux.

**All documentation files work on Windows:**
- `START_HERE.md`
- `STEP_BY_STEP.md`
- `HOW_IT_WORKS.md`
- `VALUE_SUMMARY.txt`

Just replace `/` with `\` in file paths!

---

## 🔗 **Quick Links**

- **Python Download:** https://www.python.org/downloads/
- **Microsoft Store Python:** ms-windows-store://pdp/?productid=9NRWMJP3717K
- **Pip Documentation:** https://pip.pypa.io/en/stable/installation/
- **WSL Installation:** https://learn.microsoft.com/en-us/windows/wsl/install

---

**Need more help? Open a new PowerShell and show me the output of:**
```powershell
python --version
pip --version
where python
```

And I'll help you debug! 🚀
