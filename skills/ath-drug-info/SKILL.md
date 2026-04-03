---
name: ath_drug_info
description: Look up medication and drug label information from the OpenFDA database using the CLI Tools Hub drug-info command.
metadata: {"openclaw": {"requires": {"bins": ["ath"]}}}
input_schema:
  type: object
  properties:
    name:
      type: string
      description: Drug brand name or generic name (e.g. "aspirin", "metformin", "lisinopril")
    field:
      type: string
      enum: [indications, warnings, contraindications, dosage, adverse_reactions]
      description: Return a specific field only. Omit to get a full summary.
  required: [name]
---

# Drug Information Lookup

When a user asks about a medication, drug interactions, dosage, warnings, or indications, use this tool to retrieve structured drug label information from the OpenFDA database. No API key required.

## Usage

```bash
# Full drug summary
ath drug-info --name "aspirin"

# Specific field only
ath drug-info --name "metformin" --field indications
ath drug-info --name "lisinopril" --field warnings
ath drug-info --name "ibuprofen" --field dosage
ath drug-info --name "amoxicillin" --field contraindications
ath drug-info --name "atorvastatin" --field adverse_reactions
```

## Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name` | Yes | — | Drug brand name or generic name |
| `--field` | No | None (full summary) | `indications`, `warnings`, `contraindications`, `dosage`, or `adverse_reactions` |

## Output

### Full summary (no `--field`)

```json
{
  "status": "ok",
  "data": {
    "brand_name": ["ASPIRIN"],
    "generic_name": ["ASPIRIN"],
    "manufacturer": ["Bayer HealthCare LLC"],
    "product_type": ["HUMAN OTC DRUG"],
    "route": ["ORAL"],
    "substance_name": ["ASPIRIN"],
    "indications": "Uses temporarily relieves minor aches and pains...",
    "warnings": "Reye's syndrome: Children and teenagers who have...",
    "contraindications": null,
    "dosage": "adults and children 12 years and over...",
    "adverse_reactions": null
  }
}
```

### Specific field

```json
{
  "status": "ok",
  "data": {
    "drug": "METFORMIN HYDROCHLORIDE",
    "field": "indications",
    "value": "Metformin hydrochloride tablets are indicated as an adjunct to diet..."
  }
}
```

## Requirements

- No API key needed — uses the public OpenFDA drug label database
- Install: `pip install cli-tools-hub`
- Internet access required

## When to use

- User asks about a medication's purpose, dosage, or side effects
- User wants to know contraindications or warnings for a drug
- Healthcare AI agent needs structured drug label data
- User asks "what is X used for?" or "what are the warnings for X?"

## When NOT to use

- Drug interaction checking between multiple drugs (use a dedicated interaction API)
- Real-time prescribing decisions (always defer to licensed healthcare professionals)
- Veterinary drugs (OpenFDA covers human drugs only)

## Data source

All data is sourced from the [OpenFDA Drug Label API](https://open.fda.gov/apis/drug/label/), which mirrors FDA-approved drug label information. This is reference data only and should not replace professional medical advice.
