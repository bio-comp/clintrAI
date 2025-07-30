"""
Data preparation functions for clinical trials data harmonization.
This module handles loading, flattening, and standardizing data from 
both CSV and JSON sources.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import polars as pl
from loguru import logger
from pydantic import ValidationError

from clintrai.models.types import FieldName, HarmonizedFieldName
from clintrai.models.json_models import ClinicalTrialJSONRecord




def prepare_csv_df(csv_lf: pl.LazyFrame, nct_ids: set[str]) -> pl.DataFrame:
    """Prepare CSV DataFrame with filtering and standardization."""
    if not nct_ids:
        # Return empty DF with just the key column for join
        return pl.DataFrame({HarmonizedFieldName.NCT_ID.value: []}, schema={HarmonizedFieldName.NCT_ID.value: pl.Utf8})
    
    # Filter and collect CSV data
    csv_df = csv_lf.filter(
        pl.col(FieldName.NCT_NUMBER.value).is_in(list(nct_ids))
    ).collect()
    
    # Standardize columns and types
    return _standardize_csv_columns(csv_df)


def prepare_json_df(json_dir: Path, nct_ids: set[str]) -> pl.DataFrame:
    """Prepare JSON DataFrame with parallel loading."""
    if not nct_ids:
        # Return empty DF with just the key column for join
        return pl.DataFrame({"json_nct_id": []}, schema={"json_nct_id": pl.Utf8})
        
    json_records = _load_and_flatten_json_records(json_dir, nct_ids)
    if not json_records:
        return pl.DataFrame({"json_nct_id": []}, schema={"json_nct_id": pl.Utf8})
        
    return pl.DataFrame(json_records)


def _standardize_csv_columns(csv_df: pl.DataFrame) -> pl.DataFrame:
    """Standardize CSV column names and types efficiently."""
    # Map CSV columns to harmonized names
    column_mapping = {
        FieldName.NCT_NUMBER.value: HarmonizedFieldName.NCT_ID.value,
        "Study Title": HarmonizedFieldName.TITLE.value,
        "Study URL": HarmonizedFieldName.STUDY_URL.value,
        "Acronym": HarmonizedFieldName.ACRONYM.value,
        "Study Status": HarmonizedFieldName.OVERALL_STATUS.value,
        "Study Results": HarmonizedFieldName.HAS_RESULTS.value,
        "Conditions": HarmonizedFieldName.CONDITIONS.value,
        "Interventions": HarmonizedFieldName.INTERVENTIONS.value,
        "Sponsor": HarmonizedFieldName.LEAD_SPONSOR.value,
        "Collaborators": HarmonizedFieldName.COLLABORATORS.value,
        "Sex": HarmonizedFieldName.SEX.value,
        "Age": HarmonizedFieldName.MINIMUM_AGE.value,
        "Phases": HarmonizedFieldName.STUDY_PHASE.value,
        "Enrollment": HarmonizedFieldName.ENROLLMENT.value,
        "Start Date": HarmonizedFieldName.START_DATE.value,
        "Primary Completion Date": HarmonizedFieldName.PRIMARY_COMPLETION_DATE.value,
        "Completion Date": HarmonizedFieldName.COMPLETION_DATE.value,
        "First Posted": HarmonizedFieldName.FIRST_POSTED.value,
        "Last Update Posted": HarmonizedFieldName.LAST_UPDATE_POSTED.value,
        "Study Documents": HarmonizedFieldName.DOCUMENT_URLS.value,
        "Locations": HarmonizedFieldName.LOCATIONS.value,
    }
    
    # Rename columns that exist
    existing_mappings = {k: v for k, v in column_mapping.items() if k in csv_df.columns}
    df = csv_df.rename(existing_mappings)
    
    # Build and apply all transformations in a single, declarative expression
    return df.with_columns(
        # Parse list fields from pipe-separated strings
        *[
            pl.col(field).str.split("|").fill_null([])
            for field in [
                HarmonizedFieldName.CONDITIONS.value,
                HarmonizedFieldName.INTERVENTIONS.value,
                HarmonizedFieldName.COLLABORATORS.value,
                HarmonizedFieldName.DOCUMENT_URLS.value,
                HarmonizedFieldName.LOCATIONS.value,
            ]
            if field in df.columns
        ],
        # Convert date fields with multiple format fallbacks
        *[
            pl.col(field)
            .str.to_date(format="%B %d, %Y", strict=False)
            .fill_null(pl.col(field).str.to_date(format="%Y-%m-%d", strict=False))
            .fill_null(pl.col(field).str.to_date(format="%m/%d/%Y", strict=False))
            for field in [
                HarmonizedFieldName.START_DATE.value,
                HarmonizedFieldName.PRIMARY_COMPLETION_DATE.value,
                HarmonizedFieldName.COMPLETION_DATE.value,
                HarmonizedFieldName.FIRST_POSTED.value,
                HarmonizedFieldName.LAST_UPDATE_POSTED.value,
            ]
            if field in df.columns
        ],
        # Convert boolean field
        *(
            [pl.col(HarmonizedFieldName.HAS_RESULTS.value)
             .str.to_lowercase()
             .is_in(["yes", "true", "1"])]
            if HarmonizedFieldName.HAS_RESULTS.value in df.columns
            else []
        ),
        # Convert numeric field
        *(
            [pl.col(HarmonizedFieldName.ENROLLMENT.value)
             .cast(pl.Int64, strict=False)]
            if HarmonizedFieldName.ENROLLMENT.value in df.columns
            else []
        ),
    )


def _load_and_flatten_json_records(json_dir: Path, nct_ids: set[str]) -> list[dict]:
    """Load and flatten JSON records in parallel."""
    records = []
    
    def _process_file(nct_id):
        json_path = json_dir / f"{nct_id}.json"
        if not json_path.exists():
            return None
        try:
            with json_path.open('r', encoding='utf-8') as f:
                json_data = json.load(f)
            # Validate and parse using Pydantic model
            record = ClinicalTrialJSONRecord(**json_data)
            return _flatten_json_record(nct_id, record)
        except (ValidationError, Exception) as e:
            logger.warning(f"Could not process JSON for {nct_id}: {e}")
            return None

    # Use parallel processing for better I/O performance
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_id = {executor.submit(_process_file, nct_id): nct_id for nct_id in nct_ids}
        for future in as_completed(future_to_id):
            result = future.result()
            if result:
                records.append(result)
                
    logger.info(f"Successfully loaded {len(records)} JSON records out of {len(nct_ids)} requested")
    return records


def _flatten_json_record(nct_id: str, record: ClinicalTrialJSONRecord) -> dict[str, Any]:
    """Flatten a validated JSON record into a single-level dictionary."""
    return {
        "json_nct_id": nct_id,
        "json_official_title": record.official_title,
        "json_brief_title": record.brief_title,
        "json_acronym": record.acronym,
        "json_overall_status": record.overall_status,
        "json_study_type": record.study_type,
        "json_phases": record.phases,
        "json_has_results": record.has_results,
        "json_brief_summary": record.brief_summary,
        "json_detailed_description": record.detailed_description,
        "json_conditions": record.conditions,
        "json_interventions": record.interventions,
        "json_condition_meshes": record.mesh_terms,
        "json_sex": record.sex,
        "json_minimum_age": record.minimum_age,
        "json_maximum_age": record.maximum_age,
        "json_healthy_volunteers": record.healthy_volunteers,
        "json_enrollment": record.enrollment,
        "json_start_date": record.start_date,
        "json_completion_date": record.completion_date,
        "json_document_files": record.document_files,
    }