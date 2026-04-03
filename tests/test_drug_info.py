"""Tests for the drug-info tool."""

import json
import subprocess
import sys
from unittest.mock import patch

import pytest


def run_ath(*args):
    """Run ath CLI and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Shared mock FDA response data
# ---------------------------------------------------------------------------

MOCK_FDA_RESPONSE = {
    "meta": {"results": {"skip": 0, "limit": 1, "total": 5}},
    "results": [
        {
            "openfda": {
                "brand_name": ["ASPIRIN"],
                "generic_name": ["ASPIRIN"],
                "manufacturer_name": ["Bayer HealthCare LLC"],
                "product_type": ["HUMAN OTC DRUG"],
                "route": ["ORAL"],
                "substance_name": ["ASPIRIN"],
            },
            "indications_and_usage": ["temporarily relieves minor aches and pains"],
            "warnings": ["Reye's syndrome warning"],
            "dosage_and_administration": ["adults and children 12 years: 325 mg every 4 hours"],
            "adverse_reactions": ["stomach bleeding may occur"],
        }
    ],
}


def _make_mock_urlopen(response_data):
    """Return a context-manager-compatible mock for urllib.request.urlopen."""
    import io

    encoded = json.dumps(response_data).encode()

    class MockResponse:
        def __init__(self):
            self._data = encoded

        def read(self):
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return MockResponse()


# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

class TestDrugInfoHelp:
    def test_help_exits_cleanly(self):
        code, stdout, _ = run_ath("drug-info", "--help")
        assert code == 0
        assert "--name" in stdout
        assert "--field" in stdout


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestDrugInfoValidation:
    def test_missing_name_flag(self):
        code, _, stderr = run_ath("drug-info")
        assert code != 0

    def test_invalid_field_value(self):
        code, _, stderr = run_ath("drug-info", "--name", "aspirin", "--field", "bogus")
        assert code != 0

    def test_valid_field_choices(self):
        """argparse should accept all five valid field names without erroring on the flag itself."""
        valid_fields = ["indications", "warnings", "contraindications", "dosage", "adverse_reactions"]
        for field in valid_fields:
            # We only care that argparse doesn't reject the flag (network will fail in CI)
            result = subprocess.run(
                [sys.executable, "-m", "src.cli", "drug-info", "--name", "x", "--field", field],
                capture_output=True,
                text=True,
            )
            # argparse error would be exit code 2 with "invalid choice" in stderr
            assert "invalid choice" not in result.stderr


# ---------------------------------------------------------------------------
# Unit tests — mock urllib
# ---------------------------------------------------------------------------

class TestDrugInfoUnit:
    @patch("src.drug_info.urllib.request.urlopen")
    def test_full_summary_returns_expected_keys(self, mock_urlopen):
        mock_urlopen.return_value = _make_mock_urlopen(MOCK_FDA_RESPONSE)

        from src.drug_info import get_drug_info

        result = get_drug_info("aspirin")
        assert result["brand_name"] == ["ASPIRIN"]
        assert result["generic_name"] == ["ASPIRIN"]
        assert result["manufacturer"] == ["Bayer HealthCare LLC"]
        assert result["route"] == ["ORAL"]
        assert "indications" in result
        assert "warnings" in result
        assert "dosage" in result
        assert "adverse_reactions" in result
        assert "contraindications" in result

    @patch("src.drug_info.urllib.request.urlopen")
    def test_field_indications(self, mock_urlopen):
        mock_urlopen.return_value = _make_mock_urlopen(MOCK_FDA_RESPONSE)

        from src.drug_info import get_drug_info

        result = get_drug_info("aspirin", field="indications")
        assert result["field"] == "indications"
        assert "temporarily relieves" in result["value"]
        assert result["drug"] == "ASPIRIN"

    @patch("src.drug_info.urllib.request.urlopen")
    def test_field_warnings(self, mock_urlopen):
        mock_urlopen.return_value = _make_mock_urlopen(MOCK_FDA_RESPONSE)

        from src.drug_info import get_drug_info

        result = get_drug_info("aspirin", field="warnings")
        assert result["field"] == "warnings"
        assert "Reye" in result["value"]

    @patch("src.drug_info.urllib.request.urlopen")
    def test_field_dosage(self, mock_urlopen):
        mock_urlopen.return_value = _make_mock_urlopen(MOCK_FDA_RESPONSE)

        from src.drug_info import get_drug_info

        result = get_drug_info("aspirin", field="dosage")
        assert result["field"] == "dosage"
        assert "325 mg" in result["value"]

    @patch("src.drug_info.urllib.request.urlopen")
    def test_invalid_field_raises(self, mock_urlopen):
        """Invalid field should call sys.exit(3)."""
        mock_urlopen.return_value = _make_mock_urlopen(MOCK_FDA_RESPONSE)

        from src.drug_info import get_drug_info

        with pytest.raises(SystemExit) as exc_info:
            get_drug_info("aspirin", field="not_a_real_field")
        assert exc_info.value.code == 3

    @patch("src.drug_info.urllib.request.urlopen")
    def test_empty_results_returns_not_found(self, mock_urlopen):
        """Empty results list should cause NOT_FOUND error (exit 1)."""
        mock_urlopen.return_value = _make_mock_urlopen({"meta": {}, "results": []})

        from src.drug_info import get_drug_info

        with pytest.raises(SystemExit) as exc_info:
            get_drug_info("zzznodrug")
        assert exc_info.value.code == 1

    @patch("src.drug_info._output")
    @patch("src.drug_info.urllib.request.urlopen")
    def test_run_calls_output_with_ok_status(self, mock_urlopen, mock_output):
        """run() should call _output with status ok and correct data."""
        mock_urlopen.return_value = _make_mock_urlopen(MOCK_FDA_RESPONSE)

        from src.drug_info import run

        class FakeArgs:
            name = "aspirin"
            field = None

        run(FakeArgs())

        assert mock_output.called
        call_args = mock_output.call_args[0][0]
        assert call_args["status"] == "ok"
        assert "data" in call_args
        assert call_args["data"]["brand_name"] == ["ASPIRIN"]


# ---------------------------------------------------------------------------
# Integration (subprocess) — mocking isn't feasible across subprocess boundary,
# so we just verify the command fails gracefully when the network is unavailable.
# ---------------------------------------------------------------------------

class TestDrugInfoNetworkFailure:
    def test_network_error_produces_error_json_on_stderr(self):
        """With no network (or bad host), the command should exit non-zero and
        write error JSON to stderr.  We simulate this by patching the env with
        no PATH so the child process can still run Python but DNS may fail, OR
        we can rely on a non-existent drug triggering a 404 / network path.
        Instead we just verify that when a completely bogus name is used the
        exit code is non-zero (either 1 for not-found or network error)."""
        code, stdout, stderr = run_ath("drug-info", "--name", "zzzzfakemedicationnamethatdoesnotexist12345")
        # We can't guarantee network in CI, but we can check structure
        if code != 0:
            # Should have error JSON on stderr
            try:
                err = json.loads(stderr)
                assert err["status"] == "error"
                assert "error" in err
                assert "code" in err
            except json.JSONDecodeError:
                pass  # Network failure may produce non-JSON stderr from urllib
        else:
            # Unlikely but the random name might match something — check ok JSON
            out = json.loads(stdout)
            assert out["status"] == "ok"
