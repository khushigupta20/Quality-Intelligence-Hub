# Quality Intelligence Hub

> **A unified AI-powered web application that helps software quality teams find the root cause of bugs and analyze software requirements — all in one place, powered by IBM AI.**

---

## Table of Contents

1. [What Is This App?](#1-what-is-this-app)
2. [How Does It Work? — Plain English](#2-how-does-it-work--plain-english)
3. [Architecture Overview](#3-architecture-overview)
4. [Prerequisites](#4-prerequisites)
5. [Installation](#5-installation)
6. [Running the App](#6-running-the-app)
7. [First-Time Setup](#7-first-time-setup)
8. [Using the App — Step by Step](#8-using-the-app--step-by-step)
   - [Feature 1: Defect Root Cause Analysis (RCA)](#feature-1-defect-root-cause-analysis-rca)
   - [Feature 2: Requirements Analyzer](#feature-2-requirements-analyzer)
   - [Feature 3: Settings](#feature-3-settings)
   - [Feature 4: User Management (Admin Only)](#feature-4-user-management-admin-only)
9. [Supported File Formats](#9-supported-file-formats)
10. [Project Structure](#10-project-structure)
11. [API Reference](#11-api-reference)
12. [Configuration Reference](#12-configuration-reference)
13. [Troubleshooting](#13-troubleshooting)
14. [Source Applications](#14-source-applications)

---

## 1. What Is This App?

**Quality Intelligence Hub** is a browser-based tool for software quality teams. It solves two common problems that every development team faces:

| Problem | How this app helps |
|---|---|
| *"We have hundreds of bug reports — where do we even start?"* | Upload your bug list as a spreadsheet. The app automatically groups similar bugs, ranks them by severity, finds patterns, and generates a professional PDF report explaining what went wrong and how to prevent it. |
| *"We have software requirements written in messy language — are they good enough?"* | Paste your requirements text into the app. IBM AI will analyze them for gaps, ambiguities, missing edge cases, and test coverage issues. |

You do **not** need to be a data scientist or AI expert to use it. You just need Python installed on your computer.

---

## 2. How Does It Work? — Plain English

The app runs a small local web server on your computer. You open it in any browser, just like a website — but everything stays on your machine (except when calling out to IBM cloud services).

```
Your Browser
     │
     │  http://localhost:5000
     ▼
Quality Intelligence Hub  (Flask Web Server)
     │
     ├──► Defect RCA Engine  ──────────────────► IBM watsonx.ai  (cloud)
     │    (reads your bug file,                  AI engine for RCA:
     │     groups defects, runs                  • smarter bug grouping
     │     5-Whys, builds PDF)                   • AI-written 5-Whys
     │                                           • preventive measures
     │                                           • AI executive summary
     │                                           Falls back to built-in
     │                                           static rules if not
     │                                           configured.
     │
     └──► Requirements Analyzer ──────────────► IBM ICA Agent  (cloud)
          (receives your text,                   AI engine for
           sends it to IBM ICA,                  requirements:
           returns AI analysis)                  • translate
                                                 • analyze
                                                 • edge cases
                                                 • review tests
                                                 • validate
                                                 Requires ICA
                                                 credentials to work.
```

### The two main features

**Feature 1 — Defect Root Cause Analysis (RCA)**

You export your bug list from a tool like HP ALM, JIRA, or any spreadsheet and upload the file (`.csv`, `.xlsx`, or `.xls`). The app:

1. Reads every bug entry automatically
2. Groups similar bugs together (e.g., all "login timeout" bugs in one cluster)
3. Identifies which bugs need investigation first (high severity, no known root cause)
4. Runs a **5-Whys analysis** — asking "why did this happen?" five times to drill down to the real cause
5. Suggests immediate fixes and long-term prevention actions
6. Generates a polished **PDF report** you can share with your team or management

The RCA engine uses **IBM watsonx.ai** as its AI layer. When watsonx credentials are configured, it uses the Granite LLM to write context-aware 5-Whys from your actual bug descriptions, clusters bugs by semantic meaning, and generates an AI executive summary in the PDF. If credentials are not configured, the engine falls back automatically to keyword-based grouping and pre-written 5-Whys templates — the tool still gives you useful results, just without the AI layer.

**Feature 2 — Requirements Analyzer**

You paste in software requirements (written descriptions of what a system should do) and choose what kind of analysis you want. The Requirements Analyzer is powered exclusively by the **IBM ICA Agent** (a cloud AI service). You must configure ICA credentials in Settings before using this feature.

| Task | What it does |
|---|---|
| **Translate** | Converts requirements written in any language into clear professional English |
| **Analyze** | Checks for vague language, missing information, or contradictions |
| **Edge Cases** | Identifies rare scenarios or boundary conditions that the requirements don't cover |
| **Review Tests** | Compares your test cases against requirements to find gaps or redundancies |
| **Validate** | Cross-checks that every requirement has test coverage and vice versa |

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER'S BROWSER                                │
│                                                                         │
│   Left Sidebar               Main Content Area                          │
│  ┌────────────────┐  ┌───────────────────────────────────────────────┐  │
│  │ 🏠 Home        │  │  Active section shown here:                   │  │
│  │                │  │                                               │  │
│  │ DEFECT RCA     │  │  • Drag-and-drop file upload zone             │  │
│  │ 📤 Upload &    │  │  • Real-time progress bar (4 steps)           │  │
│  │    Analyze     │  │  • Interactive charts (Chart.js)              │  │
│  │                │  │  • RCA results in 3 tabs                      │  │
│  │ REQUIREMENTS   │  │  • Requirements text input                    │  │
│  │ 🌐 Translate   │  │  • AI response display with copy button       │  │
│  │ 🔍 Analyze     │  │  • Session history per task                   │  │
│  │ ⚠️  Edge Cases │  │                                               │  │
│  │ 🧪 Review Tests│  └───────────────────────────────────────────────┘  │
│  │ ✅ Validate    │                                                      │
│  │                │                                                      │
│  │ SYSTEM         │                                                      │
│  │ ⚙️  Settings   │                                                      │
│  └────────────────┘                                                      │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │  HTTP  (localhost:5000)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  FLASK WEB SERVER  (app.py)  •  Python 3.8+             │
│                                                                         │
│  /login             GET/POST  Authentication — login page               │
│  /logout            POST      Clear session                             │
│  /                  GET       Serve the single-page app                 │
│  /upload            POST      Save uploaded defect file                 │
│  /analyze           POST      Run defect analysis engine                │
│  /generate-pdf      POST      Build PDF report                          │
│  /download/…        GET       Stream report to browser                  │
│  /api/requirements  POST      Proxy text to IBM ICA Agent               │
│  /api/settings      GET/POST  Read / write credentials in config.json   │
│  /api/users         GET/POST  List / create users  (admin only)         │
│  /api/users/…       DELETE    Remove a user        (admin only)         │
│  /api/users/…/password POST   Reset a user password                     │
│  /health            GET       Health check                              │
└──────────────┬──────────────────────────┬───────────────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────────────────────┐
│  LOCAL ANALYSIS ENGINE   │   │  IBM CLOUD SERVICES (internet required)  │
│                          │   │                                          │
│  analyzer.py             │   │  IBM watsonx.ai  ◄── Defect RCA only    │
│  • Load CSV / Excel      │   │  ┌──────────────────────────────────┐   │
│  • Auto-detect columns   │   │  │ Model: granite-3-8b-instruct     │   │
│  • Group similar defects │   │  │ • AI-written 5-Whys per cluster  │   │
│  • Score by severity     │   │  │ • Per-defect root cause hints    │   │
│  • 5-Whys analysis       │   │  │ • AI preventive measures         │   │
│  • Generate statistics   │   │  │ • AI executive summary in PDF    │   │
│                          │   │  │ Embeddings: slate-125m-rtrvr     │   │
│  report_generator.py     │   │  │ • Semantic defect clustering      │   │
│  • Build PDF (ReportLab) │   │  │                                  │   │
│  • Charts + tables       │   │  │ ⚠ Falls back to static keyword   │   │
│  • Executive summary     │   │  │   grouping + pre-written         │   │
│                          │   │  │   templates if no credentials    │   │
│  watsonx_agent.py        │   │  └──────────────────────────────────┘   │
│  • Calls watsonx SDK     │   │                                          │
│  • Graceful fallback     │   │  IBM ICA Agent  ◄── Requirements only   │
│                          │   │  ┌──────────────────────────────────┐   │
│  ica_agent.py            │   │  │ • Translate requirements         │   │
│  • HTTP POST to ICA      │   │  │ • Analyze for gaps               │   │
│  • Retry / timeout logic │   │  │ • Find edge cases                │   │
│                          │   │  │ • Review test scenarios          │   │
│  auth.py                 │   │  │ • Validate consistency           │   │
│  • Login / session       │   │  │                                  │   │
│  • Roles: admin / user   │   │  │ ✖ Returns error if ICA           │   │
│  • pbkdf2 password hash  │   │  │   credentials not configured     │   │
│                          │   │  │   (no fallback available)        │   │
│  settings.py             │   │  └──────────────────────────────────┘   │
│  • Read / write          │   └──────────────────────────────────────────┘
│    config.json           │
└──────────────────────────┘   ┌──────────────────────────────────────────┐
                               │  LOCAL FILE SYSTEM                       │
                               │  config.json      ← credentials + users  │
                               │  app/static/uploads/  ← uploaded files   │
                               │  output/          ← generated PDFs       │
                               └──────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.8+, Flask 3.0 | Web server, routing, all business logic |
| Data processing | pandas, openpyxl | Read and parse CSV / Excel defect files |
| PDF generation | ReportLab | Build the downloadable RCA report |
| AI — Defect RCA | IBM watsonx.ai SDK | LLM text generation + semantic embeddings; falls back to static rules if not configured |
| AI — Requirements | IBM ICA Agent (HTTP API) | All 5 requirements analysis tasks; requires ICA credentials — no fallback |
| Frontend | Vanilla HTML5 / CSS3 / JS | Single-page application, no framework needed |
| Charts | Chart.js 4.4 (CDN) | Interactive severity, status, and module charts |
| Design system | IBM Carbon Design System | Colors (`#0f62fe`), IBM Plex Sans font, layout tokens |
| Auth | Werkzeug pbkdf2:sha256 | Password hashing, session management |

---

## 4. Prerequisites

You need the following installed on your computer **before** you start:

| Requirement | Minimum version | How to check |
|---|---|---|
| Python | 3.8 | `python --version` |
| pip | latest | `pip --version` |
| Internet access | — | Required only to call IBM watsonx.ai and IBM ICA Agent |

> **No Node.js. No Docker. No database.** The app runs entirely with Python.

---

## 5. Installation

### Step 1 — Get the code

Navigate into the app folder:

```bash
cd ALM_Quality_Hub
```

### Step 2 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | What it does |
|---|---|
| `Flask` | Runs the web server |
| `pandas` | Reads your CSV / Excel defect files |
| `openpyxl` | Handles `.xlsx` Excel files |
| `reportlab` | Generates the PDF report |
| `requests` | Makes HTTP calls to the IBM ICA Agent |
| `Werkzeug` | Handles file uploads and password hashing |
| `python-dateutil` | Parses date columns in defect files |
| `ibm-watsonx-ai` | IBM watsonx.ai SDK for AI-driven RCA analysis |

---

## 6. Running the App

### Option A — Windows (easiest)

Double-click **`start_app.bat`** inside the `ALM_Quality_Hub/` folder.
A terminal window opens and the server starts automatically.

### Option B — Command line (any OS)

```bash
python app.py
```

You should see:

```
============================================================
  Quality Intelligence Hub
============================================================
  Starting server on http://localhost:5000
  Defect RCA + Requirements Analyzer
  Press Ctrl+C to stop
============================================================
```

### Step 3 — Open the app

Open your browser and go to: **http://localhost:5000**

You will land on a **login page**. The default credentials on a fresh installation are:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Administrator |

> **Security note:** Change the admin password immediately after first login via Settings → User Management → Reset Password.

### Running on a different port

```bash
# Linux / macOS
PORT=8080 python app.py

# Windows CMD
set PORT=8080 && python app.py

# Windows PowerShell
$env:PORT=8080; python app.py
```

---

## 7. First-Time Setup

After logging in for the first time, configure your IBM credentials so the AI features work.

### Configure IBM watsonx.ai — for Defect RCA

IBM watsonx.ai is the AI engine behind the Defect RCA feature. Configure it to unlock AI-driven bug grouping, AI-written 5-Whys, and an AI executive summary in the PDF.

> If you skip this, the RCA tool **still works** — it falls back silently to keyword grouping and pre-written category templates. No error is shown; the AI layer is simply not used.

1. Click **⚙️ Settings** in the left sidebar
2. Under **IBM watsonx.ai Settings**, enter:
   - **watsonx API Key** — your IBM Cloud IAM API key
     > Get one at: https://cloud.ibm.com/iam/apikeys → *Create an IBM Cloud API key*
   - **watsonx Project ID** — your watsonx.ai project GUID
     > Get one at: https://dataplatform.cloud.ibm.com/projects/ → open your project → *Manage* tab
   - **watsonx Model ID** — leave blank to use the default (`ibm/granite-3-8b-instruct`)
3. Click **Save Settings**

When both the API Key and Project ID are present, the full AI feature set activates automatically:

| AI feature | What it does |
|---|---|
| Semantic defect clustering | Bugs are grouped by meaning, not just keywords — even if two bugs describe the same problem with different words |
| AI-written 5-Whys | Each defect cluster gets a tailored 5-Whys chain generated by the LLM using your actual bug descriptions |
| AI preventive measures | Immediate actions and long-term prevention steps are written by AI using your defect context |
| Per-defect root cause hints | Each RCA candidate gets a 1–2 sentence AI-suggested root cause |
| AI executive summary | The PDF report opens with an AI-written paragraph summarising the quality situation |

### Configure IBM ICA Agent — for Requirements Analyzer

The Requirements Analyzer sends your text to an IBM ICA (Intelligent Collaborative Agent) running in the cloud. **This feature does not work without ICA credentials — there is no fallback.**

1. Click **⚙️ Settings** in the left sidebar
2. Under **ICA Agent Settings**, enter:
   - **ICA Endpoint URL** — the full URL of your ICA Agent
     > Format: `https://servicesessentials.ibm.com/agenticapps/a2a/<app-id>/agents/<agent-id>`
   - **ICA API Key** — your ICA authentication key
3. Click **Save Settings**

Credentials are stored in `config.json` on your computer and are never sent anywhere except your configured ICA endpoint.

---

## 8. Using the App — Step by Step

### Feature 1: Defect Root Cause Analysis (RCA)

**What you need:** A file containing your bug/defect list exported from HP ALM, JIRA, or any similar tool. Accepted formats: `.csv`, `.xlsx`, `.xls`.

#### Step 1 — Upload your defect file

1. Click **📤 Upload & Analyze** in the left sidebar
2. Either **drag and drop** your file onto the upload zone, or click **Browse Files**
3. The file name and size appear below the upload zone
4. Click **🚀 Start Analysis**

![Defect RCA upload screen — drag-and-drop zone with file browser and Start Analysis button](Defect%20RCA%20input%20screen.png)

#### Step 2 — Wait for the four-step pipeline

A progress bar tracks four steps that run automatically:

| Step | What happens |
|---|---|
| 1. Upload | Your file is saved securely with a unique session ID |
| 2. Analyze | Defects are loaded, columns detected, bugs grouped, severity scored, 5-Whys run |
| 3. Generate Report | A PDF is built with charts, candidate lists, and the executive summary |
| 4. Complete | Results are displayed in the browser |

This typically takes 5–30 seconds. With watsonx.ai enabled, it may take longer while the LLM generates content.

#### Step 3 — Review results across three tabs

**Tab 1 — Overview**

- **4 summary cards**: Total defects · High/Critical severity count · Open defects · Defects needing RCA
- **Severity chart** — bar chart showing how many defects are at each severity level
- **Status chart** — doughnut chart showing open vs. closed breakdown
- **Module chart** — which parts of your system have the most bugs

**Tab 2 — RCA Candidates**

- Ranked list of defects that most need investigation (high/medium severity, no documented root cause)
- Defects are grouped: 5 bugs that all relate to "login timeout" appear as one entry with a count badge
- Each item shows: Defect ID · summary · severity badge · affected module
- **With watsonx.ai configured:** each item also shows an AI-suggested root cause in 1–2 sentences
- **Without watsonx.ai:** items are listed without the root cause hint field

**Tab 3 — Preventive Measures**

- Organised by defect category (e.g., "Authentication Issues", "Database Issues")
- Each category shows a **5-Whys chain**, **immediate actions**, and **long-term prevention steps**
- **With watsonx.ai configured:** all content is generated by AI using your actual bug descriptions
- **Without watsonx.ai:** pre-written templates matched to each defect category are used

![Defect RCA results screen — Overview tab with severity chart, status chart, module chart, and summary cards](Defect%20RCA%20output%20screen.png)

#### Step 4 — Download the PDF report

Click **📄 Download PDF Report**. A fully formatted PDF saves to your computer, ready to share with your manager or team.

#### Step 5 — Analyze another file

Click **🔄 Analyze Another File** to reset the tool and start fresh with a new file.

---

### Feature 2: Requirements Analyzer

**What you need:** Text describing what your software should do (requirements), and/or test cases. IBM ICA credentials must be configured in Settings first — this feature has no offline fallback.

The sidebar has five tasks. Click any one to open it:

#### 🌐 Translate Requirements

*Use this when requirements are written in another language or in unclear informal language.*

1. Paste your requirements text (or click **↑ Upload File** to load from `.txt`, `.md`, `.csv`, etc.)
2. Click **Run Translate**
3. The IBM ICA Agent returns a professionally worded English version

![Translate Requirements screen — text input area with Run Translate button and AI response panel](Translate%20screen.png)

#### 🔍 Analyze Requirements

*Use this to check whether your requirements are clear and complete.*

1. Paste your requirements text
2. Click **Run Analyze**
3. The ICA Agent returns a structured report covering:
   - Clarity and completeness assessment
   - Ambiguous or vague statements with suggestions
   - Missing information
   - Recommendations for improvement

#### ⚠️ Edge Cases

*Use this to find scenarios your requirements might have missed.*

1. Paste your requirements or feature description
2. Click **Run Edge Cases**
3. The ICA Agent returns a list of boundary conditions, negative scenarios, and unusual situations to account for

![Edge Cases screen — requirements input with IBM ICA Agent response listing boundary conditions and negative scenarios](Edge%20Cases%20screen.png)

#### 🧪 Review Tests

*Use this to check whether your test cases actually cover your requirements.*

1. Paste your **requirements** in the first text box
2. Paste your **test cases** in the second text box
3. Click **Run Review Tests**
4. The ICA Agent returns missing test scenarios, redundant tests, edge cases not covered, and inconsistencies

#### ✅ Validate Consistency

*Use this to ensure requirements and test cases do not contradict each other.*

1. Paste your **requirements** in the first text box
2. Paste your **test cases** in the second text box
3. Click **Run Validate**
4. The ICA Agent returns requirements with no test coverage, unmapped test cases, and any conflicts

#### Common controls for all 5 tasks

| Control | What it does |
|---|---|
| **↑ Upload File** | Load text from a file instead of typing. Accepted: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.yaml` |
| **Copy** | Copies the full AI response to your clipboard |
| **Session History** | Previous responses appear below the form, newest first, and persist until you close the tab |
| **Progress timer** | If the ICA Agent takes more than 5 seconds, a running timer appears so you know it hasn't frozen |

---

### Feature 3: Settings

Click **⚙️ Settings** in the sidebar to manage all credentials.

| Setting | Used by | Behaviour if missing |
|---|---|---|
| ICA Endpoint URL | Requirements Analyzer — all 5 tasks | Tasks return a "not configured" error |
| ICA API Key | Requirements Analyzer — all 5 tasks | Tasks return a "not configured" error |
| watsonx API Key | Defect RCA AI engine | RCA silently falls back to static keyword rules |
| watsonx Project ID | Defect RCA AI engine | RCA silently falls back to static keyword rules |
| watsonx Model ID | Defect RCA model (override) | Defaults to `ibm/granite-3-8b-instruct` if blank |

- All API key fields have a **Show / Hide toggle** so you can verify what was entered
- The settings page never exposes the raw key value to the browser — it only shows a ✓ / ✗ presence flag
- Credentials are saved to `config.json` in the `ALM_Quality_Hub/` folder

---

### Feature 4: User Management (Admin Only)

Administrators can manage who can access the application.

1. Click **⚙️ Settings** in the sidebar
2. Scroll to **User Management**

**Create a new user:** Enter username, password (min 6 characters), and role (`admin` or `user`) → click **Create User**

**Delete a user:** Click **Delete** next to any user. You cannot delete your own account.

**Reset a password:** Click **Reset Password** next to a username. Any user can reset their own password; admins can reset anyone's.

---

## 9. Supported File Formats

### For Defect RCA

| Format | Notes |
|---|---|
| `.csv` | Comma, tab, or semicolon delimited. Encodings UTF-16, UTF-8, Latin-1, ISO-8859-1, CP1252 are all auto-detected |
| `.xlsx` | Standard Excel workbook (Excel 2007 and later) |
| `.xls` | Legacy Excel format (Excel 97–2003) |

Maximum file size: **16 MB**

### Expected columns — flexible auto-detection

You do not need to rename your columns. The app tries many common names automatically:

| Data field | Accepted column names |
|---|---|
| Defect ID | `Id`, `ID`, `Defect_ID`, `DefectID` |
| Summary / title | `Summary`, `summary`, `Title`, `Description` |
| Severity | `Severity`, `severity`, `Priority` |
| Status | `Status`, `status`, `State` |
| Module / component | `Module`, `Component`, `module`, `Area` |
| Root cause | `Root_Cause`, `RootCause`, `root_cause` |
| Defect type | `Defect_Type`, `DefectType`, `Type`, `Category` |
| Detected date | `Detected_Date`, `DetectedDate`, `Created_Date`, `Date` |

> The analysis engine always runs as long as there is at least one **Summary** column and one **Severity** or **Status** column. Other columns add richer charts and RCA output.

### For Requirements Analyzer

Any plain text input works. File upload accepts: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.yaml`, `.yml`

---

## 10. Project Structure

```
Combine_RCA_Test Flow/          ← Repository root
│
├── README.md                   ← This file
├── ALM_Quality_Hub/            ← The combined application (run this)
│   ├── app.py                  ← Flask entry point — all 16 routes
│   ├── requirements.txt        ← Python package list
│   ├── start_app.bat           ← Windows one-click launcher
│   ├── .env.example            ← Environment variable reference
│   ├── config.json             ← Credentials + user accounts (auto-created)
│   │
│   ├── app/
│   │   ├── templates/
│   │   │   ├── index.html      ← Main single-page app (IBM Carbon UI)
│   │   │   └── login.html      ← Login page
│   │   ├── static/
│   │   │   ├── css/style.css   ← IBM Carbon Design System stylesheet
│   │   │   ├── js/app.js       ← Vanilla JS (navigation + RCA + requirements + settings)
│   │   │   └── uploads/        ← Temporary storage for uploaded defect files
│   │   └── utils/
│   │       ├── analyzer.py     ← Defect analysis engine (grouping, 5-Whys, statistics)
│   │       ├── report_generator.py  ← PDF report builder (ReportLab)
│   │       ├── watsonx_agent.py     ← IBM watsonx.ai SDK integration (LLM + embeddings)
│   │       ├── ica_agent.py         ← IBM ICA Agent HTTP caller (retry logic, 5 prompts)
│   │       ├── settings.py          ← config.json reader / writer
│   │       └── auth.py              ← Login, session, user store, password hashing
│   │
│   ├── output/                 ← Generated PDF reports and analysis JSONs
│   └── data/                   ← Place sample defect files here for testing
│
├── ALM_RCA_WebApp/             ← Original standalone RCA app (not modified)
└── ICA_BOB/                    ← Original standalone requirements analyzer (not modified)
```

---

## 11. API Reference

These are the HTTP endpoints the Flask server exposes. You interact with them through the browser UI, but they can also be called directly (e.g., for automation or testing).

| Method | Route | Description |
|---|---|---|
| `GET` | `/login` | Show the login page |
| `POST` | `/login` | Submit login credentials |
| `POST` | `/logout` | Log out and clear session |
| `GET` | `/` | Serve the main single-page app (redirects to `/login` if not logged in) |
| `POST` | `/upload` | Upload a defect file → returns `{ session_id, filename, filepath }` |
| `POST` | `/analyze` | Run defect analysis → returns full results JSON |
| `POST` | `/generate-pdf-report` | Generate PDF → returns `{ pdf_report: filename }` |
| `GET` | `/download/<filename>` | Stream a generated report file to the browser |
| `POST` | `/api/requirements` | Send a requirements task to IBM ICA Agent → returns `{ reply }` |
| `GET` | `/api/settings` | Get current settings (API keys are **never** returned — only boolean presence flags) |
| `POST` | `/api/settings` | Save ICA and watsonx credentials to `config.json` |
| `GET` | `/api/users` | List all users and their roles |
| `POST` | `/api/users` | Create a new user (admin only) |
| `DELETE` | `/api/users/<username>` | Delete a user (admin only) |
| `POST` | `/api/users/<username>/password` | Reset a user's password |
| `GET` | `/health` | Health check → `{ status: "ok", app: "Quality Intelligence Hub" }` |

---

## 12. Configuration Reference

### Environment variables (optional)

Copy `.env.example` to `.env` inside `ALM_Quality_Hub/` and set any of these:

```env
# Change the port the server listens on (default: 5000)
PORT=5000

# IBM watsonx.ai credentials for AI-enhanced Defect RCA
# These can also be entered via the Settings UI (stored in config.json)
WATSONX_API_KEY=your-ibm-cloud-iam-key
WATSONX_PROJECT_ID=your-watsonx-project-guid

# Optional model overrides — these have sensible defaults
# WATSONX_MODEL_ID=ibm/granite-3-8b-instruct
# WATSONX_EMBED_MODEL=ibm/slate-125m-english-rtrvr
# WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

> Credentials set via the Settings UI (`config.json`) take precedence over environment variables.

### config.json (auto-managed)

Created automatically the first time you click **Save Settings** in the UI. Do not edit it manually.

```json
{
  "ica_endpoint": "https://servicesessentials.ibm.com/agenticapps/...",
  "ica_api_key": "ak_...",
  "watsonx_api_key": "",
  "watsonx_project_id": "",
  "watsonx_model_id": "ibm/granite-3-8b-instruct",
  "users": {
    "admin": {
      "password_hash": "pbkdf2:sha256:...",
      "role": "admin"
    }
  }
}
```

> **Security:** API keys are stored as plain text in this file. Add `config.json` to `.gitignore` and never commit it to a public repository.

---

## 13. Troubleshooting

### App won't start

| Error message | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'reportlab'` | Run `pip install reportlab==4.2.5` |
| `ModuleNotFoundError: No module named 'ibm_watsonx_ai'` | Run `pip install ibm-watsonx-ai>=1.1.2` |
| Port 5000 already in use | Run on a different port: `PORT=8080 python app.py` |

To find and free port 5000 on Windows:

```powershell
netstat -ano | findstr :5000
taskkill /PID <pid_number> /F
```

### Login issues

| Problem | Fix |
|---|---|
| Forgot the admin password | Delete `config.json` and restart — a fresh `admin` / `admin123` account is created automatically |
| "Invalid username or password" | Usernames are case-insensitive; passwords are case-sensitive |

### File upload issues

| Problem | Fix |
|---|---|
| "Invalid file type" error | Only `.csv`, `.xlsx`, and `.xls` are accepted |
| "File not found" after upload | The `app/static/uploads/` folder is auto-created; check write permissions if missing |
| CSV not parsing correctly | Try exporting from your tool as UTF-8; for HP ALM, export as UTF-16 |
| Excel file won't load | Unmerge any merged cells before exporting |

### Defect RCA issues

| Problem | Fix |
|---|---|
| Charts show "No data" | Your file must have a `Severity` or `Status` column (see Section 9 for accepted names) |
| RCA Candidates list is empty | No high/medium severity defects found, or the severity column name was not recognised |
| 5-Whys look generic, not specific to my bugs | watsonx credentials are not configured — add them in Settings to get AI-written 5-Whys |
| watsonx authentication error | Verify the IBM Cloud IAM key has the `ML Developer` role on the watsonx.ai project |
| PDF not downloading | Check the `output/` folder exists inside `ALM_Quality_Hub/` and is writable |

### Requirements Analyzer issues

| Problem | Fix |
|---|---|
| "ICA Agent is not configured" | Go to ⚙️ Settings and enter your ICA Endpoint URL and ICA API Key |
| "The ICA agent took too long" | Input may be too long — reduce it and retry; timeouts are retried once automatically |
| "ICA agent is temporarily unavailable" | Wait 30 seconds and try again |
| "ICA agent returned an error (status 401)" | Your ICA API key is wrong or expired — check it in Settings |

---

## 14. Source Applications

Quality Intelligence Hub was built by combining two standalone tools that already existed in this repository:

| Original tool | Location | What was integrated |
|---|---|---|
| **ALM RCA WebApp** | `ALM_RCA_WebApp/` | Defect file upload, analysis engine (`analyzer.py`), PDF report generator (`report_generator.py`) |
| **ICA BOB Req Analyzer** | `ICA_BOB/` | IBM ICA Agent HTTP caller, all 5 requirements task prompts, requirements UI sections |

Neither source application was modified. All code for the combined app lives exclusively in `ALM_Quality_Hub/`.

---

## License

Internal IBM tooling — not for external distribution.

---

<div align="center" style="margin-top:2rem;padding-top:1rem;border-top:1px solid #e0e0e0;color:#8d8d8d;font-size:0.75rem;">
  Made with IBM Bob
</div>
