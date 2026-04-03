---
name: ath_convert
description: Convert between file formats (CSV, JSON, XML, HTML, Markdown, PDF, XLSX) using the CLI Tools Hub.
metadata: {"openclaw": {"requires": {"bins": ["ath"]}}}
input_schema:
  type: object
  properties:
    input:
      type: string
      description: Input file path
    to:
      type: string
      description: Target format (e.g. json, csv, xml, html, text)
    output:
      type: string
      description: Output file path (defaults to stdout; required for binary formats)
  required: [input, to]
---

# File Format Converter

When the user needs to convert a file between supported formats, use this tool.

## Usage

```bash
ath convert --input data.csv --to json
ath convert --input page.html --to text
ath convert --input data.json --to csv --output data.csv
ath convert --input doc.md --to html
ath convert --input config.xml --to json
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--input` | Yes | — | Input file path |
| `--to` | Yes | — | Target format |
| `--output` | No | stdout | Output file path (required for binary) |

## Supported Conversions

| From | To |
|------|-----|
| CSV | JSON, TSV |
| TSV | JSON |
| JSON | CSV, XML |
| HTML | Text, JSON (tables) |
| Markdown | Text, HTML |
| XML | JSON |
| PDF | Text, JSON (requires PyPDF2) |
| XLSX | JSON, CSV (requires openpyxl) |

## Output

Returns JSON with converted data to stdout.

```json
{
  "status": "ok",
  "data": {
    "data": [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}],
    "rows": 2,
    "columns": ["name", "age"]
  }
}
```

## Requirements

- Install: `pip install cli-tools-hub`
- For PDF: `pip install cli-tools-hub[pdf]`
- For XLSX: `pip install cli-tools-hub[xlsx]`

## When to use

- User asks to convert a CSV to JSON or vice versa
- User needs to extract text from HTML or Markdown
- User wants to parse XML into JSON
- User needs to read data from a PDF or spreadsheet

## When NOT to use

- Image format conversion (PNG, JPG, etc.)
- Audio/video conversion
- Converting between programming languages
