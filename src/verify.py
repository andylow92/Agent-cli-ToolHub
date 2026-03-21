"""Verify tool — Verified inter-agent communication with request_id verification."""

import json
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_MS = 10000
MAX_RESPONSE_BYTES = 100 * 1024  # 100 KB


def _output(data, file=sys.stdout):
    print(json.dumps(data, indent=2), file=file)


def _error(message, code, exit_code):
    _output({"status": "error", "error": message, "code": code}, file=sys.stderr)
    sys.exit(exit_code)


def send_message(target_url: str, message: str, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> dict:
    """Send a verified message to another agent.

    Generates a unique request_id and sends it along with the message.
    The target agent must echo back the request_id in its response for verification.

    Args:
        target_url: The URL of the target agent.
        message: The message to send.
        timeout_ms: Timeout in milliseconds.

    Returns:
        dict with request_id, status, and response data.
    """
    request_id = str(uuid.uuid4())
    start_time = time.monotonic()

    payload = json.dumps({
        "request_id": request_id,
        "message": message,
    }).encode()

    req = Request(
        target_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    timeout_sec = timeout_ms / 1000.0

    try:
        with urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read(MAX_RESPONSE_BYTES + 1)

            if len(raw) > MAX_RESPONSE_BYTES:
                latency_ms = round((time.monotonic() - start_time) * 1000, 1)
                return {
                    "status": "failed",
                    "error": "response_too_large",
                    "message": f"Response exceeded {MAX_RESPONSE_BYTES} bytes limit.",
                    "request_id": request_id,
                    "latency_ms": latency_ms,
                }

            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                latency_ms = round((time.monotonic() - start_time) * 1000, 1)
                return {
                    "status": "failed",
                    "error": "invalid_response",
                    "message": "Response is not valid JSON.",
                    "request_id": request_id,
                    "latency_ms": latency_ms,
                }

    except HTTPError as e:
        latency_ms = round((time.monotonic() - start_time) * 1000, 1)
        return {
            "status": "failed",
            "error": "unreachable",
            "message": f"HTTP {e.code} from target.",
            "request_id": request_id,
            "latency_ms": latency_ms,
        }
    except (URLError, OSError) as e:
        latency_ms = round((time.monotonic() - start_time) * 1000, 1)
        return {
            "status": "failed",
            "error": "unreachable",
            "message": f"Could not reach target: {e}",
            "request_id": request_id,
            "latency_ms": latency_ms,
        }
    except TimeoutError:
        latency_ms = round((time.monotonic() - start_time) * 1000, 1)
        return {
            "status": "failed",
            "error": "timeout",
            "message": f"Request timed out after {timeout_ms}ms.",
            "request_id": request_id,
            "latency_ms": latency_ms,
        }

    # Verify request_id in response
    returned_id = body.get("request_id")
    latency_ms = round((time.monotonic() - start_time) * 1000, 1)

    if returned_id != request_id:
        return {
            "status": "failed",
            "error": "request_id_mismatch",
            "message": f"Response returned request_id '{returned_id}' but expected '{request_id}'.",
            "request_id": request_id,
            "latency_ms": latency_ms,
        }

    return {
        "status": "verified",
        "response": body.get("response", ""),
        "source": body.get("from", target_url),
        "request_id": request_id,
        "latency_ms": latency_ms,
    }


def check_response(request_id: str, response: str) -> dict:
    """Check if a response text contains the expected request_id.

    Args:
        request_id: The expected request_id.
        response: The response text to verify.

    Returns:
        dict with verification result.
    """
    try:
        body = json.loads(response)
        returned_id = body.get("request_id")
    except (json.JSONDecodeError, AttributeError):
        returned_id = None
        # Also check if the request_id appears as plain text
        if request_id in response:
            return {
                "verified": True,
                "request_id": request_id,
                "note": "request_id found in response text (not structured JSON).",
            }

    if returned_id == request_id:
        return {
            "verified": True,
            "request_id": request_id,
        }

    return {
        "verified": False,
        "request_id": request_id,
        "returned_id": returned_id,
        "message": "request_id not found or does not match.",
    }


def run(args):
    """CLI entrypoint for verify tool."""
    if args.send:
        if not args.target_url:
            _error("--to is required with --send", "VALIDATION_ERROR", 3)
        if not args.message:
            _error("--message is required with --send", "VALIDATION_ERROR", 3)
        result = send_message(args.target_url, args.message, timeout_ms=args.timeout)
        _output({"status": "ok", "data": result})

    elif args.check:
        if not args.request_id:
            _error("--request-id is required with --check", "VALIDATION_ERROR", 3)
        if not args.response:
            _error("--response is required with --check", "VALIDATION_ERROR", 3)
        result = check_response(args.request_id, args.response)
        _output({"status": "ok", "data": result})
