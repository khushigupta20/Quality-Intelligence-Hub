# Quality Intelligence Hub — Integration Plan

## Top-Level Overview

**Goal:** Create a new unified web application in `ALM_Quality_Hub/` (sibling to `ALM_RCA_WebApp/` and `ICA_BOB/`) that integrates all functionality from both existing apps into a single cohesive product.

**App Name:** Quality Intelligence Hub
**New Folder:** `ALM_Quality_Hub/`

**Approach:**
- Single Flask Python backend serving all routes (both RCA and Requirements analysis)
- Single-page vanilla HTML/CSS/JS frontend with persistent left sidebar navigation
- IBM Carbon Design System visual identity (IBM Blue `#0f62fe`, IBM Plex Sans font)
- ICA Agent called directly from Flask backend using the Python `requests` library
- Settings page persists ICA credentials to a local `config.json` file at project root
- All existing RCA Python logic (analyzer.py, report_generator.py) ported as-is
- watsonx / LLM 5-Whys integration **removed** — static 5-Whys templates used always
- `llm_five_whys.py` is **NOT ported** — `_generate_five_whys()` in analyzer.py always uses its built-in static templates
- PDF-only report export (Markdown and standalone HTML reports dropped)
- All 5 Requirements task types preserved, renamed/styled to feel unified

**Non-Goals:**
- Do NOT modify any files inside `ALM_RCA_WebApp/` or `ICA_BOB/`
- Do NOT use Node.js, React, or any non-IBM-approved framework
- Do NOT add a database — use filesystem (uploads/, output/, config.json)
- Do NOT add authentication
- Do NOT include watsonx, ibm-watsonx-ai, or any LLM integration

**Stack:**
- Backend: Python 3.8+, Flask 3.0.0, pandas>=2.2.0, openpyxl==3.1.2, python-dateutil==2.8.2, Werkzeug==3.0.1, reportlab==4.2.5, requests>=2.31.0
- Frontend: Vanilla HTML5, CSS3 (IBM Carbon variables), Vanilla JavaScript ES6+, Chart.js 4.4.0 (CDN)

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffold & Directory Structure

**Intent:**
Create the complete folder and file skeleton for `ALM_Quality_Hub/` so every subsequent sub-task has a clear, pre-agreed home for each file. No logic is written in this step — only empty placeholder files, the requirements list, env example, launcher script, and README stub.

**Expected Outcomes:**
- `ALM_Quality_Hub/` folder exists with all sub-folders in place
- All Python and static source files exist as empty placeholders ready to be filled
- `requirements.txt` is written with the exact correct package list
- `.env.example` documents only the PORT variable (watsonx removed)
- `start_app.bat` Windows launcher is written
- `README.md` stub exists (full content written in Sub-Task 7)

**Todo List:**
1. Create folder `ALM_Quality_Hub/`
2. Create `ALM_Quality_Hub/app/`
3. Create `ALM_Quality_Hub/app/utils/`
4. Create `ALM_Quality_Hub/app/templates/`
5. Create `ALM_Quality_Hub/app/static/css/`
6. Create `ALM_Quality_Hub/app/static/js/`
7. Create `ALM_Quality_Hub/app/static/uploads/` with a `.gitkeep` file
8. Create `ALM_Quality_Hub/output/` with a `.gitkeep` file
9. Create `ALM_Quality_Hub/data/` with a `.gitkeep` file
10. Create empty placeholder files:
    - `app.py`
    - `app/__init__.py`
    - `app/utils/__init__.py`
    - `app/utils/analyzer.py`
    - `app/utils/report_generator.py`
    - `app/utils/ica_agent.py` (new)
    - `app/utils/settings.py` (new)
    - `app/static/css/style.css`
    - `app/static/js/app.js`
    - `app/templates/index.html`
11. Write `requirements.txt`:
    ```
    Flask==3.0.0
    pandas>=2.2.0
    openpyxl==3.1.2
    python-dateutil==2.8.2
    Werkzeug==3.0.1
    reportlab==4.2.5
    requests>=2.31.0
    ```
12. Write `.env.example`:
    ```
    # Optional: override the default port (default: 5000)
    PORT=5000
    ```
13. Write `start_app.bat` Windows launcher that runs `python app.py` with a startup message
14. Write `README.md` stub (title + placeholder — full content added in Sub-Task 7)

**Relevant Context:**
- Mirror the structure of `ALM_RCA_WebApp/` but with `ica_agent.py` and `settings.py` instead of `llm_five_whys.py`
- `requests` is a new dependency not present in either existing app — needed for ICA Agent HTTP calls
- No watsonx packages, no dotenv package (no .env needed since watsonx removed and ICA credentials go in config.json)
- `config.json` is auto-created at runtime by `settings.py` when user saves settings — not a scaffold file

**Status:** [ ] pending

---

### Sub-Task 2 — Port Python Utility Modules

**Intent:**
Copy and adapt the two existing Python utility modules from `ALM_RCA_WebApp/app/utils/` into `ALM_Quality_Hub/app/utils/`, making only the minimal changes needed. Write two brand-new utility modules: `ica_agent.py` (ICA HTTP caller) and `settings.py` (config.json manager).

**Expected Outcomes:**
- `analyzer.py` is a complete working copy with one targeted change: the `_generate_five_whys()` method has its LLM path removed so it always uses static templates directly, and the `try/import llm_five_whys` block is deleted
- `report_generator.py` is a working copy with `generate_summary_report()` and `generate_html_report()` methods removed — only `load_data()`, `_find_column()`, and `generate_pdf_report()` are kept
- `ica_agent.py` is a new fully working module that calls the ICA agent endpoint
- `settings.py` is a new fully working module that reads/writes `config.json`
- `app/__init__.py` and `app/utils/__init__.py` are simple package markers (comment only)

**Todo List:**
1. Write `app/utils/analyzer.py` — full copy from `ALM_RCA_WebApp/app/utils/analyzer.py` with this one change: in `_generate_five_whys()`, remove the entire LLM path block (the `if defect_summaries:` try/import block at lines 323–333) so the method goes directly to `return five_whys_templates.get(category, five_whys_templates['general'])`. The `defect_summaries` parameter can remain in the signature for compatibility but is simply unused.
2. Write `app/utils/report_generator.py` — copy from `ALM_RCA_WebApp/app/utils/report_generator.py` keeping only:
   - The class definition and `__init__`
   - `load_data()` method (unchanged)
   - `_find_column()` method (unchanged)
   - `generate_pdf_report()` method and all its internal helpers (unchanged)
   - Remove `generate_summary_report()` and `generate_html_report()` entirely
3. Write `app/utils/settings.py` as a new module:
   - `CONFIG_PATH` constant = `os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')` (resolves to project root)
   - `get_settings() -> dict`: reads `config.json` if it exists, returns `{"ica_endpoint": "", "ica_api_key": ""}` as defaults if file is missing or invalid
   - `save_settings(data: dict) -> None`: writes `{"ica_endpoint": ..., "ica_api_key": ...}` to `config.json` using `json.dump` with indent=2
4. Write `app/utils/ica_agent.py` as a new module:
   - Import `requests`, `time`, `logging`
   - Define `ICA_TIMEOUT = 120` (seconds per attempt)
   - Define `RETRYABLE_STATUSES = {502, 503, 504}`
   - Define `TASK_PROMPTS` dict with all 5 task keys and their system prompts (exact copy from `ICA_BOB/req-analyzer-app/backend/server.js` lines 63–87):
     - `translate`: requirements translator prompt
     - `analyze`: software requirements analyst prompt
     - `review_tests`: test case reviewer prompt
     - `edge_cases`: QA expert edge cases prompt
     - `validate`: requirements validation expert prompt
   - Define `call_ica_agent(task_type: str, user_input: str, endpoint: str, api_key: str) -> dict` function:
     - Validates task_type exists in TASK_PROMPTS, returns `{"error": "Unknown task type"}` if not
     - Builds `full_prompt = TASK_PROMPTS[task_type] + "\n\n---\n\nUser Input:\n" + user_input`
     - Makes POST request to endpoint with body `{"message": full_prompt}` and header `Authorization: Bearer {api_key}`
     - Up to 2 attempts; retries after 3s on RETRYABLE_STATUSES or requests.Timeout
     - On success: parses JSON response, extracts reply using fallback chain:
       1. Last message with `role == "assistant"` in `data["messages"]`
       2. `data["output"]["text"]`
       3. `data["message"]`
       4. `data["response"]`
       5. `data["result"]`
       6. `data["content"]`
       7. `str(data)` as last resort
     - Returns `{"reply": agent_reply_string}` on success
     - Returns `{"error": user_friendly_message}` on failure (timeout → friendly timeout message, 503 → unavailable message, other → generic error with status code)
5. Write `app/__init__.py` with comment `# Quality Intelligence Hub package`
6. Write `app/utils/__init__.py` with comment `# Utility modules`

**Relevant Context:**
- Source for analyzer.py: `ALM_RCA_WebApp/app/utils/analyzer.py` — the ONLY change is removing lines 323–333 (the `if defect_summaries: try: from app.utils.llm_five_whys import...` block)
- Source for report_generator.py: `ALM_RCA_WebApp/app/utils/report_generator.py` — keep `generate_pdf_report()` (lines 751 onward) and its helpers; remove `generate_summary_report()` (lines 52–200) and `generate_html_report()` (lines 205–746)
- Source for TASK_PROMPTS: `ICA_BOB/req-analyzer-app/backend/server.js` lines 63–87
- Source for ICA retry/timeout logic: `ICA_BOB/req-analyzer-app/backend/server.js` `callICA()` function lines 19–60 — port the same logic to Python using `requests` with `timeout=ICA_TIMEOUT`
- ICA response parsing fallback chain: same order as `ICA_BOB/req-analyzer-app/backend/server.js` lines 123–134
- `CONFIG_PATH` must be an absolute path resolved at module load time using `os.path` to avoid working-directory issues

**Status:** [ ] pending

---

### Sub-Task 3 — Flask Backend (app.py)

**Intent:**
Write the unified Flask application entry point that serves both tools from a single server. It combines all necessary RCA routes from `ALM_RCA_WebApp/app.py` with new routes for Requirements analysis and Settings management. Removed routes from the original app are not included.

**Expected Outcomes:**
- Flask app starts cleanly on port 5000 with `python app.py`
- All RCA routes work: upload, analyze, generate PDF, download
- `POST /api/requirements` accepts task type + user input, reads settings, calls ICA, returns reply
- `GET /api/settings` returns current settings (API key masked)
- `POST /api/settings` saves new settings to config.json
- `GET /` serves the unified index.html
- `GET /health` returns `{"status": "ok"}`
- Startup banner printed to console

**Todo List:**
1. Import Flask, render_template, request, jsonify, send_file, os, json, uuid, datetime, time; import secure_filename from werkzeug.utils
2. Import `DefectAnalyzer` from `app.utils.analyzer`
3. Import `RCAReportGenerator` from `app.utils.report_generator`
4. Import `call_ica_agent` from `app.utils.ica_agent`
5. Import `get_settings`, `save_settings` from `app.utils.settings`
6. Configure Flask app: `template_folder='app/templates'`, `static_folder='app/static'`, `secret_key=os.urandom(24)`
7. Set config: `UPLOAD_FOLDER = 'app/static/uploads'`, `OUTPUT_FOLDER = 'output'`, `MAX_CONTENT_LENGTH = 16 * 1024 * 1024`, `ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}`
8. Create `uploads/` and `output/` directories on startup with `os.makedirs(..., exist_ok=True)`
9. Write `allowed_file(filename)` helper
10. Write `GET /` route → `render_template('index.html', cache_bust=str(int(time.time())))`
11. Write `POST /upload` route — exact copy from `ALM_RCA_WebApp/app.py` lines 49–83 (file validation, UUID session_id, timestamped unique filename, save to UPLOAD_FOLDER, return JSON)
12. Write `POST /analyze` route — exact copy from `ALM_RCA_WebApp/app.py` lines 85–127 (load DefectAnalyzer, run_analysis, save JSON to OUTPUT_FOLDER, return results)
13. Write `POST /generate-pdf-report` route — exact copy from `ALM_RCA_WebApp/app.py` lines 169–198 (load RCAReportGenerator, generate_pdf_report, return pdf filename)
14. Write `GET /download/<filename>` route — exact copy from `ALM_RCA_WebApp/app.py` lines 200–212
15. Write `POST /api/requirements` route:
    - Read `task_type` and `user_input` from `request.json`
    - Validate both are present, return 400 if missing
    - Load settings via `get_settings()`
    - If `ica_endpoint` or `ica_api_key` is empty/missing, return 400 with error: `"ICA Agent is not configured. Please go to Settings and enter your ICA endpoint and API key."`
    - Call `call_ica_agent(task_type, user_input, endpoint, api_key)`
    - If result contains `"error"` key, return 502 with that error
    - If result contains `"reply"` key, return 200 with `{"reply": result["reply"]}`
16. Write `GET /api/settings` route:
    - Call `get_settings()`
    - Return `{"ica_endpoint": settings["ica_endpoint"], "ica_api_key_set": bool(settings["ica_api_key"])}`
    - Never return the actual API key value to the browser
17. Write `POST /api/settings` route:
    - Read `ica_endpoint` and `ica_api_key` from `request.json`
    - Both are optional strings — allow saving empty strings (user may want to clear settings)
    - Call `save_settings({"ica_endpoint": ica_endpoint, "ica_api_key": ica_api_key})`
    - Return `{"success": True, "message": "Settings saved successfully"}`
18. Write `GET /health` route → return `{"status": "ok", "app": "Quality Intelligence Hub"}`
19. Write `if __name__ == '__main__':` block with startup banner printing app name, URL, and instructions; call `app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))`

**Relevant Context:**
- Source for RCA routes: `ALM_RCA_WebApp/app.py` — copy routes `/upload`, `/analyze`, `/generate-pdf-report`, `/download/<filename>` verbatim
- The original `/generate-report` route (MD + JSON) is NOT included — PDF only
- The original `/results/<session_id>` and `/api/sessions` routes are NOT included
- The `session` Flask object is NOT needed (removed with those routes) — no flask session imports needed
- `GET /api/settings` returns `ica_api_key_set: bool` not the actual key — JS uses this to show "API key is configured ✓" or "Not set"
- `POST /api/settings`: if user submits a new key, save it; if user submits empty string, save empty (clear it) — no validation of key format

**Status:** [ ] pending

---

### Sub-Task 4 — Unified HTML Template

**Intent:**
Write the single `index.html` Jinja2 template that renders the entire integrated application. It defines the two-column layout (sidebar + content), all navigation links, and all section DOM structures. No inline styles — all styling comes from `style.css`. No inline JS logic — all behaviour comes from `app.js`.

**Expected Outcomes:**
- Page loads with IBM Plex Sans font, correct `<title>Quality Intelligence Hub</title>`
- Two-column layout: fixed left sidebar + scrollable main content area
- Sidebar has branded header, 7 navigation items grouped into 3 sections
- Home section: welcome heading, app subtitle, two feature explanation cards (one for Defect RCA, one for Requirements Analyzer), plus a quick-start steps card
- Defect RCA section: upload card, progress card (hidden), results card with 3 tabs (hidden)
- Five Requirements sections (one per task): description banner, input field(s) with upload button, submit button, response area, history list
- Settings section: ICA endpoint input, API key input with show/hide toggle, save button, status message
- Chart.js CDN loaded before app.js
- app.js loaded with cache-bust query param

**Todo List:**
1. Write `<!DOCTYPE html>`, `<html lang="en">`, `<head>` with:
   - `<meta charset="UTF-8">`, `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
   - `<title>Quality Intelligence Hub</title>`
   - Google Fonts link for IBM Plex Sans (weights 400, 500, 600)
   - CSS link: `{{ url_for('static', filename='css/style.css') }}?v={{ cache_bust }}`
2. Write `<body>` with outer `<div class="layout">` containing `<nav class="sidebar">` and `<main class="main-content">`
3. Write sidebar `<nav class="sidebar">`:
   - Header div with app name "Quality Intelligence Hub" and tagline "Powered by IBM"
   - Nav group "DEFECT RCA" with item: "📤 Upload & Analyze" → `data-section="rca"`
   - Nav group "REQUIREMENTS ANALYSIS" with 5 items:
     - "🌐 Translate" → `data-section="req-translate"`
     - "🔍 Analyze" → `data-section="req-analyze"`
     - "⚠️ Edge Cases" → `data-section="req-edge-cases"`
     - "🧪 Review Tests" → `data-section="req-review-tests"`
     - "✅ Validate" → `data-section="req-validate"`
   - Nav group "SYSTEM" with item: "⚙️ Settings" → `data-section="settings"`
   - Home link at very top of nav (before groups): "🏠 Home" → `data-section="home"`
4. Write `<main class="main-content">` containing all sections as `<section class="page-section" id="section-{name}">`:
5. Write `#section-home`:
   - Page header: h1 "Quality Intelligence Hub", subtitle paragraph
   - Two feature cards side by side: 
     - Card 1 "🔬 Defect Root Cause Analysis" — describes what the RCA tool does (upload CSV/Excel defect files, get automated analysis, severity/module charts, RCA candidates grouped by pattern, 5-Whys analysis, PDF report download)
     - Card 2 "📋 Requirements Analyzer" — describes what the Requirements tool does (paste or upload requirements text, 5 AI-powered tasks via IBM ICA Agent, get structured analysis, translate/analyze/edge cases/review/validate)
   - Quick-start card: numbered steps "1. Configure ICA → 2. Upload defect file or paste requirements → 3. Run analysis → 4. Download report"
6. Write `#section-rca`:
   - Section heading "Defect Root Cause Analysis"
   - Upload card (`id="rca-upload-card"`): drag-drop zone, file input (accept .csv,.xlsx,.xls), browse button, file info box (hidden), "Start Analysis" button (hidden)
   - Progress card (`id="rca-progress-card"`, hidden): progress bar, progress text, 4 step indicators (Upload, Analyze, Generate Report, Complete)
   - Results card (`id="rca-results-card"`, hidden):
     - 3 tab buttons: Overview, RCA Candidates, Preventive Measures
     - Tab panel `#rca-tab-overview`: 4 stat cards (Total, High Severity, Open, RCA Needed), severity chart canvas, status chart canvas, module chart canvas, "Download PDF Report" button, "Analyze Another File" button
     - Tab panel `#rca-tab-candidates` (hidden): RCA reason callout box, candidates list container
     - Tab panel `#rca-tab-preventive` (hidden): preventive measures list container, download + reset buttons
   - Error card (`id="rca-error-card"`, hidden): error message, "Try Again" button
7. Write the 5 Requirements sections. For each, use this pattern:
   - Section heading with task label (e.g., "🌐 Translate Requirements")
   - Task description banner div
   - For single-field tasks (translate, analyze, edge_cases): one `input-field-block` div with label row (label + "↑ Upload File" button + hidden file input), hint paragraph, textarea
   - For two-field tasks (review_tests, validate): two `input-field-block` divs with same structure
   - "Clear" button per field (initially hidden, shown by JS when field has content)
   - Submit button: "Run [Task Label]"
   - Response area: loading indicator (hidden), error box (hidden), response box with header + copy button (hidden)
   - History list container (empty until populated by JS)
   - All interactive elements have unique IDs using pattern `req-{taskId}-{fieldId}` and `req-{taskId}-response` etc.
8. Write `#section-settings`:
   - Section heading "⚙️ Settings"
   - Description paragraph explaining this configures the IBM ICA Agent connection
   - Form card:
     - ICA Endpoint URL field: label, input `type="text"` `id="settings-endpoint"`, hint text
     - ICA API Key field: label, input `type="password"` `id="settings-api-key"`, show/hide toggle button, hint text, status indicator span `id="settings-key-status"` (shows "API key is configured ✓" or "Not configured" based on GET /api/settings response)
     - Save button `id="settings-save-btn"`
     - Status message div `id="settings-status"` (hidden until save attempt)
9. Load scripts at bottom of `<body>`:
   - `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>`
   - `<script src="{{ url_for('static', filename='js/app.js') }}?v={{ cache_bust }}"></script>`

**Relevant Context:**
- Source for RCA section structure: `ALM_RCA_WebApp/app/templates/index.html` (upload zone, progress steps, 3-tab results with charts)
- Source for Requirements section structure: `ICA_BOB/req-analyzer-app/frontend/src/App.js` + `InputPanel.js` + `ResponsePanel.js` + `HistoryPanel.js` — port DOM structure, no React
- Task IDs: `translate`, `analyze`, `edge_cases`, `review_tests`, `validate`
- Task labels for display: "Translate Requirements", "Analyze Requirements", "Identify Edge Cases", "Review Test Scenarios", "Validate Consistency"
- Two-field tasks: `review_tests` field ids are `requirements` + `test_cases`; `validate` field ids are `requirements` + `test_cases`
- File upload accepts: `.txt,.md,.csv,.json,.xml,.yaml,.yml,.text` (same as InputPanel.js)
- All sections have `class="page-section"` and are hidden by default except home — JS shows/hides them
- The sidebar nav items must have `data-section` attributes matching the section IDs (without the `section-` prefix)

**Status:** [ ] pending

---

### Sub-Task 5 — IBM Carbon CSS Stylesheet

**Intent:**
Write the complete `style.css` for the unified application using IBM Carbon Design System color values and IBM Plex Sans typography. This stylesheet covers the two-column layout, sidebar, all RCA components, all Requirements components, the Settings form, and responsive behavior.

**Expected Outcomes:**
- IBM Carbon color tokens applied consistently throughout
- Two-column grid layout: 240px fixed sidebar + fluid content area
- Sidebar navigation has branded header, section dividers, hover/active states with Carbon blue accent
- Home page feature cards display side-by-side in a clean grid
- All RCA components are styled: drop zone, progress bar, step indicators, stat cards, chart boxes, tabs, candidate items, preventive measures cards
- All Requirements components are styled: description banner, textarea fields with upload button, response box, loading spinner with elapsed timer, error box, history items with badges
- Settings form is clean with proper input styling and status feedback
- Responsive: layout adapts cleanly at 768px breakpoint
- Smooth section transitions and loading animations

**Todo List:**
1. Define CSS custom properties in `:root` using IBM Carbon tokens:
   - `--cds-blue-60: #0f62fe` (primary accent)
   - `--cds-blue-70: #0043ce` (hover)
   - `--cds-blue-10: #edf5ff` (light blue bg)
   - `--cds-red-60: #da1e28` (danger)
   - `--cds-green-50: #198038` (success)
   - `--cds-yellow-20: #fdd13a` (warning bg)
   - `--cds-yellow-70: #684e08` (warning text)
   - `--cds-gray-100: #161616` (primary text)
   - `--cds-gray-70: #525252` (secondary text)
   - `--cds-gray-20: #e0e0e0` (border)
   - `--cds-gray-10: #f4f4f4` (background)
   - `--cds-white: #ffffff` (surface)
   - `--sidebar-width: 240px`
   - `--sidebar-bg: #161616` (dark sidebar)
   - `--sidebar-text: #f4f4f4`
   - `--sidebar-active-bg: #0f62fe`
   - `--radius: 8px`
   - `--shadow: 0 2px 8px rgba(0,0,0,0.08)`
   - `--shadow-lg: 0 4px 16px rgba(0,0,0,0.12)`
2. Write global reset: `*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }`
3. Write `body` styles: `font-family: 'IBM Plex Sans', -apple-system, sans-serif`, `background: var(--cds-gray-10)`, `color: var(--cds-gray-100)`, `font-size: 15px`, `line-height: 1.6`
4. Write `.layout` styles: `display: grid`, `grid-template-columns: var(--sidebar-width) 1fr`, `min-height: 100vh`
5. Write `.sidebar` styles: `background: var(--sidebar-bg)`, `color: var(--sidebar-text)`, `position: sticky`, `top: 0`, `height: 100vh`, `overflow-y: auto`, `display: flex`, `flex-direction: column`
6. Write sidebar header `.sidebar-header`: dark blue background `#0043ce`, app name `font-size: 1rem font-weight: 600`, tagline smaller muted text
7. Write sidebar nav section labels `.nav-group-label`: uppercase, tiny font, muted color, padding, letter-spacing
8. Write sidebar nav items `.nav-item`: full width, padding, cursor pointer, hover state (lighter bg), active state (`.nav-item.active`: `background: var(--sidebar-active-bg)`, left border `3px solid white`)
9. Write `.main-content` styles: `padding: 2rem`, `overflow-y: auto`, `max-width: 1100px`
10. Write `.page-section` styles: `display: none` by default; `.page-section.active { display: block; animation: fadeIn 0.2s ease; }`
11. Write Home section styles:
    - `.home-hero`: large heading, subtitle, margin
    - `.feature-cards`: CSS grid `repeat(2, 1fr)`, gap
    - `.feature-card`: white surface, border, border-radius, padding, hover lift effect
    - `.feature-card h3`: IBM blue, icon + text
    - `.quickstart-card`: full-width card with numbered step list
12. Write shared card styles: `.card { background: var(--cds-white); border: 1px solid var(--cds-gray-20); border-radius: var(--radius); padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: var(--shadow); }`
13. Write RCA-specific styles ported from `ALM_RCA_WebApp/app/static/css/style.css`:
    - `.drop-zone`: dashed border, centered content, hover state with blue border
    - `.file-info-box`: flex row, file icon, file name + size
    - `.progress-bar` + `.progress-fill`: gradient fill
    - `.progress-steps`: 4-column grid, `.step` with active/completed states
    - `.results-summary`: 4-column stat cards grid
    - `.stat-card`: IBM blue gradient, white text, large number
    - `.tabs` + `.tab`: tab buttons, `.tab.active` blue underline
    - `.tab-content`: hidden by default, `.tab-content.active` displayed
    - `.candidate-item`: white card, left border warning color, severity badge
    - `.severity-high` / `.severity-medium` badge colors
    - `.measure-category`: white card, left border success color
    - `.five-whys-section`: light bg, inner border
14. Write Requirements-specific styles ported from `ICA_BOB/req-analyzer-app/frontend/src/index.css`:
    - `.task-description`: blue-10 bg, left border blue, border-radius, padding
    - `.input-field-block`: margin-bottom
    - `.field-header`: flex space-between, label styles
    - `.field-hint`: italic, muted, small
    - `.upload-btn`: light blue bg, blue border, small font, hover to solid blue
    - `.field-clear-btn`: text-only underline button, red on hover
    - `textarea`: full width, min-height 140px, blue border on focus
    - `.response-box`: white, border, pre-wrap, box-shadow
    - `.loading-indicator`: flex with spinner
    - `.spinner`: 18px rotating border animation
    - `.loading-elapsed`: blue, small font
    - `.error-box`: light red bg, red border, red text
    - `.copy-btn`: small border button, hover to blue
    - `.history-section`: top border divider, heading
    - `.history-item`: white card, border, padding
    - `.history-badge`: pill shape, blue bg
    - `.history-time`: muted small text
    - `.history-response`: pre-wrap, max-height 200px, scrollable
15. Write Settings-specific styles:
    - `.settings-form`: max-width 600px
    - `.form-group`: margin-bottom, label on top
    - `.form-group label`: bold, small, uppercase, muted
    - `input[type=text]`, `input[type=password]`: full width, border, padding, blue focus border
    - `.key-input-row`: flex row with input and show/hide toggle
    - `.key-status`: small green tick or muted "not configured"
    - `.settings-status`: success (green) or error (red) feedback box
16. Write shared button styles:
    - `.btn`: base styles (padding, border-radius, font-weight, cursor, transition)
    - `.btn-primary`: IBM blue bg, white text, hover darker blue
    - `.btn-secondary`: white bg, gray border, muted text, hover red border
    - `.btn-danger`: red bg, white text
    - `.btn-sm`: smaller padding/font
    - `.btn-lg`: full width, larger padding
17. Write `@keyframes fadeIn`: opacity 0→1 + translateY 10px→0
18. Write `@keyframes spin`: rotate 360deg
19. Write responsive `@media (max-width: 768px)`:
    - `.layout`: single column (`grid-template-columns: 1fr`)
    - `.sidebar`: `position: relative`, `height: auto`, horizontal scroll nav
    - `.main-content`: `padding: 1rem`
    - `.feature-cards`: single column
    - `.results-summary`: 2 columns

**Relevant Context:**
- IBM Carbon sidebar convention: dark background (#161616) with active items highlighted in brand blue
- RCA styles source: `ALM_RCA_WebApp/app/static/css/style.css` — port relevant class definitions, update color values to Carbon tokens
- Requirements styles source: `ICA_BOB/req-analyzer-app/frontend/src/index.css` — port relevant class definitions, update color values to Carbon tokens
- The charts container must use `display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr))` so charts wrap on smaller screens
- Sidebar `position: sticky; height: 100vh` keeps it visible while scrolling the main content

**Status:** [ ] pending

---

### Sub-Task 6 — Frontend JavaScript (app.js)

**Intent:**
Write the single unified `app.js` that drives all client-side interactions: sidebar navigation switching, the full RCA upload/analyze/report workflow, all 5 Requirements task workflows, and the Settings form. This file replaces both `ALM_RCA_WebApp/app/static/js/app.js` and the React component logic from `ICA_BOB`.

**Expected Outcomes:**
- Sidebar navigation switches sections smoothly; active item is highlighted
- RCA tool works end-to-end: drag/drop or browse → upload → analyze → display Chart.js charts → display candidates → display preventive measures → download PDF
- All 5 Requirements tasks work: fill fields → submit → loading spinner with elapsed timer → display agent reply → copy button → history entry added
- Requirements file upload: reads text files and appends content to the correct textarea
- Settings: loads current settings on page load (endpoint pre-filled, key status shown); saves on form submit; shows success/error feedback
- All state is module-scoped and does not bleed between RCA and Requirements sections
- No console errors under normal operation

**Todo List:**
1. Define module-level state variables:
   - RCA: `rcaCurrentFile`, `rcaCurrentFilepath`, `rcaSessionId`, `rcaAnalysisResults`, `rcaPdfFilename`
   - Requirements: `reqState = {}` (keyed by taskId: `{fieldValues: {}, reply: '', error: ''}`)
   - Requirements history: `reqHistory = []`
   - Shared: `elapsedTimerInterval = null`
2. Write navigation controller on `DOMContentLoaded`:
   - Select all `.nav-item` elements
   - Add click listener to each: call `showSection(item.dataset.section)`, update `.active` class on nav items
   - Call `showSection('home')` as default on load
   - Call `loadSettings()` on load
3. Write `showSection(sectionId)`:
   - Hide all `.page-section` elements (remove `.active` class)
   - Show `#section-{sectionId}` (add `.active` class)
   - Update nav item active states
4. Port RCA drag/drop and file handling from `ALM_RCA_WebApp/app/static/js/app.js`:
   - `initRCADropZone()`: attach dragenter/dragover/dragleave/drop events to `#rca-drop-zone`
   - `handleRCADrop(e)`: extract file from dataTransfer, call `handleRCAFile(file)`
   - `handleRCAFile(file)`: validate extension (.csv/.xlsx/.xls) and size (≤16MB), set `rcaCurrentFile`, call `displayRCAFileInfo(file)`
   - `displayRCAFileInfo(file)`: show filename + formatted size in `#rca-file-info`, show `#rca-analyze-btn`
   - `clearRCAFile()`: reset `rcaCurrentFile`, hide file info and analyze button
   - `formatFileSize(bytes)`: returns human-readable string (Bytes/KB/MB)
5. Write `startRCAAnalysis()` async function — the main RCA workflow:
   - Show `#rca-progress-card`, hide `#rca-upload-card`
   - Step 1 (25%): call `rcaUploadFile(rcaCurrentFile)` → set `rcaSessionId`, `rcaCurrentFilepath`
   - Step 2 (50%): call `rcaAnalyze(rcaSessionId, rcaCurrentFilepath)` → set `rcaAnalysisResults`
   - Step 3 (75%): call `rcaGeneratePdf(rcaSessionId, rcaCurrentFilepath)` → set `rcaPdfFilename`
   - Step 4 (100%): call `displayRCAResults()`
   - On any error: call `showRCAError(errorMessage)`
6. Write `rcaUploadFile(file)`, `rcaAnalyze(sessionId, filepath)`, `rcaGeneratePdf(sessionId, filepath)` as thin fetch wrappers to `/upload`, `/analyze`, `/generate-pdf-report`
7. Write `updateRCAProgress(pct, text, activeStep)`: update progress bar width, text, step active/completed classes
8. Write `displayRCAResults()`:
   - Hide progress card, show `#rca-results-card`
   - Populate 4 stat cards from `rcaAnalysisResults`
   - Call `createSeverityChart()`, `createStatusChart()`, `createModuleChart()`
   - Call `displayRCACandidates()`, `displayPreventiveMeasures()`
9. Port Chart.js chart builders from `ALM_RCA_WebApp/app/static/js/app.js`:
   - `createSeverityChart()`: bar chart on `#rca-severity-chart` canvas
   - `createStatusChart()`: doughnut chart on `#rca-status-chart` canvas
   - `createModuleChart()`: pie (≤5 modules) or horizontal bar (>5 modules) on `#rca-module-chart` canvas, with "no data" fallback
10. Port `displayRCACandidates()` from `ALM_RCA_WebApp/app/static/js/app.js`: renders grouped + standalone candidate items with severity badges and similar defect IDs
11. Port `displayPreventiveMeasures()` from `ALM_RCA_WebApp/app/static/js/app.js`: renders category cards with 5-Whys blocks, immediate actions, long-term prevention lists
12. Port `getSeverityClass(severity)` and `getPatternName(groupKey)` helper functions
13. Write `rcaDownloadPdf()`: `window.location.href = '/download/' + rcaPdfFilename`
14. Write `switchRCATab(tabName)`: hides all `#rca-tab-*` panels, shows `#rca-tab-{tabName}`, updates tab button active states
15. Write `showRCAError(message)`: hide upload/progress/results cards, show `#rca-error-card` with message
16. Write `resetRCA()`: reset all RCA state variables, hide results/error/progress cards, show upload card, clear file info
17. Write Requirements initialization:
    - `initRequirements()`: for each task in TASKS config, initialize `reqState[taskId]` with empty field values
    - Call this on `DOMContentLoaded`
18. Define `TASKS` config array in JS (mirrors `ICA_BOB/req-analyzer-app/frontend/src/tasks.js`):
    - 5 task objects each with `id`, `label`, `description`, and `fields` array (with `id`, `label`, `placeholder`, `hint`)
    - This config drives dynamic wiring of Requirements sections
19. Write `wireRequirementsSection(task)` — called for each task on init:
    - Wire textarea `oninput` to update `reqState[task.id].fieldValues[field.id]` and toggle clear button visibility
    - Wire file input `onchange` to `handleReqFileUpload(task.id, field.id, file)`
    - Wire clear button `onclick` to clear field value + textarea
    - Wire submit button `onclick` to `submitRequirement(task.id)`
20. Write `handleReqFileUpload(taskId, fieldId, file)`: use FileReader to read as text, append to current field value with double newline separator
21. Write `submitRequirement(taskId)` async function:
    - Validate all fields for task are non-empty; alert if any empty
    - Build `userInput`: concatenate fields as `"### {label}\n{value}"` joined by `"\n\n"`
    - Show loading state: show `.loading-indicator` for this task, hide previous reply/error
    - Start elapsed timer: `startElapsedTimer(taskId)`
    - POST to `/api/requirements` with `{task_type: taskId, user_input: userInput}`
    - Stop elapsed timer on response
    - On success: store reply in `reqState[taskId].reply`, call `displayReqResponse(taskId)`, call `addToReqHistory(taskId, userInput, reply)`
    - On error: store error in `reqState[taskId].error`, call `displayReqError(taskId)`
22. Write `startElapsedTimer(taskId)`: uses `setInterval` to increment counter every 1000ms, updates elapsed display element; shows elapsed text after 5s
23. Write `stopElapsedTimer()`: clears the interval, resets counter
24. Write `displayReqResponse(taskId)`: hide loading/error, show response box with reply text, show copy button
25. Write `displayReqError(taskId)`: hide loading, show error box with error message
26. Write `copyToClipboard(taskId)`: copy `reqState[taskId].reply` to clipboard; show "Copied!" on button for 2s then revert
27. Write `addToReqHistory(taskId, input, reply)`: push `{id: Date.now(), taskId, label: taskLabel, input, reply, timestamp: new Date().toLocaleTimeString()}` to `reqHistory`; call `renderReqHistory(taskId)`
28. Write `renderReqHistory(taskId)`: render all history items for this task (reverse order) into `#req-{taskId}-history` container; each item shows badge with task label, timestamp, truncated input (120 chars), scrollable reply
29. Write Settings functions:
    - `loadSettings()`: GET `/api/settings`, populate `#settings-endpoint` with endpoint value, update `#settings-key-status` span: "✓ API key is configured" (green) if `ica_api_key_set` is true, else "Not configured" (muted)
    - `saveSettings()`: read endpoint + key from inputs, POST to `/api/settings`, show success or error message in `#settings-status`, call `loadSettings()` to refresh key status
    - Wire `#settings-save-btn` click to `saveSettings()` on `DOMContentLoaded`
    - Wire show/hide toggle button for API key field: toggle `input.type` between `password` and `text`, update button text "Show"/"Hide"
30. Write `sleep(ms)` utility: `return new Promise(resolve => setTimeout(resolve, ms))`
31. Call `initRCADropZone()`, `initRequirements()`, navigation wiring, `loadSettings()`, `showSection('home')` all inside single `DOMContentLoaded` listener

**Relevant Context:**
- Source for RCA JS: `ALM_RCA_WebApp/app/static/js/app.js` — port all functions, prefix with `rca` where there may be naming collisions
- Source for Requirements JS logic: port from `ICA_BOB/req-analyzer-app/frontend/src/App.js`, `InputPanel.js`, `ResponsePanel.js`, `HistoryPanel.js` — same behaviour, no React, use DOM manipulation instead
- `TASKS` JS config must match the backend `TASK_PROMPTS` keys exactly: `translate`, `analyze`, `edge_cases`, `review_tests`, `validate`
- Task display labels: "Translate Requirements", "Analyze Requirements", "Identify Edge Cases", "Review Test Scenarios", "Validate Consistency"
- The `downloadReport()` function in the original only needs the PDF case — remove summary/JSON/HTML types
- Chart instances: store in variables so they can be destroyed before recreating on "Analyze Another File" to avoid Chart.js "Canvas already in use" errors
- The `reqState` structure isolates per-task state so switching Requirements sections preserves each task's last response — mirrors `tabState` in ICA_BOB App.js
- Section IDs follow pattern `section-{sectionId}` where sectionId matches `data-section` on nav items

**Status:** [ ] pending

---

### Sub-Task 7 — Integration Testing & Final README

**Intent:**
Verify the integrated application works end-to-end, fix any wiring issues discovered during testing, and write the final README with complete setup and usage documentation.

**Expected Outcomes:**
- `python app.py` starts cleanly with no import or configuration errors
- Home page loads with correct IBM Carbon styling and both feature cards
- RCA tool: full workflow works from upload to PDF download
- Requirements tool: all 5 tasks submit correctly (requires valid ICA credentials in Settings)
- Settings: credentials persist to config.json and survive server restart
- All sidebar navigation items switch sections correctly
- No JavaScript console errors during normal operation
- `README.md` is complete with installation, configuration, and usage instructions

**Todo List:**
1. Install dependencies in `ALM_Quality_Hub/`: `pip install -r requirements.txt`
2. Verify Flask starts: `python app.py` — check no ImportError, no missing module errors
3. Open `http://localhost:5000` — verify home page loads with correct branding and layout
4. Test sidebar navigation: click all 7 nav items, verify correct section shown, active item highlighted
5. Test RCA Upload: drag/drop `ALM_RCA_WebApp/test_login_defects.csv` onto drop zone, verify file info appears and "Start Analysis" button shows
6. Test RCA Analyze: click "Start Analysis", verify progress bar advances through 4 steps, results appear
7. Test RCA Charts: verify severity, status, and module charts render without error
8. Test RCA Candidates tab: verify defect candidates listed with severity badges and grouped pattern info
9. Test RCA Preventive Measures tab: verify measures rendered with 5-Whys blocks using static templates
10. Test RCA PDF download: click "Download PDF Report", verify PDF file downloads and opens correctly
11. Test "Analyze Another File": verify app resets to upload state
12. Test Settings save: enter a test ICA endpoint URL and dummy API key, click Save, verify `config.json` is created in project root with correct content
13. Test Settings persistence: restart Flask server, reload page, verify endpoint field is pre-populated and key status shows "✓ API key is configured"
14. Test Settings show/hide: verify API key field toggles between hidden and visible
15. Test Requirements section (if live ICA credentials available): submit requirements text to "Analyze Requirements", verify response appears
16. Test Requirements file upload: click "↑ Upload File" in a Requirements section, upload a .txt file, verify text appends to textarea
17. Test Requirements copy button: submit a task, click "Copy", verify clipboard contains the response text
18. Test Requirements history: submit 2 different tasks, navigate to each section, verify history shows entries in reverse order
19. Test Requirements error state: with no ICA credentials configured (empty settings), submit a task, verify friendly error message appears (not a Python traceback)
20. Fix any issues found in steps 2–19
21. Write complete `README.md`:
    - Project title and description
    - Prerequisites (Python 3.8+, pip)
    - Installation steps (`pip install -r requirements.txt`)
    - How to start (`python app.py` or `start_app.bat`)
    - Environment variables (PORT only — all optional)
    - First-time configuration (Settings page → enter ICA credentials)
    - How to use Defect RCA tool (step by step)
    - How to use Requirements Analyzer tool (step by step, all 5 tasks explained)
    - File format requirements for RCA (column names)
    - Troubleshooting section
    - Project structure overview

**Relevant Context:**
- Test CSV: `ALM_RCA_WebApp/test_login_defects.csv` (ready to use for RCA testing)
- Larger test CSV: any file in `ALM_RCA_WebApp/app/static/uploads/` (for testing with real data)
- `config.json` location: `ALM_Quality_Hub/config.json` (project root, auto-created on first settings save)
- ICA endpoint format: `https://servicesessentials.ibm.com/agenticapps/a2a/<app-id>/agents/<agent-id>`
- If ICA credentials are not available, Requirements sections can still be tested for UI correctness by verifying the "ICA Agent is not configured" error message appears correctly
- Chart.js "Canvas already in use" error: fixed in Sub-Task 6 by storing and destroying chart instances before recreation

**Status:** [ ] pending

---

## Final Architecture Summary

```
ALM_Quality_Hub/
├── app.py                    ← Single Flask backend (9 routes)
├── requirements.txt          ← Flask, pandas, reportlab, requests, openpyxl, etc.
├── .env.example              ← PORT only (watsonx removed)
├── config.json               ← ICA credentials (auto-created via Settings UI)
├── start_app.bat             ← Windows launcher
├── README.md
├── app/
│   ├── __init__.py
│   ├── templates/
│   │   └── index.html        ← Single unified Jinja2 template (sidebar + all sections)
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     ← IBM Carbon-themed stylesheet
│   │   ├── js/
│   │   │   └── app.js        ← Unified vanilla JS (navigation + RCA + requirements + settings)
│   │   └── uploads/          ← Uploaded defect files
│   └── utils/
│       ├── __init__.py
│       ├── analyzer.py       ← Ported from ALM_RCA_WebApp (LLM path removed, static only)
│       ├── report_generator.py ← Ported from ALM_RCA_WebApp (PDF method only)
│       ├── ica_agent.py      ← NEW: ICA HTTP caller + 5 task prompts
│       └── settings.py       ← NEW: config.json reader/writer
└── output/                   ← Generated PDF reports + analysis JSONs
```

## Route Map (Final)

| Method | Path | Purpose | Origin |
|--------|------|---------|--------|
| GET | `/` | Serve unified index.html | New |
| POST | `/upload` | Upload defect file, return session_id | ALM_RCA_WebApp |
| POST | `/analyze` | Run DefectAnalyzer, return results JSON | ALM_RCA_WebApp |
| POST | `/generate-pdf-report` | Generate PDF report, return filename | ALM_RCA_WebApp |
| GET | `/download/<filename>` | Stream file from output/ | ALM_RCA_WebApp |
| POST | `/api/requirements` | Proxy to ICA Agent via call_ica_agent() | ICA_BOB (ported) |
| GET | `/api/settings` | Return current ICA config (key masked) | New |
| POST | `/api/settings` | Save ICA config to config.json | New |
| GET | `/health` | Health check | New |

## What Was Removed vs Kept

| Feature | Decision | Reason |
|---------|----------|--------|
| watsonx / LLM 5-Whys | ❌ Removed | No credentials available |
| llm_five_whys.py | ❌ Not ported | Unnecessary without watsonx |
| Markdown summary report | ❌ Removed | PDF only per user request |
| HTML standalone report | ❌ Removed | PDF only per user request |
| /api/sessions route | ❌ Removed | Not needed in new UI |
| /results/<session_id> route | ❌ Removed | Not needed in new UI |
| All 5 RCA analysis metrics | ✅ Kept | Core functionality |
| Static 5-Whys templates | ✅ Kept | Works without watsonx |
| PDF report generation | ✅ Kept | Primary export format |
| All 5 ICA task types | ✅ Kept | Core functionality |
| ICA retry + timeout logic | ✅ Ported to Python | Reliability requirement |
| Per-task state isolation | ✅ Kept | Good UX pattern |
| Session history | ✅ Kept | Useful for multi-task sessions |
| File upload to textarea | ✅ Kept | Useful feature |
