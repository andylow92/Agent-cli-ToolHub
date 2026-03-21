"""Tests for the verify tool."""

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


class TestVerifyHelp:
    def test_help_exits_cleanly(self):
        code, stdout, _ = run_ath("verify", "--help")
        assert code == 0
        assert "--send" in stdout
        assert "--check" in stdout


class TestVerifyValidation:
    def test_missing_mode(self):
        code, _, _ = run_ath("verify")
        assert code != 0

    def test_send_missing_to(self):
        code, _, stderr = run_ath("verify", "--send", "--message", "hello")
        assert code == 3
        err = json.loads(stderr)
        assert err["status"] == "error"
        assert err["code"] == "VALIDATION_ERROR"

    def test_send_missing_message(self):
        code, _, stderr = run_ath("verify", "--send", "--to", "http://example.com")
        assert code == 3
        err = json.loads(stderr)
        assert err["status"] == "error"
        assert err["code"] == "VALIDATION_ERROR"

    def test_check_missing_request_id(self):
        code, _, stderr = run_ath("verify", "--check", "--response", "test")
        assert code == 3
        err = json.loads(stderr)
        assert err["status"] == "error"
        assert err["code"] == "VALIDATION_ERROR"

    def test_check_missing_response(self):
        code, _, stderr = run_ath("verify", "--check", "--request-id", "abc")
        assert code == 3
        err = json.loads(stderr)
        assert err["status"] == "error"
        assert err["code"] == "VALIDATION_ERROR"


class TestVerifyCheck:
    def test_check_matching_request_id(self):
        response = json.dumps({"request_id": "abc-123", "response": "hello"})
        code, stdout, _ = run_ath("verify", "--check", "--request-id", "abc-123", "--response", response)
        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert out["data"]["verified"] is True

    def test_check_mismatched_request_id(self):
        response = json.dumps({"request_id": "wrong-id", "response": "hello"})
        code, stdout, _ = run_ath("verify", "--check", "--request-id", "abc-123", "--response", response)
        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert out["data"]["verified"] is False

    def test_check_plain_text_with_id(self):
        code, stdout, _ = run_ath("verify", "--check", "--request-id", "abc-123", "--response", "contains abc-123 in text")
        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert out["data"]["verified"] is True


class TestVerifyUnit:
    def test_check_response_verified(self):
        from src.verify import check_response
        result = check_response("test-id", json.dumps({"request_id": "test-id", "response": "ok"}))
        assert result["verified"] is True

    def test_check_response_failed(self):
        from src.verify import check_response
        result = check_response("test-id", json.dumps({"request_id": "other-id"}))
        assert result["verified"] is False

    @patch("src.verify.urlopen")
    def test_send_message_success(self, mock_urlopen):
        import io
        from src.verify import send_message

        # We need to capture the request_id that gets generated
        original_uuid4 = __import__("uuid").uuid4

        def fake_uuid4():
            return type("UUID", (), {"__str__": lambda self: "fixed-uuid-123"})()

        with patch("src.verify.uuid.uuid4", fake_uuid4):
            mock_data = json.dumps({
                "request_id": "fixed-uuid-123",
                "response": "pong",
                "from": "test-agent",
            }).encode()

            mock_resp = io.BytesIO(mock_data)
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = lambda s, *a: None
            mock_resp.read = lambda max_bytes=None: mock_data
            mock_urlopen.return_value = mock_resp

            result = send_message("http://localhost:8004/talk", "ping")
            assert result["status"] == "verified"
            assert result["response"] == "pong"
            assert result["request_id"] == "fixed-uuid-123"
