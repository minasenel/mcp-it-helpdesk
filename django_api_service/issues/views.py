import os, sys, subprocess, json, re
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import viewsets, status
from .models import Issue
from .serializers import IssueSerializer

MCP_DIR = os.environ.get("MCP_DIR", "/Users/minasenel/Desktop/mcp_test")
MCP_PY = os.environ.get("MCP_PY", "/Users/minasenel/Desktop/mcp_test/.venv/bin/python")

def run_mcp_python(code: str, timeout: int = 20, max_output: int = 10000) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = MCP_DIR + os.pathsep + env.get("PYTHONPATH", "")
    wrapped = f"import sys; sys.path.insert(0, {MCP_DIR!r}); " + code
    proc = subprocess.run(
        [MCP_PY, "-c", wrapped],
        cwd=MCP_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if len(out) > max_output:
        out = out[:max_output]
    if len(err) > max_output:
        err = err[:max_output]
    return proc.returncode, out, err


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all().order_by("-created_at")
    serializer_class = IssueSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.issue_id = f"ISS{instance.pk:03d}"
        instance.save()

    @action(detail=True, methods=["post"])
    def ai_solve(self, request, pk=None):
        issue = self.get_object()
        code = (
            "from main import ai_try_solve; "
            f"print(ai_try_solve({issue.description!r}, {issue.category!r}, {issue.subcategory!r}, {issue.priority!r}))"
        )
        rc, out, err = run_mcp_python(code)
        if rc != 0:
            return Response({"error": "ai_try_solve failed"}, status=500)

        issue.ai_solution = out
        issue.save()
        return Response({"issue_id": issue.issue_id, "ai_solution": issue.ai_solution})

    @action(detail=True, methods=["post"])
    def assign_expert(self, request, pk=None):
        issue = self.get_object()
        code = "from main import assign_expert; " f"print(assign_expert({issue.description!r}))"
        rc, out, err = run_mcp_python(code)
        if rc != 0:
            return Response({"error": "assign_expert failed"}, status=500)

        issue.status = "assigned"
        m = re.search(r"Assigned expert:\s*(\w+)\s*-", out or "")
        if m:
            issue.assigned_expert_id = m.group(1)
        issue.save()
        return Response({"issue_id": issue.issue_id, "assignment": out})
