#!/usr/bin/env python3
"""Map RIS fields to understand what data is available."""

# RIS field mappings based on the file analysis
RIS_FIELD_MAPPING = {
    "TY": "Type (always DBASE)",
    "DP": "Database Provider (National Library of Medicine)",
    "PP": "Place of Publication (Bethesda MD)",
    "ID": "Database ID",
    "AB": "Abstract/Brief Summary",
    "AN": "NCT ID", 
    "SF": "Source (ClinicalTrials.gov)",
    "ST": "Short Title",
    "TI": "Full Title",
    "Y1": "First Posted Date",
    "Y2": "Study Start Date",
    "A2": "Secondary Sponsor",
    "C1": "Lead Sponsor/Organization",
    "C2": "Overall Status",
    "C3": "Last Update Posted Date", 
    "C4": "Last Update Submit Date",
    "C5": "Study Type (Interventional/Observational)",
    "C6": "Results Status (Results Posted/No Results Submitted)",
    "C7": "Documents (Study Protocol/Statistical Analysis Plan/Informed Consent Form)",
    "U1": "Other Identifiers (Grant numbers, Registry IDs, etc)",
    "RD": "Retrieval Date",
    "UR": "URL",
    "ER": "End of Record marker"
}

# Fields found in RIS that correspond to missing API sections
RIS_AVAILABLE_DATA = {
    "Basic Info": ["TI", "ST", "AN", "ID", "Y1", "Y2", "C1", "C2", "C3", "C4", "C5"],
    "Abstract": ["AB"],
    "Documents": ["C7"],  # Study Protocol, Statistical Analysis Plan, Informed Consent
    "Results": ["C6"],    # Results Posted/No Results Submitted
    "Other IDs": ["U1"],  # Grant numbers, registry IDs
    "URL": ["UR"]
}

# Missing from RIS compared to API
MISSING_IN_RIS = {
    "annotationSection": [
        "Annotation metadata",
        "Processing timestamps", 
        "Data quality indicators"
    ],
    "documentSection": [
        "Full document contents",
        "Document URLs/links",
        "Document metadata beyond C7 tags"
    ],
    "resultsSection": [
        "Detailed results data",
        "Outcome measures",
        "Participant flow",
        "Baseline characteristics",
        "Adverse events"
    ],
    "protocolSection_details": [
        "Detailed eligibility criteria",
        "Arms and interventions details",
        "Outcome measures",
        "Contacts and locations details",
        "Study design details"
    ]
}

def summarize_ris_coverage():
    """Summarize what's available in RIS vs API."""
    print("RIS FILE DATA COVERAGE ANALYSIS")
    print("=" * 60)
    
    print("\n✓ AVAILABLE IN RIS FILE:")
    for category, fields in RIS_AVAILABLE_DATA.items():
        print(f"\n{category}:")
        for field in fields:
            print(f"  - {field}: {RIS_FIELD_MAPPING[field]}")
    
    print("\n✗ MISSING FROM RIS (but available in API):")
    for section, items in MISSING_IN_RIS.items():
        print(f"\n{section}:")
        for item in items:
            print(f"  - {item}")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("- RIS contains basic metadata and document indicators (C7 field)")
    print("- RIS does NOT contain full document contents")
    print("- RIS does NOT contain detailed results data")
    print("- RIS does NOT contain annotation/processing metadata")
    print("- RIS has limited protocol details compared to API")

if __name__ == "__main__":
    summarize_ris_coverage()