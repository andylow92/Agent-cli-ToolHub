---
name: ath_search
description: AI-powered web search via Perplexity Sonar API using the CLI Tools Hub search command.
metadata: {"openclaw": {"requires": {"bins": ["ath"]}, "primaryEnv": "PERPLEXITY_API_KEY"}}
---

# AI Web Search

When the user asks a question that requires up-to-date web information, use this tool to get a direct answer with citations.

## Usage

```bash
ath search --query "latest Next.js API changes"
ath search --query "who won the game last night" --recency day
ath search --query "quantum computing explained" --model sonar-pro --max-results 2048
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--query` | Yes | — | The search query or question |
| `--model` | No | `sonar` | `sonar` (fast) or `sonar-pro` (deeper) |
| `--recency` | No | None | Filter: `day`, `week`, `month`, `year` |
| `--max-results` | No | 1024 | Max tokens in response |

## Output

Returns JSON with a direct answer and source citations.

```json
{
  "status": "ok",
  "data": {
    "answer": "The latest Next.js 15 introduced...",
    "citations": ["https://nextjs.org/blog/..."],
    "model": "sonar",
    "usage": {"prompt_tokens": 20, "completion_tokens": 150, "total_tokens": 170}
  }
}
```

## Requirements

- Environment variable `PERPLEXITY_API_KEY` must be set
- Install: `pip install cli-tools-hub`

## When to use

- User asks a factual question requiring current information
- User needs web search results summarized with sources
- User asks "search for..." or "look up..."

## When NOT to use

- Questions answerable from the codebase or local files
- Tasks that don't need web information
- When the user explicitly wants raw search links (use a browser tool instead)
