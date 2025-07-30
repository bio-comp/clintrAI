#!/usr/bin/env python3
"""Compare downloaded JSON files with API responses to check data completeness."""

import asyncio
import json
import random
from pathlib import Path
import httpx
from deepdiff import DeepDiff

from clintrai.api.client import create_default_client
from clintrai.api.studies import fetch_study


async def compare_study_data(nct_id: str, local_data_path: Path):
    """Compare local JSON with API response for a single study."""
    # Read local JSON file
    local_file = local_data_path / f"{nct_id}.json"
    if not local_file.exists():
        return {
            "nct_id": nct_id,
            "status": "error",
            "message": f"Local file not found: {local_file}"
        }
    
    with open(local_file, 'r') as f:
        local_data = json.load(f)
    
    # Fetch from API
    client = create_default_client()
    try:
        api_data = await fetch_study(client, nct_id)
        api_dict = api_data.model_dump()
        
        # Compare using DeepDiff
        diff = DeepDiff(local_data, api_dict, ignore_order=True, verbose_level=2)
        
        return {
            "nct_id": nct_id,
            "status": "success",
            "has_differences": bool(diff),
            "differences": diff.to_dict() if diff else None,
            "local_keys": set(local_data.keys()),
            "api_keys": set(api_dict.keys()),
            "missing_in_local": set(api_dict.keys()) - set(local_data.keys()),
            "missing_in_api": set(local_data.keys()) - set(api_dict.keys())
        }
    except Exception as e:
        return {
            "nct_id": nct_id,
            "status": "error",
            "message": str(e)
        }
    finally:
        await client.close()


async def main():
    """Main function to compare 10 random studies."""
    data_path = Path("/home/mike/repos/clinTrAI/data/studies")
    
    # Get all available NCT IDs
    all_files = list(data_path.glob("NCT*.json"))
    if len(all_files) < 10:
        print(f"Error: Only {len(all_files)} files found, need at least 10")
        return
    
    # Select 10 random studies
    random_files = random.sample(all_files, 10)
    nct_ids = [f.stem for f in random_files]
    
    print(f"Comparing {len(nct_ids)} random studies...")
    print(f"Selected NCT IDs: {', '.join(nct_ids)}")
    print("-" * 80)
    
    # Compare each study
    results = []
    for nct_id in nct_ids:
        print(f"\nComparing {nct_id}...")
        result = await compare_study_data(nct_id, data_path)
        results.append(result)
        
        if result['status'] == 'success':
            if result['has_differences']:
                print(f"  ⚠️  Differences found!")
                if result['missing_in_local']:
                    print(f"  Missing in local: {result['missing_in_local']}")
                if result['missing_in_api']:
                    print(f"  Missing in API: {result['missing_in_api']}")
            else:
                print(f"  ✓ No differences found")
        else:
            print(f"  ❌ Error: {result['message']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r['status'] == 'success']
    with_diffs = [r for r in successful if r['has_differences']]
    
    print(f"Total studies compared: {len(results)}")
    print(f"Successful comparisons: {len(successful)}")
    print(f"Studies with differences: {len(with_diffs)}")
    print(f"Studies without differences: {len(successful) - len(with_diffs)}")
    
    # Save detailed results
    output_file = Path("comparison_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())