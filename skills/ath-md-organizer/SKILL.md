---
name: ath_md_organizer
description: Organise agent output and files into a browsable Markdown knowledge base with a GitHub-style viewer.
metadata: {"openclaw": {"requires": {"bins": ["ath"]}}}
input_schema:
  type: object
  properties:
    subcommand:
      type: string
      enum: [init, save, list, search, serve]
      description: Subcommand to run
    title:
      type: string
      description: Document title (required for save)
    category:
      type: string
      description: Document category (required for save; optional filter for list)
    content:
      type: string
      description: Markdown content to save (for save subcommand)
    file:
      type: string
      description: File path to read content from (for save subcommand)
    tags:
      type: string
      description: Comma-separated tags (for save subcommand)
    query:
      type: string
      description: Search query (required for search subcommand)
    port:
      type: integer
      description: Port for web viewer (for serve subcommand, default 8080)
    no_open:
      type: boolean
      description: Do not auto-open browser (for serve subcommand)
  required: [subcommand]
---

# Markdown Organizer

When the user wants to save, organise, or browse documents as Markdown files, use this tool. It creates a structured `.md-hub` directory that acts as a local knowledge base with a GitHub-style web viewer.

## Usage

```bash
# Initialise a new hub
ath md-organizer init

# Save content as an organised .md file
ath md-organizer save --title "React Hooks Research" --category research --content "# Findings\n..."

# Save from a file
ath md-organizer save --title "Q4 Report" --category reports --file report.txt

# Save with tags
ath md-organizer save --title "Auth Notes" --category docs --tags "security,api" --content "..."

# List all documents
ath md-organizer list
ath md-organizer list --category research

# Search across documents
ath md-organizer search --query "authentication"

# Start the GitHub-style viewer
ath md-organizer serve
ath md-organizer serve --port 8080
ath md-organizer serve --no-open
```

## Output

All commands return structured JSON:

```json
{
  "status": "ok",
  "data": {
    "file": ".md-hub/research/react-hooks-research.md",
    "title": "React Hooks Research",
    "category": "research",
    "tags": ["react", "hooks"]
  }
}
```

## The Viewer

`ath md-organizer serve` starts a local web server with:

- GitHub-style dark/light themed Markdown rendering
- Sidebar with file tree navigation
- Live search across all documents
- Auto-generated category indexes

## Requirements

- No external dependencies (uses Python standard library only)
- Install: `pip install cli-tools-hub`

## When to use

- User says "save this", "organise this", or "file this"
- User wants to browse saved research or notes
- Agent needs to store search results, converted docs, or analysis output
- User wants a visual overview of collected documents
- After using `ath convert` to convert a file, save the result as organised .md

## When NOT to use

- User wants to edit existing files in place (use a text editor)
- User needs real-time collaboration (use Git + remote)
- User wants cloud storage (this is local only)
