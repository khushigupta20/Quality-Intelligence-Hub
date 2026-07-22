# Quality Intelligence Hub

> **A unified AI-powered web application for software quality teams — combining Defect Root Cause Analysis and Requirements Intelligence in one place.**

---

## What Is This?

If you work in software testing or quality assurance, you likely deal with two painful tasks every day:

1. **Defect reports pile up** — You export hundreds of bugs from your ALM (Application Lifecycle Management) tool and then spend hours manually reading through them, grouping similar ones, figuring out why they keep happening, and writing a Root Cause Analysis (RCA) report.

2. **Requirements are hard to validate** — You receive software requirements documents and have to manually check whether they are clear, complete, and properly covered by test cases — which is tedious and error-prone.

**Quality Intelligence Hub solves both problems in one application.**

You upload your defect file, click a button, and within seconds you get:
- Automated defect grouping and pattern detection
- A 5-Whys root cause analysis for each defect cluster
- Preventive measures to stop these defects from recurring
- A professional PDF report ready to share with your team

For requirements, you paste your text and the AI instantly analyzes it, translates it, identifies edge cases, reviews your test scenarios, and validates consistency — all powered by IBM's AI platform.

---

## Who Is This For?

- QA Engineers and Test Managers
- Software Quality Analysts
- Project Managers who review defect reports
- Anyone who works with ALM defect exports or software requirements

No programming knowledge is needed to **use** the application. You just need to install it once and then use it through your browser like any other website.

---

## What Can It Do?

### Part 1 — Defect Root Cause Analysis (RCA)

| Feature | What it means in plain English |
|---|---|
| **File Upload** | Upload your defect export from ALM as a CSV or Excel file |
| **Automatic Grouping** | The app finds defects that are similar to each other and groups them |
| **Severity Analysis** | Shows you which defects are Critical, High, Medium — with charts |
| **RCA Candidates** | Automatically identifies which defects need a root cause investigation |
| **5-Whys Analysis** | For each group of similar defects, drills down through 5 "why" questions to find the real root cause |
| **Preventive Measures** | Suggests specific actions to prevent these defects from happening again |
| **PDF Report** | Generates a complete, professional report you can download and share |
| **AI Enhancement** | When connected to IBM watsonx.ai, the analysis uses real AI to make all of the above smarter and more specific to your actual defects |

### Part 2 — Requirements Analyzer

| Task | What it does |
|---|---|
| **Translate** | Requirements written in any language? The AI translates them into clear English |
| **Analyze** | Checks your requirements for clarity, completeness, and anything that is vague or missing |
| **Edge Cases** | Finds all the unusual or boundary situations your requirements may not have considered |
| **Review Tests** | Compares your test cases against your requirements — finds gaps, duplicates, and missed scenarios |
| **Validate** | Cross-checks that every requirement has a test case and every test case maps to a requirement |

---

## Architecture

Here is how all the pieces fit together:

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR BROWSER                             │
│                                                                 │
│   Login Page ──► IBM Carbon UI (Single Page Application)        │
│                  ├── Sidebar Navigation                         │
│                  ├── Defect RCA Section                         │
│                  │     (upload, charts, candidates, PDF)        │
│                  ├── Requirements Sections                      │
│                  │     (translate, analyze, edge cases,         │
│                  │      review tests, validate)                 │
│                  └── Settings & User Management                 │
└────────────────────────────┬────────────────────────────────────┘
                             │  HTTP requests (your local network)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│               FLASK WEB SERVER  (app.py — port 5000)            │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  auth.py    │  │  settings.py │  │     config.json        │ │
│  │  Login /    │  │  Read/write  │  │  Credentials + Users   │ │
│  │  Users /    │  │  credentials │  │  (stored on disk)      │ │
│  │  Roles      │  └──────────────┘  └────────────────────────┘ │
│  └─────────────┘                                                │
│                                                                 │
│  ┌──────────────────────────┐  ┌────────────────────────────┐  │
│  │      analyzer.py         │  │    report_generator.py     │  │
│  │  Loads defect CSV/Excel  │  │  Builds PDF report using   │  │
│  │  Groups similar defects  │  │  ReportLab                 │  │
│  │  Finds RCA candidates    │  │  (AI executive summary     │  │
│  │  Generates 5-Whys        │  │   when watsonx configured) │  │
│  │  Preventive measures     │  └────────────────────────────┘  │
│  └──────────┬───────────────┘                                   │
│             │ (calls when AI is configured)                     │
│             ▼                                                   │
│  ┌──────────────────────────┐  ┌────────────────────────────┐  │
│  │    watsonx_agent.py      │  │      ica_agent.py          │  │
│  │  IBM watsonx.ai SDK      │  │  Calls IBM ICA Agent API   │  │
│  │  • Semantic clustering   │  │  for all 5 requirements    │  │
│  │  • AI 5-Whys             │  │  tasks (translate,         │  │
│  │  • Root cause suggestion │  │  analyze, edge cases,      │  │
│  │  • Executive summary     │  │  review tests, validate)   │  │
│  └──────────┬───────────────┘  └───────────────┬────────────┘  │
└─────────────┼─────────────────────────────────-┼───────────────┘
              │                                   │
              ▼                                   ▼
┌─────────────────────────┐        ┌──────────────────────────────┐
│   IBM watsonx.ai        │        │   IBM ICA Agent Endpoint     │
│                         │        │                              │
│  Model: granite-3-8b    │        │  A2A REST API                │
│  Embed: slate-125m      │        │  (Requirements analysis)     │
│  (Text generation +     │        │                              │
│   Embeddings)           │        │                              │
└─────────────────────────┘        └──────────────────────────────┘
```

### In Simple Terms

1. You open the app in your browser
2. You log in with a username and password
3. Your browser talks to the Flask server running on your machine
4. The Flask server does the heavy lifting — reading your files, running analysis, calling IBM AI services
5. Results come back to your browser and are displayed as charts, tables, and downloadable reports

---

## Project Structure

```
ALM_Quality_Hub/
│
├── app.py                        ← Start here. This is the main application file.
├── requirements.txt              ← List of Python packages to install
├── start_app.bat                 ← Windows users: double-click this to start the app
├── config.json                   ← Stores your credentials and user accounts
├── .env.example                  ← Reference for environment variable names
├── README.md                     ← This file
│
├── app/
│   ├── templates/
│   │   ├── index.html            ← The main web page (everything you see after login)
│   │   └── login.html            ← The login page
│   │
│   ├── static/
│   │   ├── css/style.css         ← IBM Carbon Design System styles
│   │   ├── js/app.js             ← All the browser-side logic (charts, forms, navigation)
│   │   └── uploads/              ← Your uploaded defect files are stored here temporarily
│   │
│   └── utils/
│       ├── analyzer.py           ← Reads defect files and runs all the analysis
│       ├── report_generator.py   ← Creates the PDF report
│       ├── watsonx_agent.py      ← Talks to IBM watsonx.ai for AI features
│       ├── ica_agent.py          ← Talks to IBM ICA Agent for requirements tasks
│       ├── settings.py           ← Reads and saves credentials from config.json
│       └── auth.py               ← Handles login, users, roles, and passwords
│
├── output/                       ← Generated reports and analysis files saved here
└── data/                         ← Optional: place sample defect files here
```

---

## Installation — Step by Step

### What You Need Before Starting

- **Python 3.8 or higher** — [Download here](https://www.python.org/downloads/)
  - During installation, check the box **"Add Python to PATH"**
- **pip** — comes bundled with Python automatically

To check if Python is already installed, open a terminal (Command Prompt on Windows) and type:
```
python --version
```
You should see something like `Python 3.11.0`. If you do, you are ready.

---

### Step 1 — Download the Project

Clone the repository or download and unzip it to a folder on your computer.

```bash
git clone https://github.com/your-username/ALM_Quality_Hub.git
cd ALM_Quality_Hub
```

---

### Step 2 — Install Dependencies

This installs all the Python packages the app needs. Run this once.

```bash
pip install -r requirements.txt
```

This will install: Flask, pandas, openpyxl, ReportLab, Werkzeug, requests, and ibm-watsonx-ai.

---

### Step 3 — Start the Application

**Option A — Windows (easiest):**
Double-click `start_app.bat` in the project folder. A command window will open showing the server is running.

**Option B — Any operating system:**
```bash
python app.py
```

You will see:
```
============================================================
  Quality Intelligence Hub
============================================================
  Starting server on http://localhost:5000
  Defect RCA + Requirements Analyzer
  Press Ctrl+C to stop
============================================================
```

---

### Step 4 — Open in Your Browser

Open your browser and go to:
```
http://localhost:5000
```

You will see the login page.

---

### Step 5 — Log In

Two accounts are created by default:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin (can manage users and settings) |
| `tester` | *(contact your admin)* | User |

> **Important:** Change the default admin password immediately after first login via **Settings → Reset My Password**.

---

## Configuration — Connecting to IBM AI Services

The app works without any AI configuration for basic rule-based defect analysis. To unlock AI-powered features, you need to configure two things.

### Configure IBM ICA Agent (for Requirements Analysis)

1. Log in and click **⚙️ Settings** in the left sidebar
2. Under **IBM ICA Agent**, enter:
   - **ICA Agent Endpoint URL** — the full HTTPS URL of your ICA agent
   - **ICA API Key** — your ICA API key starting with `ak_`
3. Click **Save Settings**

Once saved, all five Requirements Analysis tasks (Translate, Analyze, Edge Cases, Review Tests, Validate) become active.

### Configure IBM watsonx.ai (for AI-Enhanced RCA)

1. In **⚙️ Settings**, under **IBM watsonx.ai**, enter:
   - **watsonx API Key** — your IBM Cloud IAM API key
   - **watsonx Project ID** — your watsonx.ai project GUID
   - **watsonx Model ID** — leave blank to use the default (`ibm/granite-3-8b-instruct`)
2. Click **Save Settings**

Once saved, the following AI features are automatically enabled:
- Defects are grouped by semantic meaning (not just keywords)
- 5-Whys analysis is generated from your actual defect descriptions
- Each RCA candidate gets an AI-suggested root cause
- Preventive measures are tailored to your specific defect patterns
- The PDF report includes an AI-written executive summary paragraph

> **Without watsonx credentials**, all of the above still works using built-in rule-based logic — the app never breaks, it just uses pre-defined templates instead of AI.

---

## How to Use — Step by Step

### Defect Root Cause Analysis

1. Click **📤 Upload & Analyze** in the left sidebar
2. Drag and drop your defect file onto the upload zone (or click **Browse Files**)
   - Supported formats: `.csv`, `.xlsx`, `.xls`
   - Maximum file size: 16 MB
3. Click the green **🚀 Start Analysis** button
4. Watch the progress bar move through four steps: Upload → Analyze → Generate Report → Complete
5. When done, three tabs appear:
   - **Overview** — summary statistics and charts (severity, status, modules)
   - **RCA Candidates** — list of defects requiring root cause analysis, grouped by pattern
   - **Preventive Measures** — specific actions to prevent recurrence, with 5-Whys breakdown
6. Click **📄 Download PDF Report** to save the full report

### Requirements Analysis

1. Click any task in the sidebar under **Requirements Analysis** (Translate, Analyze, Edge Cases, Review Tests, or Validate)
2. Paste your requirements text into the text area — or click **↑ Upload File** to load from a `.txt` or `.md` file
3. For **Review Tests** and **Validate**, you will see two text areas — paste requirements in the first and test cases in the second
4. Click the **Run** button
5. The IBM ICA Agent processes your request (a timer shows elapsed time for longer responses)
6. The response appears below — click **Copy** to copy it to your clipboard
7. Previous responses are saved in **Session History** so you can refer back to them

### Managing Users (Admin only)

1. Go to **⚙️ Settings**
2. Scroll down to **User Management**
3. You can:
   - See all current users and their roles
   - Add a new user with a username, password, and role (User or Admin)
   - Delete any user (except yourself)
   - Reset any user's password

---

## Supported File Formats for Defect Upload

Your defect file should contain these columns (the app recognises common variations automatically):

| Data | Accepted Column Names |
|---|---|
| Defect ID | `Id`, `ID`, `Defect_ID`, `DefectID` |
| Summary | `Summary`, `Title`, `Description` |
| Severity | `Severity`, `Priority` |
| Status | `Status`, `State` |
| Module / Component | `Module`, `Component`, `Area` |
| Root Cause | `Root_Cause`, `RootCause` |
| Date | `Detected_Date`, `Created_Date`, `Date` |

The minimum required columns are **Defect ID**, **Summary**, and **Severity**. Everything else is optional and enhances the analysis when present.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `python: command not found` | Python is not installed or not added to PATH. Re-install Python and check "Add to PATH" |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Port 5000 already in use | Run `set PORT=8080 && python app.py` (Windows) or `PORT=8080 python app.py` (Mac/Linux) |
| Login page shows "Invalid username or password" | Use `admin` / `admin123` on first run |
| "ICA Agent is not configured" error | Go to Settings and enter your ICA endpoint URL and API key |
| PDF not downloading | Check that the `output/` folder exists in the project directory |
| CSV file not parsing correctly | Ensure the file has at least the ID, Summary, and Severity columns. Try exporting from ALM as UTF-8 |
| AI features not working | Ensure both **watsonx API Key** and **watsonx Project ID** are set in Settings |

---

## Default Credentials Reminder

> After cloning and running for the first time, log in as `admin` with password `admin123` and immediately change the password from **Settings → Reset My Password**. Also replace any placeholder credentials in `config.json` with your real ICA and watsonx credentials via the Settings UI.

---

## License

Internal IBM tooling — not for external distribution.
