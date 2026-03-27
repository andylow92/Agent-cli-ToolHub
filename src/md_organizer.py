"""Markdown Organizer — Save, organize, and browse Markdown files as a knowledge base."""

import datetime
import http.server
import json
import os
import re
import sys
import threading
import webbrowser


DEFAULT_HUB = ".md-hub"


def _output(data, file=sys.stdout):
    print(json.dumps(data, indent=2, default=str), file=file)


def _error(message, code, exit_code):
    _output({"status": "error", "error": message, "code": code}, file=sys.stderr)
    sys.exit(exit_code)


def _hub_path(base=None):
    """Resolve the hub root directory."""
    return os.path.abspath(base or DEFAULT_HUB)


def _slugify(text):
    """Turn a title into a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "untitled"


def _frontmatter(title, category, tags):
    """Generate YAML front-matter block."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = ["---", f"title: {title}", f"date: {now}", f"category: {category}"]
    if tags:
        lines.append(f"tags: [{', '.join(tags)}]")
    lines.append("---")
    return "\n".join(lines)


def _parse_frontmatter(content):
    """Extract YAML front-matter as a dict and body text."""
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not match:
        return {}, content
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            val = val.strip()
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip() for v in val[1:-1].split(",") if v.strip()]
            meta[key.strip()] = val
    return meta, match.group(2)


def _rebuild_index(hub, category_dir):
    """Rebuild the index.md for a category directory."""
    entries = []
    for fname in sorted(os.listdir(category_dir)):
        if fname == "index.md" or not fname.endswith(".md"):
            continue
        fpath = os.path.join(category_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            meta, _ = _parse_frontmatter(f.read())
        title = meta.get("title", fname.replace(".md", "").replace("-", " ").title())
        date = meta.get("date", "")
        entries.append(f"- [{title}]({fname}) — {date}")

    category_name = os.path.basename(category_dir)
    index_content = f"# {category_name.replace('-', ' ').title()}\n\n"
    if entries:
        index_content += "\n".join(entries) + "\n"
    else:
        index_content += "_No documents yet._\n"

    with open(os.path.join(category_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write(index_content)

    # Rebuild root index
    _rebuild_root_index(hub)


def _rebuild_root_index(hub):
    """Rebuild the root index.md listing all categories."""
    lines = ["# Knowledge Base\n"]
    for name in sorted(os.listdir(hub)):
        cat_dir = os.path.join(hub, name)
        if not os.path.isdir(cat_dir):
            continue
        count = len([f for f in os.listdir(cat_dir) if f.endswith(".md") and f != "index.md"])
        lines.append(f"- [{name.replace('-', ' ').title()}]({name}/) — {count} document{'s' if count != 1 else ''}")
    lines.append("")
    with open(os.path.join(hub, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def init_hub(path=None):
    """Initialise a .md-hub directory."""
    hub = _hub_path(path)
    if os.path.isdir(hub):
        return {"path": hub, "message": "Hub already exists"}
    os.makedirs(hub, exist_ok=True)
    with open(os.path.join(hub, "index.md"), "w", encoding="utf-8") as f:
        f.write("# Knowledge Base\n\n_No categories yet. Use `ath md-organizer save` to add documents._\n")
    return {"path": hub, "message": "Hub initialised"}


def save_document(title, content, category="general", tags=None, path=None, source_file=None):
    """Save content as an organised .md file.

    Args:
        title: Document title.
        content: Markdown text body (or None if source_file is given).
        category: Sub-directory category name.
        tags: Optional list of tags.
        path: Custom hub root.
        source_file: Read content from this file instead.
    """
    hub = _hub_path(path)
    if not os.path.isdir(hub):
        init_hub(path)

    if source_file:
        if not os.path.isfile(source_file):
            _error(f"File not found: {source_file}", "FILE_NOT_FOUND", 4)
        with open(source_file, "r", encoding="utf-8") as f:
            content = f.read()

    if not content:
        _error("No content provided. Use --content or --file.", "VALIDATION_ERROR", 3)

    cat_dir = os.path.join(hub, _slugify(category))
    os.makedirs(cat_dir, exist_ok=True)

    slug = _slugify(title)
    filename = f"{slug}.md"
    filepath = os.path.join(cat_dir, filename)

    # If file exists, append a numeric suffix
    counter = 1
    while os.path.exists(filepath):
        filename = f"{slug}-{counter}.md"
        filepath = os.path.join(cat_dir, filename)
        counter += 1

    fm = _frontmatter(title, category, tags or [])
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(fm + "\n\n" + content + "\n")

    _rebuild_index(hub, cat_dir)

    return {
        "file": filepath,
        "title": title,
        "category": category,
        "tags": tags or [],
    }


def list_documents(category=None, path=None):
    """List all documents in the hub."""
    hub = _hub_path(path)
    if not os.path.isdir(hub):
        return {"documents": [], "count": 0, "message": "Hub not initialised. Run: ath md-organizer init"}

    docs = []
    for cat_name in sorted(os.listdir(hub)):
        cat_dir = os.path.join(hub, cat_name)
        if not os.path.isdir(cat_dir):
            continue
        if category and _slugify(category) != cat_name:
            continue
        for fname in sorted(os.listdir(cat_dir)):
            if fname == "index.md" or not fname.endswith(".md"):
                continue
            fpath = os.path.join(cat_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                meta, body = _parse_frontmatter(f.read())
            docs.append({
                "title": meta.get("title", fname),
                "category": cat_name,
                "date": meta.get("date", ""),
                "tags": meta.get("tags", []),
                "file": fpath,
                "size_bytes": os.path.getsize(fpath),
            })

    return {"documents": docs, "count": len(docs)}


def search_documents(query, path=None):
    """Search documents by title or body text."""
    hub = _hub_path(path)
    if not os.path.isdir(hub):
        return {"results": [], "count": 0}

    query_lower = query.lower()
    results = []
    for cat_name in sorted(os.listdir(hub)):
        cat_dir = os.path.join(hub, cat_name)
        if not os.path.isdir(cat_dir):
            continue
        for fname in sorted(os.listdir(cat_dir)):
            if fname == "index.md" or not fname.endswith(".md"):
                continue
            fpath = os.path.join(cat_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                raw = f.read()
            meta, body = _parse_frontmatter(raw)
            title = meta.get("title", fname)
            if query_lower in title.lower() or query_lower in body.lower():
                # Find matching lines for context
                snippets = []
                for line in body.splitlines():
                    if query_lower in line.lower():
                        snippets.append(line.strip())
                        if len(snippets) >= 3:
                            break
                results.append({
                    "title": title,
                    "category": cat_name,
                    "file": fpath,
                    "snippets": snippets,
                })

    return {"results": results, "count": len(results), "query": query}


# ---------------------------------------------------------------------------
# HTML server
# ---------------------------------------------------------------------------

_GITHUB_CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
margin:0;background:#0d1117;color:#c9d1d9}
#sidebar{position:fixed;top:0;left:0;width:260px;height:100%;background:#161b22;
border-right:1px solid #30363d;overflow-y:auto;padding:16px;box-sizing:border-box}
#sidebar h2{color:#58a6ff;font-size:14px;margin:0 0 12px}
#sidebar a{display:block;color:#c9d1d9;text-decoration:none;padding:4px 8px;
border-radius:6px;font-size:13px;margin:2px 0}
#sidebar a:hover,#sidebar a.active{background:#21262d;color:#58a6ff}
#sidebar .cat{font-weight:600;margin-top:12px;color:#8b949e;font-size:12px;
text-transform:uppercase;letter-spacing:.5px;padding:4px 8px}
#content{margin-left:260px;padding:32px 48px;max-width:900px}
.markdown-body{line-height:1.6}
.markdown-body h1{padding-bottom:8px;border-bottom:1px solid #30363d;color:#c9d1d9}
.markdown-body h2{padding-bottom:6px;border-bottom:1px solid #21262d;color:#c9d1d9;margin-top:24px}
.markdown-body h3{color:#c9d1d9}
.markdown-body p{margin:8px 0}
.markdown-body a{color:#58a6ff;text-decoration:none}
.markdown-body a:hover{text-decoration:underline}
.markdown-body code{background:#161b22;padding:2px 6px;border-radius:4px;font-size:85%;color:#c9d1d9}
.markdown-body pre{background:#161b22;padding:16px;border-radius:6px;overflow-x:auto;
border:1px solid #30363d}
.markdown-body pre code{background:none;padding:0}
.markdown-body ul,.markdown-body ol{padding-left:24px}
.markdown-body li{margin:4px 0}
.markdown-body blockquote{border-left:4px solid #30363d;padding-left:16px;color:#8b949e;margin:8px 0}
.markdown-body table{border-collapse:collapse;width:100%;margin:12px 0}
.markdown-body th,.markdown-body td{border:1px solid #30363d;padding:8px 12px;text-align:left}
.markdown-body th{background:#161b22}
.markdown-body hr{border:none;border-top:1px solid #30363d;margin:24px 0}
.markdown-body img{max-width:100%}
#search{width:100%;padding:6px 10px;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;
border-radius:6px;font-size:13px;margin-bottom:12px;box-sizing:border-box}
#search:focus{outline:none;border-color:#58a6ff}
#theme-toggle{position:absolute;top:12px;right:12px;background:none;border:none;
color:#8b949e;cursor:pointer;font-size:16px}
body.light{background:#fff;color:#24292f}
body.light #sidebar{background:#f6f8fa;border-color:#d0d7de}
body.light #sidebar a{color:#24292f}
body.light #sidebar a:hover,body.light #sidebar a.active{background:#e2e5e9;color:#0969da}
body.light #sidebar .cat{color:#57606a}
body.light #sidebar h2{color:#0969da}
body.light #search{background:#fff;color:#24292f;border-color:#d0d7de}
body.light .markdown-body h1{color:#24292f;border-color:#d0d7de}
body.light .markdown-body h2{color:#24292f;border-color:#e2e5e9}
body.light .markdown-body h3{color:#24292f}
body.light .markdown-body code{background:#f6f8fa;color:#24292f}
body.light .markdown-body pre{background:#f6f8fa;border-color:#d0d7de}
body.light .markdown-body a{color:#0969da}
body.light .markdown-body blockquote{border-color:#d0d7de;color:#57606a}
body.light .markdown-body th,.markdown-body td{border-color:#d0d7de}
body.light .markdown-body th{background:#f6f8fa}
"""

_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — MD Hub</title>
<style>{css}</style></head><body>
<div id="sidebar">
<button id="theme-toggle" onclick="toggleTheme()">☀</button>
<h2>MD Hub</h2>
<input id="search" type="text" placeholder="Search docs…" oninput="filterDocs(this.value)">
{sidebar}
</div>
<div id="content"><div class="markdown-body">{body}</div></div>
<script>
function filterDocs(q){{
  q=q.toLowerCase();
  document.querySelectorAll('#sidebar a[data-title]').forEach(a=>{{
    a.style.display=a.dataset.title.toLowerCase().includes(q)?'':'none'
  }})
}}
function toggleTheme(){{
  document.body.classList.toggle('light');
  localStorage.setItem('theme',document.body.classList.contains('light')?'light':'dark');
  document.getElementById('theme-toggle').textContent=document.body.classList.contains('light')?'🌙':'☀';
}}
(function(){{if(localStorage.getItem('theme')==='light'){{document.body.classList.add('light');document.getElementById('theme-toggle').textContent='🌙'}}}})()
</script></body></html>"""


def _md_to_html(text):
    """Minimal Markdown-to-HTML renderer (no external deps)."""
    # Remove front-matter
    text = re.sub(r"^---\n.*?\n---\n?", "", text, flags=re.DOTALL)
    html = text

    # Code blocks
    html = re.sub(r"```(\w*)\n(.*?)```", r"<pre><code>\2</code></pre>", html, flags=re.DOTALL)
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

    # Headings
    for i in range(6, 0, -1):
        html = re.sub(rf"^{'#' * i}\s+(.+)$", rf"<h{i}>\1</h{i}>", html, flags=re.MULTILINE)

    # Bold, italic
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # Links
    html = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', html)

    # Horizontal rules
    html = re.sub(r"^---+$", "<hr>", html, flags=re.MULTILINE)

    # Unordered lists
    html = re.sub(r"^[-*+]\s+(.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"(<li>.*?</li>(\n|$))+", lambda m: "<ul>" + m.group(0) + "</ul>", html)

    # Blockquotes
    html = re.sub(r"^>\s?(.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)

    # Paragraphs
    html = re.sub(r"\n\n+", "</p><p>", html)
    html = f"<p>{html}</p>"
    html = re.sub(r"<p>\s*</p>", "", html)
    html = re.sub(r"<p>\s*(<h[1-6]>)", r"\1", html)
    html = re.sub(r"(</h[1-6]>)\s*</p>", r"\1", html)
    html = re.sub(r"<p>\s*(<pre>)", r"\1", html)
    html = re.sub(r"(</pre>)\s*</p>", r"\1", html)
    html = re.sub(r"<p>\s*(<ul>)", r"\1", html)
    html = re.sub(r"(</ul>)\s*</p>", r"\1", html)
    html = re.sub(r"<p>\s*(<hr>)", r"\1", html)
    html = re.sub(r"(<hr>)\s*</p>", r"\1", html)

    return html


def _build_sidebar(hub):
    """Build HTML sidebar with file tree."""
    parts = []
    for cat_name in sorted(os.listdir(hub)):
        cat_dir = os.path.join(hub, cat_name)
        if not os.path.isdir(cat_dir):
            continue
        parts.append(f'<div class="cat">{cat_name.replace("-", " ")}</div>')
        for fname in sorted(os.listdir(cat_dir)):
            if fname == "index.md" or not fname.endswith(".md"):
                continue
            title = fname.replace(".md", "").replace("-", " ").title()
            # Try to read actual title from front-matter
            fpath = os.path.join(cat_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    meta, _ = _parse_frontmatter(f.read())
                    if meta.get("title"):
                        title = meta["title"]
            except Exception:
                pass
            href = f"/{cat_name}/{fname}"
            parts.append(f'<a href="{href}" data-title="{title}">{title}</a>')
    return "\n".join(parts)


def serve_hub(port=3000, path=None, no_open=False):
    """Start a local HTTP server that renders the hub with GitHub-style UI.

    Args:
        port: Port number.
        path: Custom hub root.
        no_open: If True, don't open browser automatically.
    """
    hub = _hub_path(path)
    if not os.path.isdir(hub):
        _error("Hub not found. Run: ath md-organizer init", "NOT_FOUND", 4)

    sidebar_html = _build_sidebar(hub)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            url_path = self.path.strip("/")
            if not url_path:
                url_path = "index.md"
            if not url_path.endswith(".md"):
                url_path += ".md" if "/" not in url_path else "/index.md"

            filepath = os.path.join(hub, url_path)
            if not os.path.isfile(filepath):
                # Try adding index.md to directory paths
                dir_path = os.path.join(hub, url_path.replace(".md", ""))
                if os.path.isdir(dir_path):
                    filepath = os.path.join(dir_path, "index.md")

            if not os.path.isfile(filepath):
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")
                return

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            meta, body = _parse_frontmatter(content)
            title = meta.get("title", url_path.replace(".md", ""))
            body_html = _md_to_html(content)

            # Rebuild sidebar on each request so it stays up to date
            current_sidebar = _build_sidebar(hub)
            page = _PAGE_TEMPLATE.format(
                title=title,
                css=_GITHUB_CSS,
                sidebar=current_sidebar,
                body=body_html,
            )

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))

        def log_message(self, fmt, *args):
            # Suppress default request logging
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)

    if not no_open:
        threading.Timer(0.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

    return server, port


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def run(args):
    """CLI entrypoint for md-organizer tool."""
    cmd = args.md_command

    if cmd == "init":
        result = init_hub(args.path)
        _output({"status": "ok", "data": result})

    elif cmd == "save":
        result = save_document(
            title=args.title,
            content=args.content,
            category=args.category,
            tags=args.tags.split(",") if args.tags else None,
            path=args.path,
            source_file=args.file,
        )
        _output({"status": "ok", "data": result})

    elif cmd == "list":
        result = list_documents(category=args.category, path=args.path)
        _output({"status": "ok", "data": result})

    elif cmd == "search":
        if not args.query:
            _error("--query is required for search", "VALIDATION_ERROR", 3)
        result = search_documents(args.query, path=args.path)
        _output({"status": "ok", "data": result})

    elif cmd == "serve":
        hub = _hub_path(args.path)
        if not os.path.isdir(hub):
            _error("Hub not found. Run: ath md-organizer init", "NOT_FOUND", 4)
        server, port = serve_hub(port=args.port, path=args.path, no_open=args.no_open)
        _output({"status": "ok", "data": {"message": f"Server running at http://127.0.0.1:{port}", "port": port}})
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
