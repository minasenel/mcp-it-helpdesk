import asyncio
import os
import sys
import subprocess

try:
    from mcp_agent.core.fastagent import FastAgent  # type: ignore
except ImportError:
    def _run_cli_via_uvx() -> int:
        cmd = ["uvx", "fast-agent", "go"]
        # Run from project root so config is discovered
        cwd = os.path.dirname(__file__)
        print("[agent] fast-agent Python API not found; launching CLI via uvx...", file=sys.stderr)
        try:
            return subprocess.call(cmd, cwd=cwd)
        except FileNotFoundError:
            print("[agent] uvx not found. Install uv or run: pip install fast-agent-mcp", file=sys.stderr)
            return 1

    if __name__ == "__main__":
        sys.exit(_run_cli_via_uvx())
else:
    # Create the application via Python API
    fast = FastAgent("fast-agent example")

    @fast.agent(instruction="You are a helpful AI Agent")
    async def main():
        async with fast.run() as agent:
            await agent.interactive()

    if __name__ == "__main__":
        asyncio.run(main())
