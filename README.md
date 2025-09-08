<div align="center">

# 🤖 MCP IT Help Desk

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP Protocol](https://img.shields.io/badge/MCP-Server-5C6BC0)](https://github.com/modelcontextprotocol)
[![Fast Agent](https://img.shields.io/badge/Fast%20Agent-Compatible-00BFA5)](https://github.com/evalstate/fast-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI-powered IT support: understands issues (TR/EN), suggests fixes, and routes to the right experts. Experts are stored in Django DB (JSON fallback only if Django is unavailable).

</div>

---

## ✨ Features
- **AI-Powered Classification**: Turkish + English keyword logic; optional Gemini for validation/categorization
- **Auto-Solutions**: Common hardware/software/network fixes for non-critical cases
- **Smart Expert Assignment**: Availability + expertise + load consideration
- **Modern Web UI**: Real-time chat via Flask + Socket.IO + Tailwind
- **MCP Tools**: Add/process issues, AI try-solve, assign experts

## 🧭 Table of Contents
- 🔧 MCP Tools
- 🚀 Quick Start
- 🧱 Architecture
- 🗂️ File Structure
- 📖 Comprehensive Documentation
- ⚙️ Advanced Configuration
- 🧪 Usage Examples
- 🧠 Design Philosophy
- 🤝 Contributing & Support

## 🔧 MCP Tools

| Tool | Purpose | Inputs | Output |
|---|---|---|---|
| `add_issue` | Create a new ticket with normalized fields and timestamps | `employee_id, description, category, subcategory, priority` | `Issue created: ISSnnn` |
| `ai_try_solve` | Attempt auto-resolution for common issues (non-critical) | `description, category, subcategory, priority` | Solution text or suggestion to assign expert |
| `assign_expert` | Classify description and pick best available expert | `description` | `Assigned expert: T00x - Name (category/subcategory)` |
| `process_issues` | Batch normalize + auto-solve + assign/queue | none | Summary: closed_by_ai, assigned/queued, skipped |

### 👩‍💻 Expert Data Format (Django DB)

| Field | Type | Example | Notes |
|---|---|---|---|
| `id` | string (pk) | `T001` | Human-friendly ID |
| `name` | string | `Elif Hanım, Ağ Uzmanı` | Display name |
| `expertise` | JSON/list | `["network","vpn"]` | Tags matched by classifier |
| `contact` | string | `elif@example.com` | Optional |
| `availability` | boolean | `true` | Considered for assignment |
| `current_load` | integer | `0` | Incremented on assignment |

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended)
- Optional: Gemini key in env (`GEMINI_API_KEY` or `GOOGLE_API_KEY`)

### Install dependencies
```bash
uv sync
```

### Set up Django (migrations + import experts)
```bash
cd django_api_service
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python import_experts.py  # imports tech_experts.json into DB
```

### Run services
```bash
# MCP (via Fast Agent)
uv run fast-agent go --stdio "uv run python main.py"

# Django API
uv run python django_api_service/manage.py runserver

# Web UI (Flask)
uv run python web_agent.py
# open http://localhost:5001
```

## 🧱 Architecture

```
Web UI (Flask/Socket.IO)         Django API (REST + ORM)         MCP Server (main.py)
         │                                │                               │
         │  create/assign issues (HTTP)   │                               │
         └──────────────► /api/issues/ ───┼──────────┐                    │
                                          │          │                    │
                                          ▼          │                    │
                                  SQLite (Issues, Experts)                │
                                                     ▲                    │
                                                     └── load experts ◄───┘
```

## 🗂️ File Structure

```
mcp-it-helpdesk/
├─ main.py                     # MCP server with tools
├─ problems.txt                # Legacy issue store (MCP-only)
├─ tech_experts.json           # Legacy experts (fallback only)
├─ web_agent.py                # Flask web chat
├─ templates/index.html        # Web UI
├─ django_api_service/
│  ├─ api/settings.py          # Django settings
│  ├─ manage.py
│  └─ issues/
│     ├─ models.py             # Issue, Expert models
│     ├─ serializers.py        # Validation + Gemini integration
│     ├─ views.py              # REST endpoints and actions
│     └─ migrations/           # Django migrations
└─ docs/images/                # (add your screenshots/diagrams here)
```

## 📖 Comprehensive Documentation

### Detailed Features and Benefits
- **Bilingual understanding (TR/EN)**: Reduces back-and-forth with users
- **AI-assisted validation**: Gemini (optional) checks whether text is an IT ticket and categorizes it
- **Local-first heuristics**: Works entirely offline when no API keys are present
- **Human-in-the-loop**: Assign experts for high/critical cases or when AI can’t resolve

### Installation Guide (Step-by-Step)
1. Install dependencies with `uv sync`
2. Run Django migrations and import experts (see Quick Start)
3. Launch MCP, Django API, and the Web UI
4. Test with the usage examples below

### Practical Usage Examples
Inside Fast Agent:
```
/tools
/call main-add_issue {"employee_id":"E001","description":"VPN bağlantı sorunu","category":"network","subcategory":"vpn","priority":"medium"}
/call main-ai_try_solve {"description":"VPN bağlantı sorunu","category":"network","subcategory":"vpn","priority":"medium"}
/call main-process_issues
```

## ⚙️ Advanced Configuration
- **Gemini model**: Set `GEMINI_MODEL` env (default: `gemini-1.5-flash`)
- **API Keys**: `GEMINI_API_KEY` or `GOOGLE_API_KEY` (the code maps GEMINI to GOOGLE for convenience)
- **CORS**: `settings.py` allows `http://localhost:5001` for the web UI; adjust for production
- **Secrets & DB**: `.gitignore` excludes local DBs and secrets; use `.env` files locally (don’t commit)

## 🧠 Design Philosophy
- **Modular**: MCP tools encapsulate actions; Django provides validation and persistence; Web UI focuses on UX
- **Local-first**: Heuristics and files let you prototype without cloud dependencies
- **Single Source of Truth for Experts**: Experts live in Django DB; JSON kept only as a safety net

## 🧪 Testing Ideas
- Unit test serializers and classification fallbacks
- Integration test Django actions that shell into MCP (`assign_expert`, `ai_solve`)
- E2E test via Web UI: create issue → assign expert → verify DB state

---

Licensed under **MIT**.
