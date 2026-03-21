# Agent CLI ToolHub (`ath`)

> CLI tools that AI agents can call directly — no servers, no MCP, no wrappers needed.

If your agent has a terminal, it can use these tools. One command, JSON out, done.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-34%20passed-brightgreen.svg)](#running-tests)

---

## Why This Exists

Every AI agent framework — OpenClaw, Claude Code, Cursor, Codex, Gemini CLI — has one thing in common: **it can run a shell command.** That's the universal interface.

But most "agent tools" out there need you to run HTTP servers, configure MCP endpoints, write framework-specific adapters, or keep background processes alive. That's a lot of moving parts just to let an agent check the weather.

This repo takes a different approach. Every tool is a **CLI subcommand** that:

- Takes flags in, prints JSON out
- Needs no running server or background process
- Works with **any** agent that can execute a shell command
- Ships with [AgentSkills](https://agentskills.io) SKILL.md files so agents can discover tools automatically

```bash
ath weather --city "London"      # → structured JSON to stdout
ath search --query "next.js 15"  # → answer + citations to stdout
ath convert --input data.csv --to json  # → converted data to stdout
```

No daemon. No port. No config file. The agent runs the command, reads stdout, moves on.

---

## Why CLI over MCP / HTTP servers?

**MCP** requires the host to support the protocol, a running server process, and the right transport config. If the host doesn't speak MCP, you're stuck.

**HTTP servers** need a process running before the agent can use the tool. You end up managing ports, health checks, and "is the server up?" failures.

**A CLI** just works. Every agent has a shell. `bash` is the universal connector. This is the same pattern used by [Google Workspace CLI](https://github.com/googleworkspace/cli) (21k stars, 100+ agent skills) and [Context7](https://github.com/upstash/context7) (49k stars, CLI + Skills mode).

You can always layer MCP on top of a CLI later. But the CLI is the foundation that works everywhere first.

---

## Installation

```bash
pip install cli-tools-hub
```

Or install from source:

```bash
git clone https://github.com/andylow92/Agent-cli-ToolHub.git
cd Agent-cli-ToolHub
pip install -e .
```

For optional format support:

```bash
pip install cli-tools-hub[pdf]    # PDF text extraction (PyPDF2)
pip install cli-tools-hub[xlsx]   # Excel spreadsheet support (openpyxl)
pip install cli-tools-hub[all]    # Everything
```

---

## Quick Start

```bash
# Get current weather for any city
ath weather --city "London"

# AI-powered web search with citations
ath search --query "latest Python 3.13 features"

# Convert CSV to JSON
ath convert --input data.csv --to json

# Send a verified message to another agent
ath verify --send --to http://localhost:8004/talk --message "hello"

# Verify a response is authentic
ath verify --check --request-id "abc-123" --response '{"request_id": "abc-123"}'
```

---

## Tools

| Tool | Command | What it does | Env Vars |
|------|---------|--------------|----------|
| Weather | `ath weather` | Current weather for any city via OpenWeatherMap | `OPENWEATHERMAP_API_KEY` |
| Search | `ath search` | AI-powered web search via Perplexity Sonar — returns answers with citations, not just links | `PERPLEXITY_API_KEY` |
| Convert | `ath convert` | Convert between file formats: CSV, JSON, XML, HTML, Markdown, TSV, PDF, XLSX | None |
| Verify | `ath verify` | Inter-agent communication with request_id round-trip verification — prevents hallucinated responses | None |

---

## Output Contract

Every command follows the same contract. Agents can rely on this structure without special parsing per tool.

**Success** → exit code `0`, JSON to stdout:
```json
{
  "status": "ok",
  "data": { ... }
}
```

**Error** → non-zero exit code, JSON to stderr:
```json
{
  "status": "error",
  "error": "OPENWEATHERMAP_API_KEY environment variable is not set",
  "code": "AUTH_MISSING"
}
```

**Exit codes:**

| Code | Meaning | Example |
|------|---------|---------|
| `0` | Success | Command completed normally |
| `1` | API error | Remote service returned an error |
| `2` | Auth error | Missing or invalid API key |
| `3` | Validation error | Bad flags, missing required arguments |
| `4` | File error | File not found, unsupported format |
| `5` | Internal error | Unexpected failure |

---

## Agent Integration

Every tool ships with an [AgentSkills](https://agentskills.io)-compatible `SKILL.md` that teaches agents when and how to use it. The `skills/` directory contains one skill folder per tool.

### OpenClaw

Symlink or copy the skills into your OpenClaw workspace:

```bash
# Symlink (stays in sync with repo updates)
ln -s $(pwd)/skills/ath-* ~/.openclaw/skills/

# Or copy
cp -r skills/ath-* ~/.openclaw/skills/
```

Start a new session (`/new`) and the agent will discover the tools automatically. The skills include OpenClaw-specific metadata for binary gating and API key injection.

### Claude Code

Copy the skill files into your project or global skills directory:

```bash
cp -r skills/ath-* ~/.claude/skills/
```

Or reference them in your `CLAUDE.md`:

```markdown
## Available CLI tools
See skills/ directory for `ath` CLI tools (weather, search, convert, verify).
Run `ath --help` for usage.
```

### Cursor / Windsurf / Other Agents

Any agent that reads SKILL.md files or has terminal access can use these tools. Either point the agent's skill discovery at the `skills/` directory, or just tell the agent:

> You have access to the `ath` CLI. Run `ath --help` to see available tools.

That's usually enough — the agent will figure out the flags from `--help` output.

---

## Environment Variables

```bash
# Required for ath weather
# Get a free key at: https://openweathermap.org/appid
export OPENWEATHERMAP_API_KEY="your_key_here"

# Required for ath search
# Get a key at: https://docs.perplexity.ai/
export PERPLEXITY_API_KEY="your_key_here"
```

Tools that don't need API keys (`convert`, `verify`) work with zero configuration.

---

## What Belongs Here

Tools that any AI agent can call from the command line:

- **Stateless subcommands** — run, return JSON, exit. No background processes.
- **Real utility** — things agents actually need: search, file conversion, data lookup, inter-agent communication.
- **Zero or minimal dependencies** — the core tools use only Python's standard library.
- **SKILL.md included** — every tool ships with agent-discoverable skill files.
- **Tested** — every tool has tests covering help output, validation, error handling, and success cases.

## What This Repo Is Not

- Not a collection of HTTP microservices (see [Agent-Tool-Hub](https://github.com/andylow92/Agent-Tool-Hub-) for that)
- Not an agent framework or orchestrator
- Not a place for tools that need a running server, database, or daemon
- Not a directory of closed-source APIs with no local component

If your tool requires a background process to function, it doesn't belong here. If it can be a stateless CLI command, it does.

---

## Who This Is For

- **Developers building AI agents** who need ready-made tools their agent can call from a terminal
- **People experimenting with tool-calling** in Claude Code, Cursor, OpenClaw, Codex, or any LLM with shell access
- **Framework authors** looking for reference implementations of CLI-based agent tools
- **Researchers testing agent behavior** who need deterministic, mockable tool interfaces
- **Anyone tired of running servers** just to give an agent a weather lookup

---

## Repository Structure

```
Agent-cli-ToolHub/
├── src/
│   ├── cli.py              # Main entrypoint, subcommand routing
│   ├── weather.py           # ath weather
│   ├── search.py            # ath search
│   ├── convert.py           # ath convert
│   └── verify.py            # ath verify
├── skills/
│   ├── ath-weather/SKILL.md
│   ├── ath-search/SKILL.md
│   ├── ath-convert/SKILL.md
│   └── ath-verify/SKILL.md
├── tests/
│   ├── test_weather.py
│   ├── test_search.py
│   ├── test_convert.py
│   └── test_verify.py
├── AGENTS.md                # Instructions for AI agents working on this repo
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
└── LICENSE
```

Each tool is one Python file under `src/` with a `run(args)` function. Each skill is one folder under `skills/` with a `SKILL.md`. Adding a new tool means adding one of each.

---

## Contributing

We welcome contributions. Small, focused, well-documented tools are the goal.

### Adding a new tool

1. Create `src/<toolname>.py` with a `run(args)` function that prints JSON to stdout
2. Add the subcommand parser to `src/cli.py`
3. Create `skills/ath-<toolname>/SKILL.md` with AgentSkills frontmatter
4. Add tests in `tests/test_<toolname>.py`
5. Update the tool table in this README

### Design rules for new tools

- **JSON to stdout, errors to stderr** — follow the output contract above
- **Use structured exit codes** — 0 for success, 1-5 for typed errors
- **No background processes** — the command runs and exits
- **Minimal dependencies** — prefer Python standard library; put optional deps in `[project.optional-dependencies]`
- **Include a SKILL.md** — so agents can discover your tool automatically

### Running tests

```bash
pip install -e .
python -m pytest tests/ -v
```

---

## Attribution

Tool logic is ported from [Agent-Tool-Hub](https://github.com/andylow92/Agent-Tool-Hub-) — an open source collection of standalone HTTP tools for AI agents. This repo repackages that logic as CLI subcommands with no running servers, following the pattern established by [Google Workspace CLI](https://github.com/googleworkspace/cli).

---

## License

[MIT](LICENSE)
