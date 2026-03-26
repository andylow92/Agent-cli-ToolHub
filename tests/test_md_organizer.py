"""Tests for the md-organizer tool."""

import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest


def run_ath(*args):
    """Run ath CLI and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


@pytest.fixture
def hub_dir(tmp_path):
    """Provide a temp directory for the hub."""
    hub = str(tmp_path / "test-hub")
    yield hub
    if os.path.isdir(hub):
        shutil.rmtree(hub)


class TestMdOrganizerHelp:
    def test_help_exits_cleanly(self):
        code, stdout, _ = run_ath("md-organizer", "--help")
        assert code == 0
        assert "md-organizer" in stdout.lower() or "organis" in stdout.lower()

    def test_init_help(self):
        code, stdout, _ = run_ath("md-organizer", "init", "--help")
        assert code == 0
        assert "--path" in stdout

    def test_save_help(self):
        code, stdout, _ = run_ath("md-organizer", "save", "--help")
        assert code == 0
        assert "--title" in stdout
        assert "--content" in stdout

    def test_serve_help(self):
        code, stdout, _ = run_ath("md-organizer", "serve", "--help")
        assert code == 0
        assert "--port" in stdout


class TestMdOrganizerValidation:
    def test_save_missing_title(self):
        code, _, stderr = run_ath("md-organizer", "save", "--content", "hello")
        assert code != 0

    def test_save_missing_content_and_file(self, hub_dir):
        code, _, stderr = run_ath("md-organizer", "save", "--title", "Test", "--path", hub_dir)
        assert code == 3
        err = json.loads(stderr)
        assert err["status"] == "error"
        assert err["code"] == "VALIDATION_ERROR"

    def test_save_file_not_found(self, hub_dir):
        code, _, stderr = run_ath(
            "md-organizer", "save", "--title", "Test",
            "--file", "/nonexistent/file.md", "--path", hub_dir,
        )
        assert code == 4
        err = json.loads(stderr)
        assert err["code"] == "FILE_NOT_FOUND"


class TestMdOrganizerInit:
    def test_init_creates_hub(self, hub_dir):
        code, stdout, _ = run_ath("md-organizer", "init", "--path", hub_dir)
        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert os.path.isdir(hub_dir)
        assert os.path.isfile(os.path.join(hub_dir, "index.md"))

    def test_init_idempotent(self, hub_dir):
        run_ath("md-organizer", "init", "--path", hub_dir)
        code, stdout, _ = run_ath("md-organizer", "init", "--path", hub_dir)
        assert code == 0
        out = json.loads(stdout)
        assert "already" in out["data"]["message"].lower()


class TestMdOrganizerSave:
    def test_save_creates_file(self, hub_dir):
        code, stdout, _ = run_ath(
            "md-organizer", "save",
            "--title", "My Research",
            "--content", "# Hello\nSome research notes.",
            "--category", "research",
            "--path", hub_dir,
        )
        assert code == 0
        out = json.loads(stdout)
        assert out["status"] == "ok"
        assert out["data"]["title"] == "My Research"
        assert out["data"]["category"] == "research"
        assert os.path.isfile(out["data"]["file"])

        # Check file content
        with open(out["data"]["file"], "r") as f:
            content = f.read()
        assert "title: My Research" in content
        assert "# Hello" in content

    def test_save_with_tags(self, hub_dir):
        code, stdout, _ = run_ath(
            "md-organizer", "save",
            "--title", "Tagged Doc",
            "--content", "Content here.",
            "--tags", "api,security",
            "--path", hub_dir,
        )
        assert code == 0
        out = json.loads(stdout)
        assert out["data"]["tags"] == ["api", "security"]

    def test_save_from_file(self, hub_dir, tmp_path):
        source = tmp_path / "source.md"
        source.write_text("# From File\nThis came from a file.")

        code, stdout, _ = run_ath(
            "md-organizer", "save",
            "--title", "File Import",
            "--file", str(source),
            "--path", hub_dir,
        )
        assert code == 0
        out = json.loads(stdout)
        assert os.path.isfile(out["data"]["file"])

        with open(out["data"]["file"], "r") as f:
            content = f.read()
        assert "From File" in content

    def test_save_creates_index(self, hub_dir):
        run_ath(
            "md-organizer", "save",
            "--title", "Doc One",
            "--content", "Content.",
            "--category", "notes",
            "--path", hub_dir,
        )
        index_path = os.path.join(hub_dir, "notes", "index.md")
        assert os.path.isfile(index_path)
        with open(index_path, "r") as f:
            index_content = f.read()
        assert "Doc One" in index_content

    def test_save_duplicate_title_gets_suffix(self, hub_dir):
        run_ath(
            "md-organizer", "save",
            "--title", "Same Title",
            "--content", "First.",
            "--path", hub_dir,
        )
        code, stdout, _ = run_ath(
            "md-organizer", "save",
            "--title", "Same Title",
            "--content", "Second.",
            "--path", hub_dir,
        )
        assert code == 0
        out = json.loads(stdout)
        assert "-1" in out["data"]["file"]


class TestMdOrganizerList:
    def test_list_empty_hub(self, hub_dir):
        run_ath("md-organizer", "init", "--path", hub_dir)
        code, stdout, _ = run_ath("md-organizer", "list", "--path", hub_dir)
        assert code == 0
        out = json.loads(stdout)
        assert out["data"]["count"] == 0

    def test_list_shows_saved_docs(self, hub_dir):
        run_ath(
            "md-organizer", "save",
            "--title", "Alpha",
            "--content", "A.",
            "--category", "cat1",
            "--path", hub_dir,
        )
        run_ath(
            "md-organizer", "save",
            "--title", "Beta",
            "--content", "B.",
            "--category", "cat2",
            "--path", hub_dir,
        )
        code, stdout, _ = run_ath("md-organizer", "list", "--path", hub_dir)
        assert code == 0
        out = json.loads(stdout)
        assert out["data"]["count"] == 2
        titles = [d["title"] for d in out["data"]["documents"]]
        assert "Alpha" in titles
        assert "Beta" in titles

    def test_list_filter_by_category(self, hub_dir):
        run_ath(
            "md-organizer", "save",
            "--title", "InCat", "--content", ".",
            "--category", "target", "--path", hub_dir,
        )
        run_ath(
            "md-organizer", "save",
            "--title", "NotInCat", "--content", ".",
            "--category", "other", "--path", hub_dir,
        )
        code, stdout, _ = run_ath("md-organizer", "list", "--category", "target", "--path", hub_dir)
        assert code == 0
        out = json.loads(stdout)
        assert out["data"]["count"] == 1
        assert out["data"]["documents"][0]["title"] == "InCat"


class TestMdOrganizerSearch:
    def test_search_finds_match(self, hub_dir):
        run_ath(
            "md-organizer", "save",
            "--title", "Auth Guide",
            "--content", "Use OAuth tokens for authentication.",
            "--path", hub_dir,
        )
        run_ath(
            "md-organizer", "save",
            "--title", "Unrelated",
            "--content", "Nothing relevant here.",
            "--path", hub_dir,
        )
        code, stdout, _ = run_ath("md-organizer", "search", "--query", "OAuth", "--path", hub_dir)
        assert code == 0
        out = json.loads(stdout)
        assert out["data"]["count"] == 1
        assert out["data"]["results"][0]["title"] == "Auth Guide"

    def test_search_no_results(self, hub_dir):
        run_ath(
            "md-organizer", "save",
            "--title", "Doc", "--content", "Some text.",
            "--path", hub_dir,
        )
        code, stdout, _ = run_ath("md-organizer", "search", "--query", "zzzznotfound", "--path", hub_dir)
        assert code == 0
        out = json.loads(stdout)
        assert out["data"]["count"] == 0

    def test_search_no_hub(self, hub_dir):
        code, stdout, _ = run_ath("md-organizer", "search", "--query", "test", "--path", hub_dir)
        assert code == 0
        out = json.loads(stdout)
        assert out["data"]["count"] == 0


class TestMdOrganizerUnit:
    """Unit tests for internal functions."""

    def test_slugify(self):
        from src.md_organizer import _slugify
        assert _slugify("Hello World") == "hello-world"
        assert _slugify("React Hooks Research!") == "react-hooks-research"
        assert _slugify("  spaces  ") == "spaces"
        assert _slugify("") == "untitled"

    def test_parse_frontmatter(self):
        from src.md_organizer import _parse_frontmatter
        content = "---\ntitle: Test\ndate: 2024-01-01\ntags: [a, b]\n---\n\nBody text."
        meta, body = _parse_frontmatter(content)
        assert meta["title"] == "Test"
        assert meta["tags"] == ["a", "b"]
        assert "Body text." in body

    def test_parse_frontmatter_no_frontmatter(self):
        from src.md_organizer import _parse_frontmatter
        meta, body = _parse_frontmatter("Just plain text.")
        assert meta == {}
        assert body == "Just plain text."

    def test_frontmatter_generation(self):
        from src.md_organizer import _frontmatter
        fm = _frontmatter("My Doc", "research", ["tag1", "tag2"])
        assert "title: My Doc" in fm
        assert "category: research" in fm
        assert "tags: [tag1, tag2]" in fm

    def test_md_to_html_headings(self):
        from src.md_organizer import _md_to_html
        html = _md_to_html("# Title\n\n## Subtitle")
        assert "<h1>Title</h1>" in html
        assert "<h2>Subtitle</h2>" in html

    def test_md_to_html_bold_italic(self):
        from src.md_organizer import _md_to_html
        html = _md_to_html("**bold** and *italic*")
        assert "<strong>bold</strong>" in html
        assert "<em>italic</em>" in html

    def test_md_to_html_code_block(self):
        from src.md_organizer import _md_to_html
        html = _md_to_html("```python\nprint('hi')\n```")
        assert "<pre><code>" in html
        assert "print('hi')" in html

    def test_md_to_html_links(self):
        from src.md_organizer import _md_to_html
        html = _md_to_html("[Click](https://example.com)")
        assert 'href="https://example.com"' in html
        assert "Click</a>" in html

    def test_init_hub(self, hub_dir):
        from src.md_organizer import init_hub
        result = init_hub(hub_dir)
        assert "initialised" in result["message"].lower()
        assert os.path.isfile(os.path.join(hub_dir, "index.md"))

    def test_save_and_list(self, hub_dir):
        from src.md_organizer import init_hub, save_document, list_documents
        init_hub(hub_dir)
        save_document("Test Doc", "Content here.", category="notes", path=hub_dir)
        result = list_documents(path=hub_dir)
        assert result["count"] == 1
        assert result["documents"][0]["title"] == "Test Doc"

    def test_save_and_search(self, hub_dir):
        from src.md_organizer import init_hub, save_document, search_documents
        init_hub(hub_dir)
        save_document("API Notes", "The authentication flow uses JWT tokens.", path=hub_dir)
        result = search_documents("JWT", path=hub_dir)
        assert result["count"] == 1
        assert len(result["results"][0]["snippets"]) > 0
