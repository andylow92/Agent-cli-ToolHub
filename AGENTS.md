# AGENTS.md

## Project overview
CLI Tools Hub (`ath`) is a single Python CLI that provides AI-agent-friendly tools as subcommands.

## Setup
```bash
pip install -e .
```

## Testing
```bash
python -m pytest tests/
```

## Architecture
- `src/cli.py` — entrypoint and argparse routing
- `src/<tool>.py` — one module per tool, each exposes a `run(args)` function
- `skills/` — AgentSkills SKILL.md files for agent integration
- All tools print JSON to stdout, errors to stderr
- No HTTP servers, no background processes

## Output contract
Every command follows this contract:

**Success** (exit code 0, JSON to stdout):
```json
{"status": "ok", "data": { ... }}
```

**Error** (non-zero exit code, JSON to stderr):
```json
{"status": "error", "error": "Missing API key", "code": "AUTH_MISSING"}
```

**Exit codes:**
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API error (remote service failure) |
| 2 | Auth error (missing/invalid API key) |
| 3 | Validation error (bad arguments) |
| 4 | File error (not found, unsupported format) |
| 5 | Internal error |

## Adding a new tool

1. Create `src/<toolname>.py` with a `run(args)` function
2. Add the subcommand to `src/cli.py`
3. Create `skills/ath-<toolname>/SKILL.md`
4. Add tests in `tests/test_<toolname>.py`
5. Update `README.md` tool table
