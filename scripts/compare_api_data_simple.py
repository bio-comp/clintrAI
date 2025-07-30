#!/usr/bin/env python3
"""Compare downloaded JSON files with API responses to check data completeness."""

import asyncio
import json
import random
from pathlib import Path

from clintrai.api.hybrid_client import create_hybrid_client
from clintrai.api.studies import fetch_study


def get_all_keys(obj: dict | list, prefix: str = "") -> set[str]:
    """Recursively get all keys from a nested dictionary."""
    keys = set()
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            keys.update(get_all_keys(value, full_key))
    elif isinstance(obj, list) and obj:
        # Check first item of list for structure
        keys.update(get_all_keys(obj[0], f"{prefix}[0]"))
    
    return keys


async def compare_study_data(nct_id: str, local_data_path: Path) -> dict[str, str | int | float | list[str]]:
    """Compare local JSON with API response for a single study."""
    # Read local JSON file
    local_file = local_data_path / f"{nct_id}.json"
    if not local_file.exists():
        return {
            "nct_id": nct_id,
            "status": "error",
            "message": f"Local file not found: {local_file}"
        }
    
    local_data = json.loads(local_file.read_text())
    
    # Fetch from API using hybrid client to avoid TLS fingerprinting
    client = create_hybrid_client()
    try:
        api_response = await fetch_study(client, nct_id)
        api_data = json.loads(api_response.model_dump_json())
        
        # Get all keys recursively
        local_keys = get_all_keys(local_data)
        api_keys = get_all_keys(api_data)
        
        # Compare top-level structure
        local_top = set(local_data.keys()) if isinstance(local_data, dict) else set()
        api_top = set(api_data.keys()) if isinstance(api_data, dict) else set()
        
        # Calculate differences
        missing_in_local = api_keys - local_keys
        missing_in_api = local_keys - api_keys
        
        # Check data sizes (rough comparison)
        local_size = len(json.dumps(local_data))
        api_size = len(json.dumps(api_data))
        size_diff_pct = abs(local_size - api_size) / max(local_size, api_size) * 100
        
        return {
            "nct_id": nct_id,
            "status": "success",
            "local_top_keys": sorted(local_top),
            "api_top_keys": sorted(api_top),
            "missing_top_in_local": sorted(api_top - local_top),
            "missing_top_in_api": sorted(local_top - api_top),
            "total_keys_local": len(local_keys),
            "total_keys_api": len(api_keys),
            "missing_keys_in_local": len(missing_in_local),
            "missing_keys_in_api": len(missing_in_api),
            "local_size_bytes": local_size,
            "api_size_bytes": api_size,
            "size_difference_pct": round(size_diff_pct, 2),
            "sample_missing_in_local": sorted(list(missing_in_local)[:10]),
            "sample_missing_in_api": sorted(list(missing_in_api)[:10])
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
    
    print(f"Comparing {len(nct_ids)} random studies with API...")
    print(f"Selected NCT IDs: {', '.join(nct_ids)}")
    print("-" * 80)
    
    # Compare each study
    results = []
    for i, nct_id in enumerate(nct_ids, 1):
        print(f"\n[{i}/10] Comparing {nct_id}...")
        result = await compare_study_data(nct_id, data_path)
        results.append(result)
        
        if result['status'] == 'success':
            print("  ✓ Comparison complete")
            print(f"  - Local keys: {result['total_keys_local']}")
            print(f"  - API keys: {result['total_keys_api']}")
            print(f"  - Size difference: {result['size_difference_pct']}%")
            
            if result['missing_top_in_local']:
                print(f"  ⚠️  Missing top-level keys in local: {result['missing_top_in_local']}")
            if result['missing_top_in_api']:
                print(f"  ⚠️  Missing top-level keys in API: {result['missing_top_in_api']}")
        else:
            print(f"  ❌ Error: {result['message']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful = [r for r in results if r['status'] == 'success']
    
    if successful:
        avg_size_diff = sum(r['size_difference_pct'] for r in successful) / len(successful)
        avg_missing_in_local = sum(r['missing_keys_in_local'] for r in successful) / len(successful)
        avg_missing_in_api = sum(r['missing_keys_in_api'] for r in successful) / len(successful)
        
        print(f"Total studies compared: {len(results)}")
        print(f"Successful comparisons: {len(successful)}")
        print(f"Failed comparisons: {len(results) - len(successful)}")
        print(f"\nAverage size difference: {avg_size_diff:.2f}%")
        print(f"Average keys missing in local: {avg_missing_in_local:.1f}")
        print(f"Average keys missing in API: {avg_missing_in_api:.1f}")
        
        # Check if all have same structure
        all_local_tops = [set(r['local_top_keys']) for r in successful]
        all_api_tops = [set(r['api_top_keys']) for r in successful]
        
        if all(s == all_local_tops[0] for s in all_local_tops):
            print("\n✓ All local files have consistent top-level structure")
            print(f"  Top-level keys: {sorted(all_local_tops[0])}")
        else:
            print("\n⚠️  Local files have inconsistent top-level structure")
            
        if all(s == all_api_tops[0] for s in all_api_tops):
            print("\n✓ All API responses have consistent top-level structure")
            print(f"  Top-level keys: {sorted(all_api_tops[0])}")
        else:
            print("\n⚠️  API responses have inconsistent top-level structure")
    
    # Save detailed results
    output_file = Path("comparison_results.json")
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())