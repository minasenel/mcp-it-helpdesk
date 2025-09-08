# MCP IT Help Desk – AI-Powered Support with Unified Expert Storage

An AI-enabled help desk built on Model Context Protocol (MCP), Django, and a modern web UI. It classifies issues, suggests fixes, and routes tickets to the right experts—with Turkish and English support.

## What’s included

- **MCP tools** in `main.py` for: issue creation, AI try-solve, expert assignment, bulk processing
- **Django API** for validation, persistence (SQLite by default), and actions
- **Web UI** (Flask + Socket.IO + Tailwind) for a clean chat experience
- **Unified experts store**: Experts now live in Django DB (JSON fallback remains only if Django isn’t available)

## Architecture

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

## Quick start

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Optional: Gemini API key (`GEMINI_API_KEY` or `GOOGLE_API_KEY`) for smarter validation

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
- MCP (via Fast Agent):
```bash
uv run fast-agent go --stdio "uv run python main.py"
```
- Django API:
```bash
uv run python django_api_service/manage.py runserver
```
- Web UI (Flask):
```bash
uv run python web_agent.py
# open http://localhost:5001
```

## MCP tools
1. `add_issue(employee_id, description, category, subcategory, priority)`
2. `ai_try_solve(description, category, subcategory, priority)`
3. `assign_expert(description)`
4. `process_issues()`

Example (inside Fast Agent):
```
/tools
/call main-add_issue {"employee_id":"E001","description":"VPN bağlantı sorunu","category":"network","subcategory":"vpn","priority":"medium"}
/call main-ai_try_solve {"description":"VPN bağlantı sorunu","category":"network","subcategory":"vpn","priority":"medium"}
/call main-process_issues
```

## Data model and storage
- Issues (MCP file path remains for legacy): `problems.txt`
- Experts: now stored in Django DB (`issues_expert` table). `tech_experts.json` is kept as a fallback only.

To ensure Django is the source of truth for experts:
1) Run migrations
2) Run `django_api_service/import_experts.py`
3) Restart MCP and Django to reload the DB-backed experts

## Turkish + English intelligence
- Heuristics and prompts handle bilingual keywords: hardware (“donuyor”, “yavaş”), software/login (“giriş”, “şifre”), network (“ağ”, “vpn”, “wifi”).
- Django serializer optionally uses Gemini for “is this an IT issue?” and “which category?”, with graceful fallback to local rules.

## Adding images to this README
1) Create a folder for assets, e.g. `docs/images/`
2) Put your PNG/JPG/SVG files there
3) Reference them with relative paths in Markdown:
```md
![Web chat](docs/images/web-chat.png)
![Architecture](docs/images/architecture.png)
```
Tips:
- Keep image filenames lowercase and hyphenated.
- Use `.png` or `.svg` for diagrams; prefer `.png` for screenshots.
- On GitHub, you can also drag-and-drop images into an issue or README editor to auto-host, but repo-stored assets are more portable.

## Security and config
- Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `django_api_service/api/.env` (not committed)
- Local DB files (`*.sqlite3`) and secrets (`fastagent.secrets.yaml`) are ignored via `.gitignore`

## Contributing
PRs and issues welcome.

## License
MIT
