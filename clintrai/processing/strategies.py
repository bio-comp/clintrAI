"""Coalescing strategies for clinical trials data harmonization."""

from __future__ import annotations

import polars as pl

from clintrai.models.types import HarmonizedFieldName, JSONSourceField


def _create_coalesce_expression(primary_col: str, fallback_col: str, output_col: str) -> pl.Expr:
    """
    Create a Polars expression for simple coalescing with priority.
    
    Args:
        primary_col: Column name to prioritize
        fallback_col: Column name to use if primary is null
        output_col: Name for the output column
        
    Returns:
        Polars expression for coalescing
    """
    return pl.coalesce([
        pl.col(primary_col),
        pl.col(fallback_col)
    ]).alias(output_col)


def _create_merged_list_expression(
    json_col: str, 
    csv_col: str, 
    output_col: str
) -> pl.Expr:
    """
    Create a Polars expression to merge two list-type columns.
    
    Combines lists when both exist, otherwise uses coalescing.
    Automatically deduplicates merged lists.
    
    Args:
        json_col: JSON column name
        csv_col: CSV column name  
        output_col: Name for the output column
        
    Returns:
        Polars expression for list merging
    """
    return pl.when(
        pl.col(json_col).is_not_null() & pl.col(csv_col).is_not_null()
    ).then(
        pl.col(json_col).list.concat(pl.col(csv_col)).list.unique()
    ).otherwise(
        pl.coalesce([pl.col(json_col), pl.col(csv_col)])
    ).alias(output_col)


def _create_preservation_expression(source_col: str, preserved_alias: str) -> pl.Expr:
    """
    Create a Polars expression to preserve original column values.
    
    Args:
        source_col: Source column name
        preserved_alias: Alias for the preserved column
        
    Returns:
        Polars expression for field preservation
    """
    return pl.col(source_col).alias(preserved_alias)


def apply_json_priority_coalescing(df: pl.DataFrame) -> pl.DataFrame:
    """
    Apply coalescing logic to prioritize JSON data over CSV data.
    
    Args:
        df: DataFrame with both CSV and JSON columns
        
    Returns:
        DataFrame with JSON-prioritized coalesced columns
    """
    return df.with_columns([
        _create_coalesce_expression(
            JSONSourceField.JSON_OFFICIAL_TITLE.value,
            HarmonizedFieldName.TITLE.value,
            HarmonizedFieldName.OFFICIAL_TITLE.value
        ),
        _create_coalesce_expression(
            JSONSourceField.JSON_BRIEF_TITLE.value,
            HarmonizedFieldName.TITLE.value,
            HarmonizedFieldName.BRIEF_TITLE.value
        ),
        _create_coalesce_expression(
            JSONSourceField.JSON_OVERALL_STATUS.value,
            HarmonizedFieldName.OVERALL_STATUS.value,
            HarmonizedFieldName.OVERALL_STATUS.value
        ),
        _create_coalesce_expression(
            JSONSourceField.JSON_STUDY_TYPE.value,
            HarmonizedFieldName.STUDY_TYPE.value,
            HarmonizedFieldName.STUDY_TYPE.value
        ),
        _create_coalesce_expression(
            JSONSourceField.JSON_BRIEF_SUMMARY.value,
            HarmonizedFieldName.BRIEF_SUMMARY.value,
            HarmonizedFieldName.BRIEF_SUMMARY.value
        ),
        pl.col(JSONSourceField.JSON_DETAILED_DESCRIPTION.value)
        .alias(HarmonizedFieldName.DETAILED_DESCRIPTION.value),
        _create_coalesce_expression(
            JSONSourceField.JSON_CONDITIONS.value,
            HarmonizedFieldName.CONDITIONS.value,
            HarmonizedFieldName.CONDITIONS.value
        ),
        _create_coalesce_expression(
            JSONSourceField.JSON_INTERVENTIONS.value,
            HarmonizedFieldName.INTERVENTIONS.value,
            HarmonizedFieldName.INTERVENTIONS.value
        ),
        pl.col(JSONSourceField.JSON_CONDITION_MESHES.value)
        .alias(HarmonizedFieldName.CONDITION_MESHES.value),
        _create_coalesce_expression(
            JSONSourceField.JSON_SEX.value,
            HarmonizedFieldName.SEX.value,
            HarmonizedFieldName.SEX.value
        ),
        _create_coalesce_expression(
            JSONSourceField.JSON_ENROLLMENT.value,
            HarmonizedFieldName.ENROLLMENT.value,
            HarmonizedFieldName.ENROLLMENT.value
        ),
        pl.col(JSONSourceField.JSON_HAS_RESULTS.value)
        .alias(HarmonizedFieldName.HAS_RESULTS.value),
    ])


def apply_csv_priority_coalescing(df: pl.DataFrame) -> pl.DataFrame:
    """
    Apply coalescing logic to prioritize CSV data over JSON data.
    
    Args:
        df: DataFrame with both CSV and JSON columns
        
    Returns:
        DataFrame with CSV-prioritized coalesced columns
    """
    return df.with_columns([
        _create_coalesce_expression(
            HarmonizedFieldName.TITLE.value,
            JSONSourceField.JSON_OFFICIAL_TITLE.value,
            HarmonizedFieldName.OFFICIAL_TITLE.value
        ),
        _create_coalesce_expression(
            HarmonizedFieldName.TITLE.value,
            JSONSourceField.JSON_BRIEF_TITLE.value,
            HarmonizedFieldName.BRIEF_TITLE.value
        ),
        _create_coalesce_expression(
            HarmonizedFieldName.OVERALL_STATUS.value,
            JSONSourceField.JSON_OVERALL_STATUS.value,
            HarmonizedFieldName.OVERALL_STATUS.value
        ),
        _create_coalesce_expression(
            HarmonizedFieldName.STUDY_TYPE.value,
            JSONSourceField.JSON_STUDY_TYPE.value,
            HarmonizedFieldName.STUDY_TYPE.value
        ),
        _create_coalesce_expression(
            HarmonizedFieldName.BRIEF_SUMMARY.value,
            JSONSourceField.JSON_BRIEF_SUMMARY.value,
            HarmonizedFieldName.BRIEF_SUMMARY.value
        ),
        pl.col(JSONSourceField.JSON_DETAILED_DESCRIPTION.value)
        .alias(HarmonizedFieldName.DETAILED_DESCRIPTION.value),
        _create_coalesce_expression(
            HarmonizedFieldName.CONDITIONS.value,
            JSONSourceField.JSON_CONDITIONS.value,
            HarmonizedFieldName.CONDITIONS.value
        ),
        _create_coalesce_expression(
            HarmonizedFieldName.INTERVENTIONS.value,
            JSONSourceField.JSON_INTERVENTIONS.value,
            HarmonizedFieldName.INTERVENTIONS.value
        ),
        pl.col(JSONSourceField.JSON_CONDITION_MESHES.value)
        .alias(HarmonizedFieldName.CONDITION_MESHES.value),
        _create_coalesce_expression(
            HarmonizedFieldName.SEX.value,
            JSONSourceField.JSON_SEX.value,
            HarmonizedFieldName.SEX.value
        ),
        _create_coalesce_expression(
            HarmonizedFieldName.ENROLLMENT.value,
            JSONSourceField.JSON_ENROLLMENT.value,
            HarmonizedFieldName.ENROLLMENT.value
        ),
        pl.col(JSONSourceField.JSON_HAS_RESULTS.value)
        .alias(HarmonizedFieldName.HAS_RESULTS.value),
    ])


def apply_merge_coalescing(df: pl.DataFrame) -> pl.DataFrame:
    """
    Apply coalescing logic to merge and preserve data from both sources.
    
    Args:
        df: DataFrame with both CSV and JSON columns
        
    Returns:
        DataFrame with merged data preserving information from both sources
    """
    return df.with_columns([
        # Create combined titles - preserve both when available
        _create_coalesce_expression(
            JSONSourceField.JSON_OFFICIAL_TITLE.value,
            HarmonizedFieldName.TITLE.value,
            HarmonizedFieldName.OFFICIAL_TITLE.value
        ),
        _create_coalesce_expression(
            JSONSourceField.JSON_BRIEF_TITLE.value,
            HarmonizedFieldName.TITLE.value,
            HarmonizedFieldName.BRIEF_TITLE.value
        ),
        
        # Keep separate CSV and JSON specific fields for research
        _create_preservation_expression(HarmonizedFieldName.TITLE.value, "csv_title"),
        _create_preservation_expression(JSONSourceField.JSON_OFFICIAL_TITLE.value, "json_official_title_preserved"),
        _create_preservation_expression(JSONSourceField.JSON_BRIEF_TITLE.value, "json_brief_title_preserved"),
        
        # Merge status information with JSON priority but preserve CSV
        _create_coalesce_expression(
            JSONSourceField.JSON_OVERALL_STATUS.value,
            HarmonizedFieldName.OVERALL_STATUS.value,
            HarmonizedFieldName.OVERALL_STATUS.value
        ),
        _create_preservation_expression(HarmonizedFieldName.OVERALL_STATUS.value, "csv_overall_status"),
        
        # Merge study type with JSON priority
        _create_coalesce_expression(
            JSONSourceField.JSON_STUDY_TYPE.value,
            HarmonizedFieldName.STUDY_TYPE.value,
            HarmonizedFieldName.STUDY_TYPE.value
        ),
        
        # Merge summaries - JSON detailed description is unique
        _create_coalesce_expression(
            JSONSourceField.JSON_BRIEF_SUMMARY.value,
            HarmonizedFieldName.BRIEF_SUMMARY.value,
            HarmonizedFieldName.BRIEF_SUMMARY.value
        ),
        pl.col(JSONSourceField.JSON_DETAILED_DESCRIPTION.value)
        .alias(HarmonizedFieldName.DETAILED_DESCRIPTION.value),
        
        # Merge conditions and interventions - combine lists when both exist
        _create_merged_list_expression(
            JSONSourceField.JSON_CONDITIONS.value,
            HarmonizedFieldName.CONDITIONS.value,
            HarmonizedFieldName.CONDITIONS.value
        ),
        _create_merged_list_expression(
            JSONSourceField.JSON_INTERVENTIONS.value,
            HarmonizedFieldName.INTERVENTIONS.value,
            HarmonizedFieldName.INTERVENTIONS.value
        ),
        
        # Keep JSON-only enriched data
        pl.col(JSONSourceField.JSON_CONDITION_MESHES.value)
        .alias(HarmonizedFieldName.CONDITION_MESHES.value),
        
        # Demographics - merge with JSON priority but preserve CSV
        _create_coalesce_expression(
            JSONSourceField.JSON_SEX.value,
            HarmonizedFieldName.SEX.value,
            HarmonizedFieldName.SEX.value
        ),
        _create_preservation_expression(HarmonizedFieldName.SEX.value, "csv_sex"),
        
        # Enrollment - JSON priority but preserve both
        _create_coalesce_expression(
            JSONSourceField.JSON_ENROLLMENT.value,
            HarmonizedFieldName.ENROLLMENT.value,
            HarmonizedFieldName.ENROLLMENT.value
        ),
        _create_preservation_expression(HarmonizedFieldName.ENROLLMENT.value, "csv_enrollment"),
        
        # Results availability
        pl.col(JSONSourceField.JSON_HAS_RESULTS.value)
        .alias(HarmonizedFieldName.HAS_RESULTS.value),
    ])