from mcp.server.fastmcp import FastMCP
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
import re

# Try to initialize Django for expert DB access. Falls back to JSON if unavailable.
try:
    DJANGO_DIR = os.path.join(os.path.dirname(__file__), "django_api_service")
    if DJANGO_DIR not in sys.path:
        sys.path.insert(0, DJANGO_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    import django  # type: ignore
    django.setup()
    from django.db import transaction  # type: ignore
    from issues.models import Expert as DjangoExpert  # type: ignore
    _DJANGO_READY = True
except Exception:
    _DJANGO_READY = False

# MCP server for IT Help Desk & Support System
mcp = FastMCP("IT Help Desk")

# -----------------------------
# File paths and ensure helpers
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
PROBLEMS_FILE = os.path.join(BASE_DIR, "problems.txt") # C:\Users\minasenel\Desktop\mcp_test\problems.txt
EXPERTS_FILE = os.path.join(BASE_DIR, "tech_experts.json") # legacy JSON (used only as fallback)


def ensure_problems_file() -> None: # This function ensures that the problems.txt file exists
    if not os.path.exists(PROBLEMS_FILE):
        with open(PROBLEMS_FILE, "w") as f:
            f.write("")


def ensure_experts_file() -> None:
    if not os.path.exists(EXPERTS_FILE): # This function ensures that the tech_experts.json file exists
        seed_experts: List[Dict] = [ # This is the seed data for the tech_experts.json file
            {
                "id": "T001",
                "name": "Ayşe Hanım, Teknik Uzman",
                "expertise": ["hardware", "performance"],
                "contact": "ayse@example.com",
                "availability": True, # This is the availability of the expert, could be changed to False İF NOT available
                "current_load": 0,
            },
            {
                "id": "T002",
                "name": "Mehmet Bey, Yazılım Uzmanı",
                "expertise": ["software", "login", "password", "network"],
                "contact": "mehmet@example.com",
                "availability": True,
                "current_load": 0,
            },
            {
                "id": "T003",
                "name": "Elif Hanım, Ağ Uzmanı",
                "expertise": ["network", "wifi", "vpn"],
                "contact": "elif@example.com",
                "availability": True,
                "current_load": 0,
            },
        ]
        with open(EXPERTS_FILE, "w") as f:
            json.dump(seed_experts, f, ensure_ascii=False, indent=2)


def _load_experts_from_json() -> List[Dict]:
    if not os.path.exists(EXPERTS_FILE):
        return []
    try:
        with open(EXPERTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


# -----------------------------
# Loaders, parsers, serializers
# -----------------------------
Issue = Dict[str, Optional[str]]


def parse_issue_line(line: str) -> Issue: # This function parses the issue line and returns a dictionary
    parts = [p.strip() for p in line.strip().split("|")]
    while len(parts) < 6:
        parts.append("")
    base = {
        "issue_id": parts[0] if len(parts) > 0 else "",
        "employee_id": parts[1] if len(parts) > 1 else "",
        "description": parts[2] if len(parts) > 2 else "",
        "category": parts[3] if len(parts) > 3 else "",
        "subcategory": parts[4] if len(parts) > 4 else "",
        "priority": parts[5] if len(parts) > 5 else "",
    }
    base["status"] = parts[6] if len(parts) > 6 else "open"
    base["assigned_expert_id"] = parts[7] if len(parts) > 7 else ""
    base["ai_solution"] = parts[8] if len(parts) > 8 else ""
    base["created_at"] = parts[9] if len(parts) > 9 else ""
    base["updated_at"] = parts[10] if len(parts) > 10 else ""
    return base


def serialize_issue(issue: Issue) -> str: # This function serializes the issue and returns a string
    fields = [
        issue.get("issue_id", ""),
        issue.get("employee_id", ""),
        issue.get("description", ""),
        issue.get("category", ""),
        issue.get("subcategory", ""),
        issue.get("priority", ""),
        issue.get("status", "open"),
        issue.get("assigned_expert_id", ""),
        issue.get("ai_solution", ""), # This is the AI solution for the issue
        issue.get("created_at", ""),
        issue.get("updated_at", ""),
    ]
    return " | ".join(fields)


def load_experts() -> List[Dict]:
    """Prefer Django DB experts; fallback to legacy JSON file if Django isn't ready."""
    if _DJANGO_READY:
        try:
            return [
                {
                    "id": e.id,
                    "name": e.name,
                    "expertise": list(e.expertise or []),
                    "contact": e.contact,
                    "availability": bool(e.availability),
                    "current_load": int(e.current_load or 0),
                }
                for e in DjangoExpert.objects.all()
            ]
        except Exception:
            pass
    return _load_experts_from_json()


def mark_expert_assigned(expert_id: str) -> None:
    """Best-effort bump of current_load when we assign an expert (DB only)."""
    if not _DJANGO_READY:
        return
    try:
        with transaction.atomic():
            exp = DjangoExpert.objects.select_for_update().get(id=expert_id)
            exp.current_load = int(exp.current_load or 0) + 1
            exp.save(update_fields=["current_load"])
    except Exception:
        # Silent no-op if DB not available or expert not found
        pass


def load_issues() -> List[Issue]:
    with open(PROBLEMS_FILE, "r") as f:
        lines = [l for l in (ln.strip() for ln in f.readlines()) if l]
    return [parse_issue_line(l) for l in lines] # This function loads the issues from the problems.txt file and returns a list of issues


def write_issues(issues: List[Issue]) -> None: # This function writes the issues to the problems.txt file
    with open(PROBLEMS_FILE, "w") as f:
        for issue in issues:
            f.write(serialize_issue(issue) + "\n")


def generate_next_issue_id(issues: List[Issue]) -> str: # This function generates the next issue id
    max_num = 0
    for issue in issues:
        iid = issue.get("issue_id") or ""
        m = re.match(r"^ISS(\d+)$", iid)
        if m:
            try:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"ISS{max_num + 1:03d}"


# -----------------------------
# Core functions
# -----------------------------
def add_issue_impl(employee_id: str, description: str, category: str, subcategory: str, priority: str) -> Issue:
    ensure_problems_file()
    issues = load_issues() # This function loads the issues from the problems.txt file and returns a list of issues
    new_id = generate_next_issue_id(issues)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # This is the current date and time
    issue: Issue = {
        "issue_id": new_id,
        "employee_id": employee_id.strip(),
        "description": description.strip(),
        "category": (category or "").strip().lower(),
        "subcategory": (subcategory or "").strip().lower(),
        "priority": (priority or "medium").strip().lower(),
        "status": "open",
        "assigned_expert_id": "",
        "ai_solution": "",
        "created_at": now,
        "updated_at": now,
    }
    issues.append(issue)
    write_issues(issues)
    print(f"[IT-HELPDESK] Added issue {new_id} for employee {employee_id}", file=sys.stderr)
    return issue


def ai_try_solve_impl(issue: Issue) -> Tuple[bool, str]:
    description = (issue.get("description") or "").lower()
    category = (issue.get("category") or "").lower()
    subcategory = (issue.get("subcategory") or "").lower()
    priority = (issue.get("priority") or "medium").lower()

    if priority in {"high", "critical"}:
        return False, "High/critical öncelik: insan uzman incelemesi gerekli."

    if category == "hardware" or any(k in description for k in ["don", "donuyor", "yavaş", "ısın", "lag", "freeze", "slow"]):
        solution = (
            "Yeniden başlatın, arka plan uygulamalarını kapatın, disk doluluğunu ve güncellemeleri kontrol edin. "
            "Sorun sürerse donanım tanılama çalıştırın."
        )
        return True, solution

    if category == "software" or subcategory in {"login", "password"} or any(k in description for k in ["şifre", "parola", "giriş", "login", "password"]):
        solution = (
            "Parolayı sıfırlayın veya tek seferlik kodla giriş yapın. Tarayıcı önbelleğini temizleyin ve VPN/proxy ayarlarını kontrol edin."
        )
        return True, solution

    if category == "network" or any(k in description for k in ["wifi", "ağ", "vpn", "bağlanm", "internet"]):
        solution = (
            "Modemi/router'ı yeniden başlatın, kabloları kontrol edin, farklı bir ağ deneyin ve VPN ayarlarını doğrulayın."
        )
        return True, solution

    return False, "İnsan uzman ataması gerekiyor."


def ai_classify_issue(description: str) -> Tuple[str, str]:
    """
    Classify free-text description into standardized (category, subcategory)
    that align with our experts' expertise labels.
    """
    text = (description or "").lower()

    # Network
    if any(k in text for k in ["wifi", "wi-fi", "ağ", "internet", "vpn", "bağlanm", "dns", "proxy", "lan", "wan"]):
        if "vpn" in text:
            return "network", "vpn"
        if any(k in text for k in ["wifi", "wi-fi", "kablosuz"]):
            return "network", "wifi"
        return "network", "connectivity"

    # Software
    if any(k in text for k in ["şifre", "parola", "login", "giriş", "oturum", "uygulama", "program", "kurulum", "installation", "update"]):
        if any(k in text for k in ["şifre", "parola", "password", "reset"]):
            return "software", "password"
        if any(k in text for k in ["login", "giriş", "oturum"]):
            return "software", "login"
        return "software", "application"

    # Hardware / Performance
    if any(k in text for k in ["don", "donuyor", "yavaş", "ısın", "fan", "gürültü", "disk", "ssd", "ram", "ekran", "klavye", "mouse", "keyboard", "freeze", "slow", "lag"]):
        if any(k in text for k in ["don", "donuyor", "yavaş", "freeze", "slow", "lag"]):
            return "hardware", "performance"
        return "hardware", "device"

    # Default fallback
    return "software", "general"


def choose_expert(category: str, subcategory: str, experts: List[Dict]) -> Optional[Dict]:
    category = (category or "").lower()
    subcategory = (subcategory or "").lower()
    candidates = [e for e in experts if e.get("availability")]
    if not candidates:
        return None
    def is_match(exp: Dict) -> bool:
        expertise = [str(x).lower() for x in (exp.get("expertise") or [])]
        return (category in expertise) or (subcategory in expertise)
    matched = [e for e in candidates if is_match(e)] or candidates
    return sorted(matched, key=lambda e: int(e.get("current_load", 0)))[0]


def process_issues_impl() -> Dict[str, int]:
    ensure_problems_file()
    issues = load_issues()
    counts = {"closed_by_ai": 0, "assigned": 0, "skipped": 0}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for issue in issues:
        status = (issue.get("status") or "open").lower()
        if status not in {"", "open", "reopen", "reopened"}:
            counts["skipped"] += 1
            continue
        # Normalize classification based on description to fit standard experts
        cat, sub = ai_classify_issue(issue.get("description", ""))
        issue["category"] = cat
        issue["subcategory"] = sub
        resolved, solution = ai_try_solve_impl(issue)
        if resolved:
            issue["status"] = "closed"
            issue["ai_solution"] = solution
            issue["updated_at"] = now
            counts["closed_by_ai"] += 1
        else:
            expert = choose_expert(issue.get("category", ""), issue.get("subcategory", ""), EXPERTS_CACHE)
            if expert:
                issue["status"] = "assigned"
                issue["assigned_expert_id"] = expert.get("id", "")
                mark_expert_assigned(issue["assigned_expert_id"])  # best-effort bump
            else:
                issue["status"] = "queued"
            issue["updated_at"] = now
            counts["assigned"] += 1

    write_issues(issues)
    print(f"[IT-HELPDESK] Processed issues summary: {counts}", file=sys.stderr)
    return counts


# -----------------------------
# MCP Tools (exposed names)
# -----------------------------
@mcp.tool()
def add_issue(employee_id: str, description: str, category: str, subcategory: str, priority: str) -> str:  
        issue = add_issue_impl(employee_id, description, category, subcategory, priority)
        return f"Issue created: {issue.get('issue_id')}"

# this tool is used to trying to solve the issue with ai first
@mcp.tool()
def ai_try_solve(description: str, category: str, subcategory: str, priority: str) -> str: 
    """
    This tool is used to try to solve the issue with AI first
    @param description: The description of the issue
    @param category: The category of the issue
    @param subcategory: The subcategory of the issue
    @param priority: The priority of the issue
    @return: The solution for the issue if it is solved, otherwise "Çözüm önerisi bulunamadı: uzman ataması önerilir."
    """
    tmp_issue: Issue = {
        "issue_id": "",
        "employee_id": "",
        "description": description,
        "category": category,
        "subcategory": subcategory,
        "priority": priority,
        "status": "open",
        "assigned_expert_id": "",
        "ai_solution": "",
        "created_at": "",
        "updated_at": "",
    }
    resolved, solution = ai_try_solve_impl(tmp_issue)
    return solution if resolved else "Çözüm önerisi bulunamadı: uzman ataması önerilir."


@mcp.tool()
def assign_expert(description: str) -> str:
    """
    Analyze the problem description, classify into standard categories,
    and choose the most suitable available expert.
    """
    category, subcategory = ai_classify_issue(description)
    expert = choose_expert(category, subcategory, EXPERTS_CACHE)
    if not expert:
        return "Uygun uzman bulunamadı"
    return f"Assigned expert: {expert.get('id')} - {expert.get('name')} ({category}/{subcategory})"


@mcp.tool()
def process_issues() -> str:
    """
    This tool is used to process the issues
    @return: The summary of the issues
    """
    counts = process_issues_impl()
    return f"Closed by AI: {counts['closed_by_ai']}, Assigned/Queued: {counts['assigned']}, Skipped: {counts['skipped']}"


# -----------------------------
# Startup initialization
# -----------------------------
ensure_problems_file()
EXPERTS_CACHE: List[Dict] = load_experts()
try:
    num_issues = len(load_issues())
except Exception:
    num_issues = 0
print(f"[IT-HELPDESK] Server starting. Issues: {num_issues}, Experts: {len(EXPERTS_CACHE)}", file=sys.stderr)


if __name__ == "__main__":
    # STDIO mode for Fast Agent
    mcp.run()


