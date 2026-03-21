"""Tests for the search tool."""

import json
import subprocess
import sys
from unittest.mock import patch

import pytest


def run_ath(*args):
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestSearchHelp:
    def test_help_exits_cleanly(self):
        code, stdout, _ = run_ath("search", "--help")
        assert code == 0
        assert "--query" in stdout
        assert "--model" in stdout


class TestSearchValidation:
    def test_missing_query_flag(self):
        code, _, stderr = run_ath("search")
        assert code != 0

    def test_missing_api_key(self):
        env = {"PATH": ""}
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "search", "--query", "test"],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 2
        err = json.loads(result.stderr)
        assert err["status"] == "error"
        assert err["code"] == "AUTH_MISSING"


class TestSearchUnit:
    @patch("src.search.urllib.request.urlopen")
    @patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test_key"})
    def test_search_success(self, mock_urlopen):
        import io
        from src.search import search

        mock_data = json.dumps({
            "choices": [{
                "message": {"content": "Python 3.13 introduced..."},
                "citations": ["https://python.org/3.13"],
            }],
            "model": "sonar",
            "usage": {"prompt_tokens": 20, "completion_tokens": 100, "total_tokens": 120},
        }).encode()

        mock_resp = io.BytesIO(mock_data)
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = lambda s, *a: None
        mock_resp.read = lambda: mock_data
        mock_urlopen.return_value = mock_resp

        result = search("Python 3.13 features")
        assert result["answer"] == "Python 3.13 introduced..."
        assert len(result["citations"]) == 1
        assert result["model"] == "sonar"
        assert result["usage"]["total_tokens"] == 120
