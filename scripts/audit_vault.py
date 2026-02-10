#!/usr/bin/env python3
"""
Vault Ingestion Artifacts Audit Script
Validates meta indexes, PDF provenance, and extracted text quality.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import re

# Configuration
VAULT_ROOT = Path("Vault/00-System")
META_DIR = VAULT_ROOT / "Indexes" / "meta"
STAGING_DIR = VAULT_ROOT / "Staging"
CORE_RULEBOOKS = Path("Core Rulebooks")

# Results storage
audit_results = {
    "meta_issues": [],
    "source_decisions": [],
    "summary": {},
    "timestamp": datetime.utcnow().isoformat() + "Z"
}

def validate_meta_json(meta_path):
    """Validate meta JSON structure and required fields."""
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        required_keys = ["sourceId", "title", "path_mnt", "pages", "extractedAt"]
        missing = [k for k in required_keys if k not in data]

        if missing:
            return {"valid": False, "error": f"Missing keys: {missing}", "data": data}

        # Type validation
        if not isinstance(data["sourceId"], str) or not data["sourceId"]:
            return {"valid": False, "error": "sourceId must be non-empty string", "data": data}

        if not isinstance(data["pages"], int) or data["pages"] <= 0:
            return {"valid": False, "error": f"pages must be positive int, got {data['pages']}", "data": data}

        return {"valid": True, "data": data}

    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"JSON parse error: {e}", "data": None}
    except Exception as e:
        return {"valid": False, "error": f"Read error: {e}", "data": None}


def check_pdf_existence(path_mnt):
    """Check if PDF exists, trying multiple path translations."""
    # Original path
    if Path(path_mnt).exists():
        return str(Path(path_mnt)), True

    # Try translating /mnt/f/ to current drive
    if path_mnt.startswith("/mnt/f/"):
        local_path = path_mnt.replace("/mnt/f/", "f:/").replace("/", "\\\\")
        if Path(local_path).exists():
            return local_path, True

        # Try relative to current dir
        relative_path = path_mnt.replace("/mnt/f/DnD-3.5/", "")
        if Path(relative_path).exists():
            return relative_path, True

    return path_mnt, False


def count_pdf_pages(pdf_path):
    """Count PDF pages using PyPDF2 if available."""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)
    except ImportError:
        return None  # PyPDF2 not available
    except Exception as e:
        return f"ERROR: {e}"


def audit_extracted_pages(source_id, expected_pages):
    """Audit extracted page text files in Staging."""
    staging_path = STAGING_DIR / source_id / "pages"

    if not staging_path.exists():
        return {
            "found": False,
            "page_files": [],
            "coverage": "none",
            "quality_flags": []
        }

    # List all .txt files
    page_files = sorted(staging_path.glob("*.txt"))
    page_numbers = []

    for pf in page_files:
        # Extract page number (e.g., 0001.txt -> 1)
        match = re.match(r"(\\d+)\\.txt", pf.name)
        if match:
            page_numbers.append(int(match.group(1)))

    # Check coverage
    if not page_numbers:
        coverage = "none"
    else:
        min_page = min(page_numbers)
        max_page = max(page_numbers)
        gaps = set(range(min_page, max_page + 1)) - set(page_numbers)

        if gaps:
            coverage = f"gaps (missing: {sorted(gaps)[:10]})"
        elif max_page == expected_pages:
            coverage = "complete (1-indexed)"
        elif max_page == expected_pages - 1:
            coverage = "complete (0-indexed)"
        else:
            coverage = f"partial ({min_page}-{max_page} vs expected {expected_pages})"

    # Quality sampling (first 5 pages)
    quality_flags = []
    empty_count = 0
    garbled_count = 0

    for pf in page_files[:5]:
        try:
            content = pf.read_text(encoding='utf-8')

            if len(content.strip()) < 20:
                empty_count += 1

            # Garbled heuristic: >30% non-ASCII printable
            non_ascii = sum(1 for c in content if ord(c) > 127 or not c.isprintable())
            if len(content) > 0 and non_ascii / len(content) > 0.3:
                garbled_count += 1

        except UnicodeDecodeError:
            quality_flags.append("encoding_error")

    if empty_count >= 3:
        quality_flags.append("high_empty_rate")
    if garbled_count >= 3:
        quality_flags.append("high_garbled_rate")

    # Raw vs processed heuristic
    sample_content = page_files[0].read_text(encoding='utf-8') if page_files else ""
    if "[[" in sample_content or "#" in sample_content[:100]:
        quality_flags.append("appears_processed")
    else:
        quality_flags.append("appears_raw")

    return {
        "found": True,
        "page_files": len(page_files),
        "coverage": coverage,
        "quality_flags": quality_flags
    }


def classify_reuse_decision(source_audit):
    """Classify reuse decision based on audit results."""
    meta_ok = source_audit["meta_valid"]
    pdf_exists = source_audit["pdf_exists"]
    pages_match = source_audit.get("pages_match", False)
    extracted_ok = source_audit.get("extracted_text", {}).get("found", False)
    coverage_ok = "complete" in source_audit.get("extracted_text", {}).get("coverage", "")
    quality_clean = not any(
        flag in source_audit.get("extracted_text", {}).get("quality_flags", [])
        for flag in ["high_empty_rate", "high_garbled_rate", "encoding_error"]
    )

    notes = []

    if not meta_ok:
        decision = "rerun_recommended"
        notes.append("meta validation failed")
    elif not pdf_exists:
        decision = "rerun_recommended"
        notes.append("PDF not found")
    elif source_audit.get("pages_pdf") == "ERROR" or (pages_match == False and source_audit.get("pages_diff", 0) > 5):
        decision = "rerun_recommended"
        notes.append("severe page count mismatch or PDF read error")
    elif not extracted_ok:
        decision = "reuse_meta_only"
        notes.append("extracted text not found")
    elif not coverage_ok:
        decision = "reuse_meta_only"
        notes.append("incomplete page coverage")
    elif not quality_clean:
        decision = "reuse_meta_only"
        notes.append("quality concerns: " + ", ".join(source_audit["extracted_text"]["quality_flags"]))
    else:
        decision = "reuse_strong"
        notes.append("all checks passed")

    return decision, notes


# Main audit execution
print("=== VAULT INGESTION ARTIFACTS AUDIT ===")
print(f"Started: {audit_results['timestamp']}")
print()

# Check A: Meta Index Integrity
print("[A] Scanning meta index files...")
meta_files = list(META_DIR.glob("*.json"))
print(f"Found {len(meta_files)} meta JSON files")

source_ids = {}
path_duplicates = defaultdict(list)
malformed_count = 0

for meta_file in meta_files:
    result = validate_meta_json(meta_file)

    if not result["valid"]:
        malformed_count += 1
        audit_results["meta_issues"].append({
            "file": str(meta_file),
            "error": result["error"]
        })
        print(f"  ✗ {meta_file.name}: {result['error']}")
    else:
        data = result["data"]
        source_id = data["sourceId"]

        # Check uniqueness
        if source_id in source_ids:
            audit_results["meta_issues"].append({
                "type": "duplicate_sourceId",
                "sourceId": source_id,
                "files": [source_ids[source_id], str(meta_file)]
            })
            print(f"  ⚠ Duplicate sourceId: {source_id}")
        else:
            source_ids[source_id] = str(meta_file)

        # Track path duplicates
        path_duplicates[data["path_mnt"]].append(source_id)

# Report path duplicates
duplicate_paths = {k: v for k, v in path_duplicates.items() if len(v) > 1}
if duplicate_paths:
    print(f"  ⚠ Found {len(duplicate_paths)} paths with multiple sourceIds:")
    for path, ids in list(duplicate_paths.items())[:5]:
        print(f"    {path}: {ids}")
    audit_results["meta_issues"].append({
        "type": "duplicate_paths",
        "count": len(duplicate_paths),
        "examples": {k: v for k, v in list(duplicate_paths.items())[:3]}
    })

print(f"  Meta integrity: {len(source_ids)} valid, {malformed_count} malformed")
print()

# Check B & C: PDF provenance and extracted text
print("[B+C] Auditing PDF provenance and extracted text...")
pdf_found = 0
pdf_missing = 0
pages_match = 0
pages_mismatch = 0

for source_id, meta_file in source_ids.items():
    result = validate_meta_json(meta_file)
    data = result["data"]

    # Check PDF
    resolved_path, pdf_exists = check_pdf_existence(data["path_mnt"])
    pdf_pages = None

    if pdf_exists:
        pdf_found += 1
        pdf_pages = count_pdf_pages(resolved_path)

        if pdf_pages and isinstance(pdf_pages, int):
            if pdf_pages == data["pages"]:
                pages_match += 1
                match_status = True
                diff = 0
            else:
                pages_mismatch += 1
                match_status = False
                diff = abs(pdf_pages - data["pages"])
        else:
            match_status = None
            diff = None
    else:
        pdf_missing += 1
        match_status = None
        diff = None

    # Check extracted text
    extracted = audit_extracted_pages(source_id, data["pages"])

    # Build source audit record
    source_audit = {
        "sourceId": source_id,
        "title": data["title"],
        "path_mnt": data["path_mnt"],
        "pages_meta": data["pages"],
        "pdf_exists": pdf_exists,
        "pdf_path_resolved": resolved_path if pdf_exists else None,
        "pages_pdf": pdf_pages,
        "pages_match": match_status,
        "pages_diff": diff,
        "meta_valid": True,
        "extracted_text": extracted
    }

    # Classify decision
    decision, notes = classify_reuse_decision(source_audit)

    source_audit["decision"] = decision
    source_audit["notes"] = "; ".join(notes)

    audit_results["source_decisions"].append(source_audit)

print(f"  PDFs found: {pdf_found}/{len(source_ids)}")
print(f"  Page counts: {pages_match} match, {pages_mismatch} mismatch")
print()

# Summary
print("[D] Classification summary:")
decision_counts = defaultdict(int)
for sd in audit_results["source_decisions"]:
    decision_counts[sd["decision"]] += 1

for decision, count in sorted(decision_counts.items()):
    print(f"  {decision}: {count}")

audit_results["summary"] = {
    "total_sources": len(source_ids),
    "malformed_meta": malformed_count,
    "pdf_found": pdf_found,
    "pdf_missing": pdf_missing,
    "pages_match": pages_match,
    "pages_mismatch": pages_mismatch,
    "decisions": dict(decision_counts)
}

# Write REUSE_DECISION.json
output_path = Path("REUSE_DECISION.json")
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(audit_results, f, indent=2)

print()
print(f"✓ Audit complete. Results written to {output_path}")
print(f"  Total sources audited: {len(source_ids)}")
print(f"  Reuse strong: {decision_counts.get('reuse_strong', 0)}")
print(f"  Reuse meta only: {decision_counts.get('reuse_meta_only', 0)}")
print(f"  Rerun recommended: {decision_counts.get('rerun_recommended', 0)}")
