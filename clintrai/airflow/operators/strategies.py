"""
Coalescing strategies for clinical trials data harmonization.
This module contains functions that implement different data merging strategies
for combining CSV and JSON data sources.
"""

from __future__ import annotations

import polars as pl

from clintrai.models.types import HarmonizedFieldName


def apply_json_priority_coalescing(df: pl.DataFrame) -> pl.DataFrame:
    """Apply coalescing logic to prioritize JSON data over CSV data."""
    return df.with_columns([
        pl.coalesce([
            pl.col("json_official_title"),
            pl.col(HarmonizedFieldName.TITLE.value)
        ]).alias(HarmonizedFieldName.OFFICIAL_TITLE.value),
        
        pl.coalesce([
            pl.col("json_brief_title"),
            pl.col(HarmonizedFieldName.TITLE.value)
        ]).alias(HarmonizedFieldName.BRIEF_TITLE.value),
        
        pl.coalesce([
            pl.col("json_overall_status"),
            pl.col(HarmonizedFieldName.OVERALL_STATUS.value)
        ]).alias(HarmonizedFieldName.OVERALL_STATUS.value),
        
        pl.coalesce([
            pl.col("json_study_type"),
            pl.col(HarmonizedFieldName.STUDY_TYPE.value)
        ]).alias(HarmonizedFieldName.STUDY_TYPE.value),
        
        pl.coalesce([
            pl.col("json_brief_summary"),
            pl.col(HarmonizedFieldName.BRIEF_SUMMARY.value)
        ]).alias(HarmonizedFieldName.BRIEF_SUMMARY.value),
        
        pl.col("json_detailed_description").alias(HarmonizedFieldName.DETAILED_DESCRIPTION.value),
        
        pl.coalesce([
            pl.col("json_conditions"),
            pl.col(HarmonizedFieldName.CONDITIONS.value)
        ]).alias(HarmonizedFieldName.CONDITIONS.value),
        
        pl.coalesce([
            pl.col("json_interventions"),
            pl.col(HarmonizedFieldName.INTERVENTIONS.value)
        ]).alias(HarmonizedFieldName.INTERVENTIONS.value),
        
        pl.col("json_condition_meshes").alias(HarmonizedFieldName.CONDITION_MESHES.value),
        
        pl.coalesce([
            pl.col("json_sex"),
            pl.col(HarmonizedFieldName.SEX.value)
        ]).alias(HarmonizedFieldName.SEX.value),
        
        pl.coalesce([
            pl.col("json_enrollment"),
            pl.col(HarmonizedFieldName.ENROLLMENT.value)
        ]).alias(HarmonizedFieldName.ENROLLMENT.value),
        
        pl.col("json_has_results").alias(HarmonizedFieldName.HAS_RESULTS.value),
    ])


def apply_csv_priority_coalescing(df: pl.DataFrame) -> pl.DataFrame:
    """Apply coalescing logic to prioritize CSV data over JSON data."""
    return df.with_columns([
        pl.coalesce([
            pl.col(HarmonizedFieldName.TITLE.value),
            pl.col("json_official_title")
        ]).alias(HarmonizedFieldName.OFFICIAL_TITLE.value),
        
        pl.coalesce([
            pl.col(HarmonizedFieldName.TITLE.value),
            pl.col("json_brief_title")
        ]).alias(HarmonizedFieldName.BRIEF_TITLE.value),
        
        pl.coalesce([
            pl.col(HarmonizedFieldName.OVERALL_STATUS.value),
            pl.col("json_overall_status")
        ]).alias(HarmonizedFieldName.OVERALL_STATUS.value),
        
        pl.coalesce([
            pl.col(HarmonizedFieldName.STUDY_TYPE.value),
            pl.col("json_study_type")
        ]).alias(HarmonizedFieldName.STUDY_TYPE.value),
        
        pl.coalesce([
            pl.col(HarmonizedFieldName.BRIEF_SUMMARY.value),
            pl.col("json_brief_summary")
        ]).alias(HarmonizedFieldName.BRIEF_SUMMARY.value),
        
        pl.col("json_detailed_description").alias(HarmonizedFieldName.DETAILED_DESCRIPTION.value),
        
        pl.coalesce([
            pl.col(HarmonizedFieldName.CONDITIONS.value),
            pl.col("json_conditions")
        ]).alias(HarmonizedFieldName.CONDITIONS.value),
        
        pl.coalesce([
            pl.col(HarmonizedFieldName.INTERVENTIONS.value),
            pl.col("json_interventions")
        ]).alias(HarmonizedFieldName.INTERVENTIONS.value),
        
        pl.col("json_condition_meshes").alias(HarmonizedFieldName.CONDITION_MESHES.value),
        
        pl.coalesce([
            pl.col(HarmonizedFieldName.SEX.value),
            pl.col("json_sex")
        ]).alias(HarmonizedFieldName.SEX.value),
        
        pl.coalesce([
            pl.col(HarmonizedFieldName.ENROLLMENT.value),
            pl.col("json_enrollment")
        ]).alias(HarmonizedFieldName.ENROLLMENT.value),
        
        pl.col("json_has_results").alias(HarmonizedFieldName.HAS_RESULTS.value),
    ])


def apply_merge_coalescing(df: pl.DataFrame) -> pl.DataFrame:
    """Apply coalescing logic to merge and preserve data from both CSV and JSON sources."""
    return df.with_columns([
        # Create combined titles - preserve both when available
        pl.coalesce([
            pl.col("json_official_title"),
            pl.col(HarmonizedFieldName.TITLE.value)
        ]).alias(HarmonizedFieldName.OFFICIAL_TITLE.value),
        
        pl.coalesce([
            pl.col("json_brief_title"),
            pl.col(HarmonizedFieldName.TITLE.value)
        ]).alias(HarmonizedFieldName.BRIEF_TITLE.value),
        
        # Keep separate CSV and JSON specific fields for research
        pl.col(HarmonizedFieldName.TITLE.value).alias("csv_title"),
        pl.col("json_official_title").alias("json_official_title_preserved"),
        pl.col("json_brief_title").alias("json_brief_title_preserved"),
        
        # Merge status information with JSON priority but preserve CSV
        pl.coalesce([
            pl.col("json_overall_status"),
            pl.col(HarmonizedFieldName.OVERALL_STATUS.value)
        ]).alias(HarmonizedFieldName.OVERALL_STATUS.value),
        pl.col(HarmonizedFieldName.OVERALL_STATUS.value).alias("csv_overall_status"),
        
        # Merge study type with JSON priority
        pl.coalesce([
            pl.col("json_study_type"),
            pl.col(HarmonizedFieldName.STUDY_TYPE.value)
        ]).alias(HarmonizedFieldName.STUDY_TYPE.value),
        
        # Merge summaries - JSON detailed description is unique
        pl.coalesce([
            pl.col("json_brief_summary"),
            pl.col(HarmonizedFieldName.BRIEF_SUMMARY.value)
        ]).alias(HarmonizedFieldName.BRIEF_SUMMARY.value),
        pl.col("json_detailed_description").alias(HarmonizedFieldName.DETAILED_DESCRIPTION.value),
        
        # Merge conditions and interventions - combine lists when both exist
        pl.when(pl.col("json_conditions").is_not_null() & pl.col(HarmonizedFieldName.CONDITIONS.value).is_not_null())
        .then(
            pl.col("json_conditions").list.concat(pl.col(HarmonizedFieldName.CONDITIONS.value)).list.unique()
        )
        .otherwise(
            pl.coalesce([pl.col("json_conditions"), pl.col(HarmonizedFieldName.CONDITIONS.value)])
        ).alias(HarmonizedFieldName.CONDITIONS.value),
        
        pl.when(pl.col("json_interventions").is_not_null() & pl.col(HarmonizedFieldName.INTERVENTIONS.value).is_not_null())
        .then(
            pl.col("json_interventions").list.concat(pl.col(HarmonizedFieldName.INTERVENTIONS.value)).list.unique()
        )
        .otherwise(
            pl.coalesce([pl.col("json_interventions"), pl.col(HarmonizedFieldName.INTERVENTIONS.value)])
        ).alias(HarmonizedFieldName.INTERVENTIONS.value),
        
        # Keep JSON-only enriched data
        pl.col("json_condition_meshes").alias(HarmonizedFieldName.CONDITION_MESHES.value),
        
        # Demographics - merge with JSON priority but preserve CSV
        pl.coalesce([
            pl.col("json_sex"),
            pl.col(HarmonizedFieldName.SEX.value)
        ]).alias(HarmonizedFieldName.SEX.value),
        pl.col(HarmonizedFieldName.SEX.value).alias("csv_sex"),
        
        # Enrollment - JSON priority but preserve both
        pl.coalesce([
            pl.col("json_enrollment"),
            pl.col(HarmonizedFieldName.ENROLLMENT.value)
        ]).alias(HarmonizedFieldName.ENROLLMENT.value),
        pl.col(HarmonizedFieldName.ENROLLMENT.value).alias("csv_enrollment"),
        
        # Results availability
        pl.col("json_has_results").alias(HarmonizedFieldName.HAS_RESULTS.value),
    ])