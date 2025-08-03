# clintrai/metaflow/harmonization.py
"""Data harmonization logic for clinical trials pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import polars as pl
from loguru import logger

from clintrai.models.types import (
    DataSource, 
    DeduplicationStrategy, 
    CSVFieldName, 
    JSONSourceField,
    HarmonizedFieldName,
)
from clintrai.processing.preparation import prepare_csv_df, prepare_json_df
from clintrai.processing.schema import OUTPUT_SCHEMA, finalize_and_enforce_schema
from clintrai.processing.strategies import (
    apply_csv_priority_coalescing,
    apply_json_priority_coalescing,
    apply_merge_coalescing,
)


def analyze_overlap(csv_path: Path, json_dir: Path) -> dict[str, any]:
    """
    Analyze overlap between CSV and JSON data sources.
    
    Args:
        csv_path: Path to CSV file
        json_dir: Path to JSON directory
        
    Returns:
        dict: Statistics about data overlap
    """
    logger.info("Analyzing data overlap between CSV and JSON sources")
    
    # Get NCT IDs from CSV using enum for column name
    csv_lf = pl.scan_csv(csv_path)
    csv_nct_ids = set(
        csv_lf.select(CSVFieldName.NCT_NUMBER.value)
        .collect()
        .get_column(CSVFieldName.NCT_NUMBER.value)
        .to_list()
    )
    
    # Get NCT IDs from JSON files
    json_files = list(json_dir.glob("NCT*.json"))
    json_nct_ids = {f.stem for f in json_files}
    
    # Calculate overlap
    overlap = csv_nct_ids & json_nct_ids
    csv_only = csv_nct_ids - json_nct_ids
    json_only = json_nct_ids - overlap
    
    stats = {
        "csv_total": len(csv_nct_ids),
        "json_total": len(json_nct_ids),
        "overlap_count": len(overlap),
        "csv_only_count": len(csv_only),
        "json_only_count": len(json_only),
        "overlap_percentage": (
            (len(overlap) / len(csv_nct_ids)) * 100 
            if csv_nct_ids else 0
        ),
        "csv_nct_ids": csv_nct_ids,
        "json_nct_ids": json_nct_ids,
        "overlap": overlap,
        "csv_only": csv_only,
        "json_only": json_only,
    }
    
    logger.info(
        f"Found {stats['csv_total']:,} CSV studies, "
        f"{stats['json_total']:,} JSON studies, "
        f"{stats['overlap_count']:,} overlapping"
    )
    
    return stats


def get_strategy_config(strategy: DeduplicationStrategy) -> dict[str, any]:
    """
    Get configuration for deduplication strategy.
    
    Args:
        strategy: DeduplicationStrategy enum
        
    Returns:
        dict: Configuration with coalesce function and source logic
    """
    strategies = {
        DeduplicationStrategy.JSON_PRIORITY: {
            "coalesce_func": apply_json_priority_coalescing,
            "source_logic": pl.when(pl.col(JSONSourceField.JSON_OFFICIAL_TITLE.value).is_not_null())
            .then(pl.lit(DataSource.JSON_PRIORITY.value))
            .otherwise(pl.lit(DataSource.CSV_ONLY.value)),
        },
        DeduplicationStrategy.CSV_PRIORITY: {
            "coalesce_func": apply_csv_priority_coalescing,
            "source_logic": pl.when(pl.col(HarmonizedFieldName.TITLE.value).is_not_null())
            .then(pl.lit(DataSource.CSV_PRIORITY.value))
            .otherwise(pl.lit(DataSource.JSON_ONLY.value)),
        },
        DeduplicationStrategy.MERGE_ALL: {
            "coalesce_func": apply_merge_coalescing,
            "source_logic": pl.when(
                pl.col(JSONSourceField.JSON_OFFICIAL_TITLE.value).is_not_null() 
                & pl.col(HarmonizedFieldName.TITLE.value).is_not_null()
            )
            .then(pl.lit(DataSource.MERGED.value))
            .when(pl.col(JSONSourceField.JSON_OFFICIAL_TITLE.value).is_not_null())
            .then(pl.lit(DataSource.JSON_ONLY.value))
            .otherwise(pl.lit(DataSource.CSV_ONLY.value)),
        },
    }
    
    return strategies[strategy]


def harmonize_data(
    csv_path: Path, 
    json_dir: Path, 
    overlap_stats: dict[str, any], 
    strategy: DeduplicationStrategy
) -> tuple[pl.DataFrame, dict[str, any]]:
    """
    Harmonize CSV and JSON data using selected deduplication strategy.
    
    Args:
        csv_path: Path to CSV file
        json_dir: Path to JSON directory
        overlap_stats: Dictionary with overlap analysis results
        strategy: DeduplicationStrategy enum
        
    Returns:
        tuple: (harmonized_dataframe, statistics_dict)
    """
    logger.info(f"Harmonizing data with {strategy.value} strategy")
    
    # Prepare data
    json_df = prepare_json_df(
        json_dir, 
        overlap_stats["overlap"] | overlap_stats["json_only"]
    )
    csv_df = prepare_csv_df(
        pl.scan_csv(csv_path), 
        overlap_stats["overlap"] | overlap_stats["csv_only"]
    )
    
    logger.debug(
        f"Prepared {len(csv_df)} CSV records and {len(json_df)} JSON records"
    )
    
    # Get strategy configuration
    strategy_config = get_strategy_config(strategy)
    
    # Merge dataframes
    merged_df = csv_df.join(
        json_df,
        left_on=HarmonizedFieldName.NCT_ID.value,
        right_on=JSONSourceField.JSON_NCT_ID.value,
        how="outer_coalesce",
    )
    
    if len(merged_df) == 0:
        logger.warning("No data after merge, creating empty dataset")
        harmonized_df = pl.DataFrame(schema=OUTPUT_SCHEMA)
    else:
        # Apply coalescing strategy
        final_df = merged_df.pipe(strategy_config["coalesce_func"])
        final_df = final_df.with_columns(
            strategy_config["source_logic"].alias("data_source")
        )
        
        # Enforce schema
        harmonized_df = finalize_and_enforce_schema(final_df)
    
    stats = {
        "input_csv_records": len(csv_df),
        "input_json_records": len(json_df),
        "output_records": len(harmonized_df),
    }
    
    logger.info(f"Harmonized {len(harmonized_df):,} records")
    
    return harmonized_df, stats


def create_shards(
    dataframe: pl.DataFrame, 
    shard_count: int, 
    output_dir: Path
) -> list[dict[str, any]]:
    """
    Create data shards for parallel processing.
    
    Args:
        dataframe: Polars DataFrame to shard
        shard_count: Number of shards to create
        output_dir: Output directory for shards
        
    Returns:
        list: List of shard metadata dictionaries
    """
    logger.info(f"Creating {shard_count} shards for parallel processing")
    
    # Add shard assignments using hash of NCT ID
    df_with_shards = dataframe.with_columns(
        (pl.col(HarmonizedFieldName.NCT_ID.value).hash() % shard_count).alias("shard_id")
    )
    
    # Create shard directory
    shard_dir = output_dir / "sharded"
    shard_dir.mkdir(parents=True, exist_ok=True)
    
    # Create and save each shard
    shards = []
    for shard_id in range(shard_count):
        shard_data = df_with_shards.filter(pl.col("shard_id") == shard_id)
        if len(shard_data) > 0:
            shard_path = shard_dir / f"shard_{shard_id:03d}.parquet"
            shard_data.write_parquet(shard_path)
            
            shards.append({
                "shard_id": shard_id,
                "path": str(shard_path),
                "record_count": len(shard_data),
            })
    
    logger.info(f"Created {len(shards)} non-empty shards")
    return shards