#!/usr/bin/env python3
"""Validate and enrich bibliography entries using Crossref API.

This script checks DOI validity and enriches bibliographic entries with
additional metadata from Crossref where possible.
"""

from pathlib import Path
import re
import sys
import time
from typing import Any

import requests


def validate_doi(doi: str) -> bool:
    """Validate a DOI by checking if it resolves correctly."""
    if not doi:
        return False

    # Clean DOI if it's a URL
    if doi.startswith("http"):
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

    try:
        response = requests.get(f"https://api.crossref.org/works/{doi}", timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False


def enrich_from_crossref(doi: str) -> dict[str, Any] | None:
    """Enrich bibliographic entry with data from Crossref API."""
    if not doi:
        return None

    # Clean DOI if it's a URL
    if doi.startswith("http"):
        doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

    try:
        response = requests.get(f"https://api.crossref.org/works/{doi}", timeout=10)
        if response.status_code == 200:
            data = response.json()["message"]
            enriched = {}

            # Extract useful fields
            if data.get("title"):
                enriched["title"] = data["title"][0]

            if "author" in data:
                # Format authors as "Last Name, First Name" or "Last Name et al."
                authors = []
                for author in data["author"][:3]:  # Limit to first 3 authors
                    if "family" in author:
                        if "given" in author:
                            authors.append(f"{author['family']}, {author['given']}")
                        else:
                            authors.append(author["family"])

                if len(data["author"]) > 3:
                    authors.append("et al.")

                enriched["author"] = " and ".join(authors)

            if "issued" in data and "date-parts" in data["issued"]:
                enriched["year"] = str(data["issued"]["date-parts"][0][0])

            if data.get("container-title"):
                enriched["journal"] = data["container-title"][0]

            if "volume" in data:
                enriched["volume"] = str(data["volume"])

            if "page" in data:
                enriched["pages"] = data["page"]

            if "publisher" in data:
                enriched["publisher"] = data["publisher"]

            return enriched
    except requests.RequestException as e:
        print(f"Error enriching from Crossref: {e}")
        return None

    return None


def parse_bibtex_entry(entry: str) -> dict[str, str]:
    """Parse a BibTeX entry into a dictionary of fields."""
    # Extract entry type and key
    entry_type_match = re.match(r"@(\w+)\{([^,]+),", entry.strip())
    if not entry_type_match:
        return {}

    entry_type = entry_type_match.group(1)
    entry_key = entry_type_match.group(2)

    # Extract fields
    fields = {"entry_type": entry_type, "entry_key": entry_key}
    field_pattern = r"(\w+)\s*=\s*\{([^}]+)\}"
    for match in re.finditer(field_pattern, entry):
        field_name = match.group(1).lower()
        field_value = match.group(2).strip()
        fields[field_name] = field_value

    return fields


def format_bibtex_entry(fields: dict[str, str]) -> str:
    """Format a dictionary of fields back into a BibTeX entry."""
    entry_type = fields.get("entry_type", "article")
    entry_key = fields.get("entry_key", "unknown")

    # Format the entry
    entry_lines = [f"@{entry_type}{{{entry_key},"]

    # Add fields in a consistent order
    field_order = [
        "title",
        "author",
        "journal",
        "year",
        "volume",
        "number",
        "pages",
        "doi",
        "url",
        "publisher",
    ]

    # Add ordered fields first
    for field in field_order:
        if fields.get(field):
            entry_lines.append(f"  {field} = {{{fields[field]}}},")

    # Add any remaining fields
    for field, value in fields.items():
        if (
            field not in ["entry_type", "entry_key"]
            and value
            and field not in field_order
        ):
            entry_lines.append(f"  {field} = {{{value}}},")

    # Close the entry
    entry_lines[-1] = entry_lines[-1].removesuffix(",")  # Remove trailing comma

    entry_lines.append("}")

    return "\n".join(entry_lines)


def process_bibliography_file(input_file: Path, output_file: Path) -> None:
    """Process a bibliography file, validating DOIs and enriching entries."""
    print(f"Processing bibliography file: {input_file}")

    # Read the input file
    with open(input_file) as f:
        content = f.read()

    # Split into entries
    entries = re.split(r"\n(?=@)", content)

    processed_entries = []
    enriched_count = 0
    validated_count = 0

    for i, entry in enumerate(entries):
        if not entry.strip():
            continue

        # Parse the entry
        fields = parse_bibtex_entry(entry)
        if not fields:
            processed_entries.append(entry)
            continue

        # Check for DOI
        doi = fields.get("doi", "")
        if doi:
            # Validate DOI
            if validate_doi(doi):
                validated_count += 1
                print(f"  ✓ Valid DOI for {fields.get('entry_key', 'unknown')}: {doi}")

                # Enrich from Crossref
                enriched_data = enrich_from_crossref(doi)
                if enriched_data:
                    # Update fields with enriched data (don't overwrite existing)
                    for key, value in enriched_data.items():
                        if key not in fields or not fields[key]:
                            fields[key] = value

                    enriched_count += 1
                    print("    ↻ Enriched with Crossref data")
            else:
                print(
                    f"  ✗ Invalid DOI for {fields.get('entry_key', 'unknown')}: {doi}"
                )

        # Format the entry back
        processed_entry = format_bibtex_entry(fields)
        processed_entries.append(processed_entry)

        # Rate limiting - be respectful to Crossref API
        if doi and i % 5 == 4:  # Every 5th entry, pause
            time.sleep(1)

    # Write to output file
    with open(output_file, "w") as f:
        f.write("\n\n".join(processed_entries) + "\n")

    print(f"\nProcessed {len(processed_entries)} entries:")
    print(f"  - Validated {validated_count} DOIs")
    print(f"  - Enriched {enriched_count} entries with Crossref data")
    print(f"  - Output written to {output_file}")


def main():
    """Main function to validate and enrich bibliography."""
    # Process the references file
    input_path = Path("paper/references_corrected.bib")
    output_path = Path("paper/references_enriched.bib")

    if input_path.exists():
        process_bibliography_file(input_path, output_path)
    else:
        print(f"Input file not found: {input_path}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
