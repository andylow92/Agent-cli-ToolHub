"""Tests for the convert tool."""

import json
import os
import subprocess
import sys
import tempfile

import pytest


def run_ath(*args):
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestConvertHelp:
    def test_help_exits_cleanly(self):
        code, stdout, _ = run_ath("convert", "--help")
        assert code == 0
        assert "--input" in stdout
        assert "--to" in stdout


class TestConvertValidation:
    def test_missing_input_flag(self):
        code, _, _ = run_ath("convert", "--to", "json")
        assert code != 0

    def test_missing_to_flag(self):
        code, _, _ = run_ath("convert", "--input", "file.csv")
        assert code != 0

    def test_file_not_found(self):
        code, _, stderr = run_ath("convert", "--input", "/nonexistent/file.csv", "--to", "json")
        assert code == 4
        err = json.loads(stderr)
        assert err["status"] == "error"
        assert err["code"] == "FILE_NOT_FOUND"


class TestConvertCSVtoJSON:
    def test_csv_to_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,age\nAlice,30\nBob,25\n")
            f.flush()
            code, stdout, _ = run_ath("convert", "--input", f.name, "--to", "json")
        os.unlink(f.name)

        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert out["data"]["rows"] == 2
        assert out["data"]["columns"] == ["name", "age"]
        assert out["data"]["data"][0]["name"] == "Alice"
        assert out["data"]["data"][1]["age"] == "25"


class TestConvertJSONtoCSV:
    def test_json_to_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"name": "Alice", "age": 30}], f)
            f.flush()
            code, stdout, _ = run_ath("convert", "--input", f.name, "--to", "csv")
        os.unlink(f.name)

        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert out["data"]["rows"] == 1


class TestConvertXML:
    def test_xml_to_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<root><item>hello</item></root>")
            f.flush()
            code, stdout, _ = run_ath("convert", "--input", f.name, "--to", "json")
        os.unlink(f.name)

        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert "root" in out["data"]["data"]


class TestConvertMarkdown:
    def test_markdown_to_text(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Hello\n\n**Bold** text")
            f.flush()
            code, stdout, _ = run_ath("convert", "--input", f.name, "--to", "text")
        os.unlink(f.name)

        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert "Hello" in out["data"]["data"]
        assert "Bold" in out["data"]["data"]

    def test_markdown_to_html(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Hello\n\n**Bold**")
            f.flush()
            code, stdout, _ = run_ath("convert", "--input", f.name, "--to", "html")
        os.unlink(f.name)

        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert "<h1>" in out["data"]["data"]


class TestConvertHTML:
    def test_html_to_text(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write("<html><body><p>Hello World</p></body></html>")
            f.flush()
            code, stdout, _ = run_ath("convert", "--input", f.name, "--to", "text")
        os.unlink(f.name)

        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert "Hello World" in out["data"]["data"]


class TestConvertWithOutput:
    def test_output_to_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,age\nAlice,30\n")
            f.flush()
            input_path = f.name

        output_path = input_path.replace(".csv", ".json")
        try:
            code, stdout, _ = run_ath("convert", "--input", input_path, "--to", "json", "--output", output_path)
            assert code == 0
            out = json.loads(stdout)
            assert out["status"] == "ok"
            assert os.path.exists(output_path)
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestConvertUnit:
    def test_list_conversions(self):
        from src.convert import list_conversions
        result = list_conversions()
        assert result["count"] > 0
        assert any(c["from"] == "csv" and c["to"] == "json" for c in result["conversions"])

    def test_unsupported_conversion(self):
        from src.convert import convert_content
        result = convert_content("data", "png", "json")
        assert "error" in result
        assert "Unsupported" in result["error"]
