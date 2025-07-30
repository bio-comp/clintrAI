"""
Main Airflow operator for clinical trials data harmonization.
This module contains the DataHarmonizationOperator class, which orchestrates
the data loading, preparation, and harmonization process.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import polars as pl
from airflow.models import BaseOperator
from airflow.utils.context import Context
from loguru import logger

from clintrai.models.types import DeduplicationStrategy, DataSource, FieldName, HarmonizedFieldName
from .preparation import prepare_csv_df, prepare_json_df
from .strategies import (
    apply_json_priority_coalescing,
    apply_csv_priority_coalescing,
    apply_merge_coalescing,
)
from .schema import OUTPUT_SCHEMA, finalize_and_enforce_schema


class DataHarmonizationOperator(BaseOperator):
    """
    Orchestrates the harmonization of CSV and JSON clinical trial data by
    coordinating data preparation, strategy application, and schema enforcement.
    
    This operator handles:
    - Loading CSV and JSON data efficiently using vectorized operations
    - Deduplication based on NCT IDs with configurable strategies
    - Field mapping and data consolidation using Pydantic models
    - Output in standardized format with consistent snake_case fields
    - Schema enforcement for data consistency
    """

    template_fields = ['csv_path', 'json_dir', 'output_path']

    def __init__(
        self,
        csv_path: str | Path,
        json_dir: str | Path,
        output_path: str | Path,
        deduplication_strategy: DeduplicationStrategy = DeduplicationStrategy.JSON_PRIORITY,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.csv_path = Path(csv_path)
        self.json_dir = Path(json_dir)
        self.output_path = Path(output_path)
        self.deduplication_strategy = deduplication_strategy

        # Validation
        if not self.csv_path.exists():
            raise ValueError(f"CSV file not found: {self.csv_path}")
        if not self.json_dir.exists():
            raise ValueError(f"JSON directory not found: {self.json_dir}")

    def execute(self, context: Context) -> dict[str, Any]:
        """Execute the data harmonization process."""
        logger.info(f"Starting data harmonization: {self.csv_path} + {self.json_dir}")
        logger.info(f"Using deduplication strategy: {self.deduplication_strategy.value}")

        try:
            # Load CSV data with lazy evaluation
            csv_lf = pl.scan_csv(self.csv_path)
            csv_nct_ids = set(
                csv_lf.select(FieldName.NCT_NUMBER.value).collect().get_column(FieldName.NCT_NUMBER.value).to_list()
            )
            logger.info(f"Found {len(csv_nct_ids):,} studies in CSV")

            # Get JSON NCT IDs
            json_files = list(self.json_dir.glob("NCT*.json"))
            json_nct_ids = {f.stem for f in json_files}
            logger.info(f"Found {len(json_nct_ids):,} studies in JSON")

            # Analyze overlap
            overlap = csv_nct_ids & json_nct_ids
            csv_only = csv_nct_ids - json_nct_ids
            json_only = json_nct_ids - csv_nct_ids

            logger.info(f"Overlap: {len(overlap):,} studies")
            logger.info(f"CSV only: {len(csv_only):,} studies")
            logger.info(f"JSON only: {len(json_only):,} studies")

            # Create harmonized dataset
            harmonized_data = self._harmonize_data(csv_lf, overlap, csv_only, json_only)

            # Save results
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            harmonized_data.write_parquet(self.output_path)

            # Return statistics for downstream tasks
            stats = {
                "csv_studies": len(csv_nct_ids),
                "json_studies": len(json_nct_ids),
                "overlap_studies": len(overlap),
                "csv_only_studies": len(csv_only),
                "json_only_studies": len(json_only),
                "harmonized_studies": len(harmonized_data),
                "output_path": str(self.output_path),
                "deduplication_strategy": self.deduplication_strategy.value,
            }

            logger.success(f"Harmonization complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Harmonization failed: {e}")
            raise

    def _harmonize_data(
        self,
        csv_lf: pl.LazyFrame,
        overlap: set[str],
        csv_only: set[str],
        json_only: set[str],
    ) -> pl.DataFrame:
        """Dispatcher for harmonization strategies."""
        strategy_map = {
            DeduplicationStrategy.JSON_PRIORITY: {
                "coalesce_func": apply_json_priority_coalescing,
                "source_logic": pl.when(pl.col("json_official_title").is_not_null())
                .then(
                    pl.when(pl.col(HarmonizedFieldName.TITLE.value).is_not_null())
                    .then(pl.lit(DataSource.JSON_PRIORITY.value))  # Both sources
                    .otherwise(pl.lit(DataSource.JSON_ONLY.value))  # JSON only
                )
                .otherwise(pl.lit(DataSource.CSV_ONLY.value)),  # CSV only
            },
            DeduplicationStrategy.CSV_PRIORITY: {
                "coalesce_func": apply_csv_priority_coalescing,
                "source_logic": pl.when(pl.col(HarmonizedFieldName.TITLE.value).is_not_null())
                .then(
                    pl.when(pl.col("json_official_title").is_not_null())
                    .then(pl.lit(DataSource.CSV_PRIORITY.value))  # Both sources
                    .otherwise(pl.lit(DataSource.CSV_ONLY.value))  # CSV only
                )
                .otherwise(pl.lit(DataSource.JSON_ONLY.value)),  # JSON only
            },
            DeduplicationStrategy.MERGE_ALL: {
                "coalesce_func": apply_merge_coalescing,
                "source_logic": pl.when(
                    pl.col("json_official_title").is_not_null()
                    & pl.col(HarmonizedFieldName.TITLE.value).is_not_null()
                )
                .then(pl.lit(DataSource.MERGED.value))  # Both sources merged
                .when(pl.col("json_official_title").is_not_null())
                .then(pl.lit(DataSource.JSON_ONLY.value))  # JSON only
                .otherwise(pl.lit(DataSource.CSV_ONLY.value)),  # CSV only
            },
        }

        strategy = strategy_map.get(self.deduplication_strategy)
        if not strategy:
            raise ValueError(f"Unknown deduplication strategy: {self.deduplication_strategy}")

        return self._harmonize_by_priority(
            csv_lf=csv_lf,
            overlap=overlap,
            csv_only=csv_only,
            json_only=json_only,
            **strategy,
        )

    def _harmonize_by_priority(
        self,
        csv_lf: pl.LazyFrame,
        overlap: set[str],
        csv_only: set[str],
        json_only: set[str],
        coalesce_func: Callable[[pl.DataFrame], pl.DataFrame],
        source_logic: pl.Expr,
    ) -> pl.DataFrame:
        """Generic harmonization logic based on a provided coalescing function and source logic."""
        logger.info(f"Processing data with {self.deduplication_strategy.value} strategy...")

        # 1. Prepare DataFrames. These methods return empty DFs if no data.
        json_df = prepare_json_df(self.json_dir, overlap | json_only)
        csv_df = prepare_csv_df(csv_lf, overlap | csv_only)

        # 2. Perform the outer join. This works even if one DF is empty.
        merged_df = csv_df.join(
            json_df,
            left_on=HarmonizedFieldName.NCT_ID.value,
            right_on="json_nct_id",
            how="outer_coalesce"  # Automatically merges the join keys
        )

        # If the merged result is empty, return early
        if len(merged_df) == 0:
            logger.info("No data to process after join")
            return pl.DataFrame(schema=OUTPUT_SCHEMA)

        logger.info(f"Processing {len(merged_df)} merged records")

        # 3. Apply the passed-in coalescing function
        final_df = coalesce_func(merged_df)
        
        # 4. Apply the passed-in data source logic
        final_df = final_df.with_columns(
            source_logic.alias(HarmonizedFieldName.DATA_SOURCE.value)
        )

        return finalize_and_enforce_schema(final_df)

    def on_kill(self) -> None:
        """Clean up resources if task is killed."""
        logger.warning(f"Data harmonization task killed: {self.task_id}")
        # Cleanup any temporary files or connections if needed