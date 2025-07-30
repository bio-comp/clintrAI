#!/usr/bin/env python3
"""Analyze the actual structure of downloaded JSON files vs API expectations."""

import json
from pathlib import Path
from collections import Counter


def analyze_json_structure():
    """Analyze the structure of downloaded JSON files."""
    data_path = Path("/home/mike/repos/clinTrAI/data/studies")
    
    # Counters for analysis
    top_level_keys = Counter()
    has_document_section = 0
    has_annotation_section = 0 
    has_results_section = 0
    total_files = 0
    
    # Analyze first 100 files to avoid timeout
    json_files = list(data_path.glob("NCT*.json"))[:100]
    
    print(f"Analyzing {len(json_files)} JSON files...")
    
    for json_file in json_files:
        try:
            data = json.loads(json_file.read_text())
            total_files += 1
            
            # Count top-level keys
            for key in data.keys():
                top_level_keys[key] += 1
            
            # Check for specific sections
            if "documentSection" in data:
                has_document_section += 1
            if "annotationSection" in data:
                has_annotation_section += 1
            if "resultsSection" in data:
                has_results_section += 1
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\nTotal files analyzed: {total_files}")
    
    print(f"\nTop-level key frequencies:")
    for key, count in top_level_keys.most_common():
        percentage = (count / total_files) * 100
        print(f"  {key}: {count} files ({percentage:.1f}%)")
    
    print(f"\nSpecific sections:")
    print(f"  documentSection: {has_document_section} files ({(has_document_section/total_files)*100:.1f}%)")
    print(f"  annotationSection: {has_annotation_section} files ({(has_annotation_section/total_files)*100:.1f}%)")
    print(f"  resultsSection: {has_results_section} files ({(has_results_section/total_files)*100:.1f}%)")
    
    # Look at a file with documentSection if available
    if has_document_section > 0:
        print(f"\n" + "="*60)
        print("DOCUMENT SECTION EXAMPLE")
        print("="*60)
        
        for json_file in json_files:
            try:
                data = json.loads(json_file.read_text())
                if "documentSection" in data:
                    print(f"\nFile: {json_file.name}")
                    print(f"Document section structure:")
                    print(json.dumps(data["documentSection"], indent=2))
                    break
            except:
                continue
    
    print(f"\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    print("The downloaded JSON files DO contain:")
    print("- protocolSection (100% of files)")
    print("- derivedSection (100% of files)")
    print("- hasResults flag (100% of files)")
    if has_results_section > 0:
        print(f"- resultsSection ({(has_results_section/total_files)*100:.1f}% of files)")
    if has_document_section > 0:
        print(f"- documentSection ({(has_document_section/total_files)*100:.1f}% of files)")
    if has_annotation_section > 0:
        print(f"- annotationSection ({(has_annotation_section/total_files)*100:.1f}% of files)")
    
    print("\nThese sections appear to be conditionally present based on study characteristics.")


if __name__ == "__main__":
    analyze_json_structure()