# IT Help Desk & Support System

A Model Context Protocol (MCP) server that provides IT help desk functionality with AI-powered issue resolution and expert assignment.

## Features

- **Issue Management**: Add, track, and process IT issues
- **AI-Powered Solutions**: Automatic issue classification and solution suggestions
- **Expert Assignment**: Smart assignment of issues to available technical experts
- **Fast Agent Integration**: Seamless integration with Fast Agent for interactive management
- **Turkish Language Support**: Full support for Turkish issue descriptions

## MCP Tools

1. **`add_issue`** - Add new IT issues to the system
2. **`ai_try_solve`** - Attempt AI-powered solution for issues
3. **`assign_expert`** - Assign issues to appropriate technical experts
4. **`process_issues`** - Process and manage all open issues

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- [Fast Agent](https://github.com/evalstate/fast-agent)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/minasenel/mcp-it-helpdesk.git
cd mcp-it-helpdesk
```

2. Install dependencies:
```bash
uv sync
```

3. Run with Fast Agent:
```bash
uv run fast-agent go --stdio "uv run python main.py"
```

### Usage

Once Fast Agent is running, you can:

- View available tools: `/tools`
- Add an issue: `/call main-add_issue {"employee_id":"E001","description":"VPN bağlantı sorunu","category":"network","subcategory":"vpn","priority":"medium"}`
- Try AI solution: `/call main-ai_try_solve {"description":"VPN bağlantı sorunu","category":"network","subcategory":"vpn","priority":"medium"}`
- Process all issues: `/call main-process_issues`

## Data Files

- **`problems.txt`**: Stores IT issues in pipe-separated format
- **`tech_experts.json`**: Contains technical expert information and availability

## Architecture

```
Fast Agent (Interactive Interface)
    ↓ (MCP Protocol)
IT Help Desk MCP Server (main.py)
    ↓ (File Operations)
problems.txt & tech_experts.json
```

## Development

The system is designed to be:
- **Modular**: Easy to extend with new tools and features
- **Local-first**: No external dependencies or authentication required
- **Fast Agent Ready**: Optimized for Fast Agent integration

## License

MIT License - feel free to use and modify for your needs!

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
