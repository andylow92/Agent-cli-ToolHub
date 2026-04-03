"""Drug info tool — Look up medication information via the OpenFDA API."""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.fda.gov/drug/label.json"


def _output(data, file=sys.stdout):
    print(json.dumps(data, indent=2), file=file)


def _error(message, code, exit_code):
    _output({"status": "error", "error": message, "code": code}, file=sys.stderr)
    sys.exit(exit_code)


def _first(lst):
    """Return first item of a list, or None."""
    if lst and isinstance(lst, list):
        return lst[0]
    return lst


def get_drug_info(name: str, field: str = None) -> dict:
    """Look up drug/medication information from OpenFDA drug label database.

    Args:
        name: Drug brand name or generic name (e.g., "aspirin", "metformin").
        field: Optional specific field to return. One of: indications, warnings,
               contraindications, dosage, adverse_reactions. If omitted, returns
               a summary of all available fields.

    Returns:
        dict with structured drug information.
    """
    VALID_FIELDS = {"indications", "warnings", "contraindications", "dosage", "adverse_reactions"}
    if field and field not in VALID_FIELDS:
        _error(
            f"Invalid field '{field}'. Choose from: {', '.join(sorted(VALID_FIELDS))}",
            "VALIDATION_ERROR",
            3,
        )

    # Search by brand name OR generic name
    search = f'openfda.brand_name:"{name}"+OR+openfda.generic_name:"{name}"'
    params = urllib.parse.urlencode({"search": search, "limit": 1})
    url = f"{BASE_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            _error(
                f"No drug records found for '{name}'. Try a different name or spelling.",
                "NOT_FOUND",
                1,
            )
        body = e.read().decode()
        try:
            detail = json.loads(body).get("error", {}).get("message", body)
        except json.JSONDecodeError:
            detail = body
        _error(f"API error {e.code}: {detail}", "API_ERROR", 1)
    except urllib.error.URLError as e:
        _error(f"Network error: {e.reason}", "API_ERROR", 1)

    results = data.get("results", [])
    if not results:
        _error(
            f"No drug records found for '{name}'. Try a different name or spelling.",
            "NOT_FOUND",
            1,
        )

    label = results[0]
    openfda = label.get("openfda", {})

    FIELD_MAP = {
        "indications": "indications_and_usage",
        "warnings": "warnings",
        "contraindications": "contraindications",
        "dosage": "dosage_and_administration",
        "adverse_reactions": "adverse_reactions",
    }

    if field:
        raw = label.get(FIELD_MAP[field])
        if not raw:
            _error(
                f"Field '{field}' is not available for '{name}' in this record.",
                "FIELD_MISSING",
                1,
            )
        return {
            "drug": _first(openfda.get("brand_name")) or _first(openfda.get("generic_name")) or name,
            "field": field,
            "value": _first(raw),
        }

    result = {
        "brand_name": openfda.get("brand_name", []),
        "generic_name": openfda.get("generic_name", []),
        "manufacturer": openfda.get("manufacturer_name", []),
        "product_type": openfda.get("product_type", []),
        "route": openfda.get("route", []),
        "substance_name": openfda.get("substance_name", []),
    }

    for friendly, raw_key in FIELD_MAP.items():
        raw = label.get(raw_key)
        result[friendly] = _first(raw) if raw else None

    return result


def run(args):
    """CLI entrypoint for drug-info tool."""
    result = get_drug_info(args.name, getattr(args, "field", None))
    _output({"status": "ok", "data": result})
