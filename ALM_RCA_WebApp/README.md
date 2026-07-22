# ALM RCA Web Application

🚀 **Web-based Root Cause Analysis Tool for ALM Defects**

Upload your defect files and get instant RCA analysis with interactive visualizations!

## ✨ Features

- 📤 **Drag & Drop File Upload** - Easy file upload with drag-and-drop support
- 🔍 **Instant Analysis** - Automated defect analysis with real-time progress tracking
- 📊 **Interactive Dashboards** - Beautiful charts and visualizations
- 📄 **Automated Reports** - Generate comprehensive RCA reports
- 💾 **Session Management** - Track multiple analysis sessions
- 🎯 **RCA Candidates** - Automatically identify defects requiring RCA
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Navigate to the project directory:**
   ```bash
   cd ALM_RCA_WebApp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

### Option 1: Using Python directly

```bash
python app.py
```

### Option 2: Using the startup script (Windows)

```bash
start_webapp.bat
```

The application will start on **http://localhost:5000**

## 📖 How to Use

### Step 1: Upload Your Defect File

1. Open your browser and go to `http://localhost:5000`
2. Drag and drop your defect file (CSV or Excel) onto the upload zone
   - Or click "Browse Files" to select a file
3. Supported formats: `.csv`, `.xlsx`, `.xls`
4. Maximum file size: 16MB

### Step 2: Start Analysis

1. Click the "🚀 Start Analysis" button
2. Watch the real-time progress as the system:
   - Uploads your file
   - Analyzes defects
   - Generates reports
   - Prepares visualizations

### Step 3: View Results

The results page shows:

- **Summary Statistics**
  - Total defects
  - High severity count
  - Open defects
  - Defects requiring RCA

- **Interactive Charts**
  - Severity distribution (bar chart)
  - Status distribution (doughnut chart)

- **RCA Candidates**
  - List of defects requiring root cause analysis
  - Defect ID, summary, and severity

### Step 4: Download Reports

- **📄 Summary Report** - Executive summary in Markdown format
- **📊 JSON Data** - Complete analysis data for further processing

### Step 5: Analyze Another File

Click "🔄 Analyze Another File" to start a new analysis

## 📁 File Format Requirements

Your defect file should contain these columns (flexible naming):

### Required Columns:
- **Defect ID**: `Id`, `ID`, `Defect_ID`, `DefectID`
- **Summary**: `Summary`, `Title`, `Description`
- **Status**: `Status`, `State`
- **Severity**: `Severity`, `Priority`

### Optional Columns:
- **Module/Component**: `Module`, `Component`, `Area`
- **Root Cause**: `Root_Cause`, `RootCause`
- **Defect Type**: `Defect_Type`, `Type`, `Category`
- **Detected Date**: `Detected_Date`, `Created_Date`, `Date`
- **Detected By**: `Detected_By`, `Reporter`

## 🎨 Features in Detail

### Drag & Drop Upload
- Intuitive drag-and-drop interface
- Visual feedback during drag operations
- File validation (type and size)
- Instant file information display

### Real-time Progress Tracking
- Visual progress bar
- Step-by-step status indicators
- Clear progress messages
- Smooth animations

### Interactive Visualizations
- **Severity Chart**: Bar chart showing defect distribution by severity
- **Status Chart**: Doughnut chart showing open vs closed defects
- Color-coded for easy interpretation
- Responsive and mobile-friendly

### Automated RCA Identification
The system automatically identifies defects requiring RCA based on:
- High/Critical severity levels
- Missing root cause information
- Configurable criteria

### Session Management
- Unique session ID for each analysis
- Multiple analyses can be performed
- Results stored separately
- Easy tracking and retrieval

## 📂 Project Structure

```
ALM_RCA_WebApp/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── start_webapp.bat           # Windows startup script
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Application styles
│   │   ├── js/
│   │   │   └── app.js         # Client-side JavaScript
│   │   └── uploads/           # Uploaded files (auto-created)
│   ├── templates/
│   │   └── index.html         # Main page template
│   └── utils/
│       ├── analyzer.py        # Defect analysis logic
│       └── report_generator.py # Report generation
├── output/                     # Generated reports (auto-created)
└── data/                       # Sample data (optional)
```

## 🔧 Configuration

### Change Port

Edit `app.py` (line 227):
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port here
```

### Adjust File Size Limit

Edit `app.py` (line 18):
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

### Customize Analysis Criteria

Edit `app/utils/analyzer.py` to modify:
- Severity thresholds
- RCA candidate criteria
- Column name mappings

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Windows: Find and kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### Module Not Found Error
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### File Upload Fails
- Check file format (CSV or Excel)
- Verify file size (max 16MB)
- Ensure file has required columns
- Try converting to Excel format

### Analysis Errors
- Verify column names match expected format
- Check for empty or corrupted data
- Ensure proper encoding (UTF-8 recommended)

## 🔒 Security Notes

- Files are stored with unique session IDs
- Uploaded files are validated for type and size
- Session data is isolated
- Consider adding authentication for production use

## 🚀 Deployment

### For Production:

1. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set up environment variables:**
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secret-key-here
   ```

3. **Configure reverse proxy (nginx/Apache)**

4. **Enable HTTPS**

5. **Set up proper logging**

## 📊 Sample Data

Use the template from the original ALM_RCA_Analysis project:
```
ALM_RCA_Analysis/templates/ALM_Defects_Template.csv
```

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the original ALM_RCA_Analysis documentation
3. Verify your file format matches requirements

## 📝 License

This tool is built upon the ALM_RCA_Analysis project and inherits its licensing.

## 🎉 Enjoy!

Start analyzing your defects with ease! Upload a file and let the system do the heavy lifting.

---

**Made with ❤️ for better defect analysis**