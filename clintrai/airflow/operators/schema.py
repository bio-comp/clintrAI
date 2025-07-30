"""
Schema definitions and enforcement for clinical trials data harmonization.
This module defines the output schema and provides functions for 
data finalization and schema enforcement.
"""

from __future__ import annotations

from datetime import datetime, timezone

import polars as pl

from clintrai.models.types import HarmonizedFieldName


# Define output schema for consistency
OUTPUT_SCHEMA = {
    HarmonizedFieldName.NCT_ID.value: pl.Utf8,
    HarmonizedFieldName.TITLE.value: pl.Utf8,
    HarmonizedFieldName.OFFICIAL_TITLE.value: pl.Utf8,
    HarmonizedFieldName.BRIEF_TITLE.value: pl.Utf8,
    HarmonizedFieldName.STUDY_URL.value: pl.Utf8,
    HarmonizedFieldName.ACRONYM.value: pl.Utf8,
    HarmonizedFieldName.OVERALL_STATUS.value: pl.Utf8,
    HarmonizedFieldName.STUDY_TYPE.value: pl.Utf8,
    HarmonizedFieldName.STUDY_PHASE.value: pl.Utf8,
    HarmonizedFieldName.HAS_RESULTS.value: pl.Boolean,
    HarmonizedFieldName.BRIEF_SUMMARY.value: pl.Utf8,
    HarmonizedFieldName.DETAILED_DESCRIPTION.value: pl.Utf8,
    HarmonizedFieldName.CONDITIONS.value: pl.List(pl.Utf8),
    HarmonizedFieldName.INTERVENTIONS.value: pl.List(pl.Utf8),
    HarmonizedFieldName.CONDITION_MESHES.value: pl.List(pl.Utf8),
    HarmonizedFieldName.SEX.value: pl.Utf8,
    HarmonizedFieldName.MINIMUM_AGE.value: pl.Utf8,
    HarmonizedFieldName.MAXIMUM_AGE.value: pl.Utf8,
    HarmonizedFieldName.HEALTHY_VOLUNTEERS.value: pl.Boolean,
    HarmonizedFieldName.ENROLLMENT.value: pl.Int64,
    HarmonizedFieldName.START_DATE.value: pl.Date,
    HarmonizedFieldName.PRIMARY_COMPLETION_DATE.value: pl.Date,
    HarmonizedFieldName.COMPLETION_DATE.value: pl.Date,
    HarmonizedFieldName.FIRST_POSTED.value: pl.Date,
    HarmonizedFieldName.LAST_UPDATE_POSTED.value: pl.Date,
    HarmonizedFieldName.LEAD_SPONSOR.value: pl.Utf8,
    HarmonizedFieldName.COLLABORATORS.value: pl.List(pl.Utf8),
    HarmonizedFieldName.DOCUMENT_URLS.value: pl.List(pl.Utf8),
    HarmonizedFieldName.DOCUMENT_FILES.value: pl.List(pl.Utf8),
    HarmonizedFieldName.LOCATIONS.value: pl.List(pl.Utf8),
    HarmonizedFieldName.DATA_SOURCE.value: pl.Utf8,
    HarmonizedFieldName.SHARD_HASH.value: pl.UInt64,
    HarmonizedFieldName.PROCESSING_TIMESTAMP.value: pl.Datetime,
}


def finalize_and_enforce_schema(df: pl.DataFrame) -> pl.DataFrame:
    """Add metadata and enforce the final output schema."""
    # Add metadata using native polars operations
    df_with_metadata = df.with_columns([
        # Use native polars hash for better performance
        pl.col(HarmonizedFieldName.NCT_ID.value)
        .hash()
        .alias(HarmonizedFieldName.SHARD_HASH.value),
        
        # Use timezone-aware datetime
        pl.lit(datetime.now(timezone.utc)).alias(HarmonizedFieldName.PROCESSING_TIMESTAMP.value)
    ])
    
    # Enforce schema
    return _enforce_output_schema(df_with_metadata)


def _enforce_output_schema(df: pl.DataFrame) -> pl.DataFrame:
    """Enforce the output schema on the final DataFrame."""
    # Select columns in the correct order and cast to proper types
    columns_to_select = []
    
    for col_name, col_type in OUTPUT_SCHEMA.items():
        if col_name in df.columns:
            columns_to_select.append(pl.col(col_name).cast(col_type).alias(col_name))
        else:
            # Add null column with proper type if missing
            if col_type == pl.List(pl.Utf8):
                columns_to_select.append(pl.lit([]).cast(col_type).alias(col_name))
            elif col_type == pl.Boolean:
                columns_to_select.append(pl.lit(None).cast(col_type).alias(col_name))
            elif col_type == pl.Int64:
                columns_to_select.append(pl.lit(None).cast(col_type).alias(col_name))
            elif col_type == pl.Date:
                columns_to_select.append(pl.lit(None).cast(col_type).alias(col_name))
            elif col_type == pl.Datetime:
                columns_to_select.append(pl.lit(None).cast(col_type).alias(col_name))
            else:
                columns_to_select.append(pl.lit(None).cast(col_type).alias(col_name))
    
    return df.select(columns_to_select)