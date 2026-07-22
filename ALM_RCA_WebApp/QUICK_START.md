# 🚀 Quick Start Guide - ALM RCA Web Application

Get up and running in 3 minutes!

## 📋 Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.8+ installed
- ✅ pip (Python package manager)
- ✅ A defect file (CSV or Excel format)

## ⚡ Installation (One-Time Setup)

### Step 1: Open Terminal/Command Prompt

Navigate to the project folder:
```bash
cd C:\Users\AnkanDua\Desktop\ALM_RCA_WebApp
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- pandas (data processing)
- openpyxl (Excel support)

**Installation takes ~1-2 minutes**

## 🎯 Running the Application

### Option A: Double-click the Batch File (Easiest)

1. Find `start_webapp.bat` in the project folder
2. Double-click it
3. A command window opens showing the server status
4. Open your browser to: **http://localhost:5000**

### Option B: Command Line

```bash
python app.py
```

Then open: **http://localhost:5000**

## 📤 Using the Application

### 1️⃣ Upload Your File

**Drag & Drop Method:**
- Drag your CSV/Excel file onto the upload zone
- File info appears automatically

**Browse Method:**
- Click "Browse Files"
- Select your defect file
- Click "Open"

**Supported Files:**
- `.csv` - Comma-separated values
- `.xlsx` - Excel 2007+
- `.xls` - Excel 97-2003

**File Size:** Maximum 16MB

### 2️⃣ Start Analysis

Click the green **"🚀 Start Analysis"** button

**What Happens:**
1. **Upload** (5 seconds) - File uploads to server
2. **Analyze** (10-30 seconds) - System analyzes defects
3. **Generate Reports** (5 seconds) - Creates summary reports
4. **Complete** - Results displayed!

### 3️⃣ View Results

**Summary Cards:**
- Total Defects
- High Severity Count
- Open Defects
- RCA Needed

**Charts:**
- Severity Distribution (bar chart)
- Status Distribution (pie chart)

**RCA Candidates:**
- List of defects requiring root cause analysis
- Sorted by severity

### 4️⃣ Download Reports

Click buttons to download:
- **📄 Summary Report** - Markdown format (.md)
- **📊 JSON Data** - Machine-readable format (.json)

### 5️⃣ Analyze Another File

Click **"🔄 Analyze Another File"** to start over

## 📁 Sample File Format

Your defect file should have these columns:

### Minimum Required:
```
Id, Summary, Status, Severity
```

### Example CSV:
```csv
Id,Summary,Status,Severity
DEF-001,Login button not working,Open,High
DEF-002,Typo in error message,Closed,Low
DEF-003,Database connection timeout,Open,Critical
```

### Example Excel:
| Id | Summary | Status | Severity |
|----|---------|--------|----------|
| DEF-001 | Login button not working | Open | High |
| DEF-002 | Typo in error message | Closed | Low |
| DEF-003 | Database connection timeout | Open | Critical |

## 🎨 Features at a Glance

✨ **Drag & Drop Upload** - No clicking needed!
📊 **Live Charts** - Interactive visualizations
🎯 **Auto RCA Detection** - Identifies defects needing analysis
📱 **Mobile Friendly** - Works on any device
💾 **Session Tracking** - Multiple analyses supported
🚀 **Fast Processing** - Results in seconds

## ❓ Common Questions

### Q: What if my file has different column names?

**A:** The system is flexible! It recognizes variations like:
- Status: `Status`, `State`, `status`
- Severity: `Severity`, `Priority`, `severity`
- ID: `Id`, `ID`, `Defect_ID`, `DefectID`

### Q: Can I analyze multiple files?

**A:** Yes! Each analysis gets a unique session ID. Click "Analyze Another File" when done.

### Q: Where are my reports saved?

**A:** In the `output/` folder with unique session IDs:
- `RCA_Summary_[session-id]_[date].md`
- `analysis_[session-id]_[date].json`

### Q: How do I stop the server?

**A:** Press `Ctrl+C` in the command window, or close the window.

### Q: Can I use this on a network?

**A:** Yes! Change `localhost` to your computer's IP address. Others on your network can access it.

## 🐛 Troubleshooting

### Problem: "Port 5000 already in use"

**Solution:**
```bash
# Windows: Kill the process
netstat -ano | findstr :5000
taskkill /PID [process_id] /F
```

### Problem: "Module not found"

**Solution:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Problem: "File upload failed"

**Check:**
- File is CSV or Excel format
- File size under 16MB
- File has required columns
- File is not corrupted

### Problem: "Analysis error"

**Check:**
- Column names match expected format
- No completely empty columns
- Data is properly formatted
- Try converting to Excel format

## 🎓 Tips for Best Results

1. **Clean Your Data**
   - Remove empty rows
   - Ensure consistent severity values
   - Use standard date formats

2. **Column Names**
   - Use standard names (Id, Summary, Status, Severity)
   - Or use variations the system recognizes

3. **File Format**
   - Excel (.xlsx) works best
   - CSV should be UTF-8 encoded

4. **Performance**
   - Files under 1000 rows: ~10 seconds
   - Files 1000-5000 rows: ~30 seconds
   - Files over 5000 rows: ~1 minute

## 📞 Need Help?

1. Check this guide
2. Review the main README.md
3. Check the troubleshooting section
4. Verify your file format

## 🎉 You're Ready!

1. Run `start_webapp.bat`
2. Open http://localhost:5000
3. Upload your file
4. Get instant RCA analysis!

**Happy Analyzing! 🚀**

---

*For detailed documentation, see README.md*