"""Search tool — AI-powered web search via Perplexity Sonar API."""

import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.perplexity.ai/chat/completions"


def _output(data, file=sys.stdout):
    print(json.dumps(data, indent=2), file=file)


def _error(message, code, exit_code):
    _output({"status": "error", "error": message, "code": code}, file=sys.stderr)
    sys.exit(exit_code)


def search(query: str, model: str = "sonar", recency: str = None, max_tokens: int = 1024) -> dict:
    """Search the web using Perplexity Sonar and get a direct answer.

    Args:
        query: The question or search query.
        model: "sonar" (fast) or "sonar-pro" (deeper, more citations).
        recency: Filter sources by time — "day", "week", "month", "year", or None.
        max_tokens: Maximum length of the answer.

    Returns:
        dict with answer, citations, and usage.
    """
    api_key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not api_key:
        _error("PERPLEXITY_API_KEY environment variable is not set", "AUTH_MISSING", 2)

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Be precise and concise."},
            {"role": "user", "content": query},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "return_citations": True,
    }

    if recency:
        body["search_recency_filter"] = recency

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            detail = json.loads(raw).get("error", {}).get("message", raw)
        except (json.JSONDecodeError, AttributeError):
            detail = raw
        _error(f"API error {e.code}: {detail}", "API_ERROR", 1)
    except urllib.error.URLError as e:
        _error(f"Network error: {e.reason}", "API_ERROR", 1)

    choice = result.get("choices", [{}])[0]
    message = choice.get("message", {})
    usage = result.get("usage", {})

    return {
        "answer": message.get("content", ""),
        "citations": choice.get("citations", []),
        "model": result.get("model", model),
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        },
    }


def run(args):
    """CLI entrypoint for search tool."""
    result = search(args.query, model=args.model, recency=args.recency, max_tokens=args.max_results)
    _output({"status": "ok", "data": result})
