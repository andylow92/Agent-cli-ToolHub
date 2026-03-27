# CLI Tools Hub (`ath`)

A single CLI that wraps multiple AI-agent-friendly tools into subcommands. Every tool returns structured JSON to stdout, takes arguments via flags, and requires zero running server processes.

## Why

AI agents need tools they can call directly from the command line — no servers, no daemons, no background processes. Just run, get JSON, exit. CLI Tools Hub packages common agent utilities into one installable command.

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
pip install cli-tools-hub[pdf]    # PDF conversion (PyPDF2)
pip install cli-tools-hub[xlsx]   # XLSX conversion (openpyxl)
pip install cli-tools-hub[all]    # All optional dependencies
```

## Quick Start

```bash
# Get weather
ath weather --city "London"

# AI-powered web search
ath search --query "latest Python 3.13 features"

# Convert CSV to JSON
ath convert --input data.csv --to json

# Save agent output as organised Markdown
ath md-organizer save --title "Research Notes" --category research --content "# Findings..."

# Browse your knowledge base in the browser
ath md-organizer serve

# Send verified message to another agent
ath verify --send --to http://localhost:8004/talk --message "hello"

# Check a response
ath verify --check --request-id "abc-123" --response '{"request_id": "abc-123"}'
```

## Tools

| Tool | Command | Description | Required Env Vars |
|------|---------|-------------|-------------------|
| Weather | `ath weather` | Current weather for any city via OpenWeatherMap | `OPENWEATHERMAP_API_KEY` |
| Search | `ath search` | AI-powered web search via Perplexity Sonar | `PERPLEXITY_API_KEY` |
| Convert | `ath convert` | Convert between file formats (CSV, JSON, XML, HTML, Markdown, PDF, XLSX) | None |
| MD Organizer | `ath md-organizer` | Save, organise, search, and browse Markdown files with a GitHub-style viewer | None |
| Verify | `ath verify` | Verified inter-agent communication with request_id verification | None |

## Output Format

Every command returns structured JSON:

**Success** (exit code 0, stdout):
```json
{"status": "ok", "data": { ... }}
```

**Error** (non-zero exit code, stderr):
```json
{"status": "error", "error": "Missing API key", "code": "AUTH_MISSING"}
```

| Exit Code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | API error |
| 2 | Auth error |
| 3 | Validation error |
| 4 | File error |
| 5 | Internal error |

## Agent Integration

### OpenClaw

```bash
ln -s $(pwd)/skills/ath-* ~/.openclaw/skills/
# or
cp -r skills/ath-* ~/.openclaw/skills/
```

### Claude Code

Add to your project's tool configuration or reference the SKILL.md files in your agent's skill discovery path.

### Cursor

Point Cursor's tool discovery at the `skills/` directory. Each `SKILL.md` contains the usage instructions, flags, and examples.

## Environment Variables

```bash
export OPENWEATHERMAP_API_KEY="your_key_here"  # For ath weather
export PERPLEXITY_API_KEY="your_key_here"       # For ath search
```

See `.env.example` for a template.

## Contributing

### Adding a new tool

1. Create `src/<toolname>.py` with a `run(args)` function
2. Add the subcommand parser to `src/cli.py`
3. Create `skills/ath-<toolname>/SKILL.md`
4. Add tests in `tests/test_<toolname>.py`
5. Update the tool table in this README

### Running tests

```bash
pip install -e .
python -m pytest tests/
```

## Attribution

Tool logic is ported from [Agent-Tool-Hub](https://github.com/andylow92/Agent-Tool-Hub-), repackaged as CLI subcommands with no running servers.

## License

[MIT](LICENSE)
