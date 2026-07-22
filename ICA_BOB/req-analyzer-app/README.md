# Requirements Analyzer — ICA Agent Web App

A full-stack web application that uses an IBM ICA agent to translate, analyze, review, and validate software requirements.

## Architecture

```
Browser (React)
    │
    │  POST /api/agent  { taskType, userInput }
    ▼
Express Backend (port 4000)
    │  Routes task type → system prompt
    │  POST with x-api-key
    ▼
ICA Agent Endpoint
```

The **router pattern** is implemented in the backend: each `taskType` maps to a specific system prompt injected before the user's input, directing the ICA agent to behave appropriately for that task.

## Task Types (Routes)

| Route | What it does |
|---|---|
| `translate` | Translates requirements into English |
| `analyze` | Analyzes requirements for quality & completeness |
| `review_tests` | Reviews test cases against requirements |
| `edge_cases` | Identifies edge cases & boundary conditions |
| `validate` | Validates consistency between requirements & tests |

## Setup

### 1. Backend

```bash
cd backend
npm install
```

Create a `.env` file (copy from `.env.example`):
```
ICA_ENDPOINT=https://servicesessentials.ibm.com/agenticapps/a2a/91a9025b-2dca-4849-9443-91b6f0d228b5/agents/888d13a3-78f1-4e4b-b22e-042419acd124
ICA_API_KEY=ak_bFqQhXRCtY3ZRwCWccicORanJT5GY9GOMCMxY-3xpi4
PORT=4000
```

Start the backend:
```bash
npm run dev     # development (auto-restart)
npm start       # production
```

### 2. Frontend

```bash
cd frontend
npm install
npm start       # opens http://localhost:3000
```

> The React dev server proxies `/api/*` requests to `http://localhost:4000` automatically.

## Project Structure

```
req-analyzer-app/
├── backend/
│   ├── server.js          # Express server + router logic
│   ├── package.json
│   └── .env.example
└── frontend/
    ├── public/index.html
    ├── src/
    │   ├── App.js                        # Main app component
    │   ├── tasks.js                      # Task router config
    │   ├── index.js
    │   ├── index.css
    │   └── components/
    │       ├── TaskTabs.js               # Tab navigation
    │       ├── InputPanel.js             # User input area
    │       ├── ResponsePanel.js          # Agent response display
    │       └── HistoryPanel.js           # Session history
    └── package.json
```
