"""Data preparation functions for clinical trials data harmonization."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, TypeAlias

import polars as pl
from loguru import logger
from pydantic import ValidationError

from clintrai.models.types import JSONSourceField, HarmonizedFieldName, CSVFieldName
from clintrai.models.json_models import ClinicalTrialJSONRecord

# Type aliases for better readability
NCTIdSet: TypeAlias = set[str]
JSONRecord: TypeAlias = dict[str, Any]


def prepare_csv_df(csv_lf: pl.LazyFrame, nct_ids: NCTIdSet) -> pl.DataFrame:
    """
    Prepare CSV DataFrame with filtering and standardization.
    
    Args:
        csv_lf: Lazy DataFrame from CSV file
        nct_ids: Set of NCT IDs to filter for
        
    Returns:
        Standardized DataFrame with harmonized columns
    """
    if not nct_ids:
        # Return empty DF with just the key column for join
        return pl.DataFrame(
            {HarmonizedFieldName.NCT_ID.value: []}, 
            schema={HarmonizedFieldName.NCT_ID.value: pl.Utf8}
        )
    
    # Filter and collect CSV data
    csv_df = csv_lf.filter(
        pl.col(CSVFieldName.NCT_NUMBER.value).is_in(list(nct_ids))
    ).collect()
    
    # Standardize columns and types
    return _standardize_csv_columns(csv_df)


def prepare_json_df(json_dir: Path, nct_ids: NCTIdSet) -> pl.DataFrame:
    """
    Prepare JSON DataFrame with parallel loading.
    
    Args:
        json_dir: Directory containing JSON files
        nct_ids: Set of NCT IDs to load
        
    Returns:
        DataFrame with flattened JSON data
    """
    if not nct_ids:
        # Return empty DF with just the key column for join
        return pl.DataFrame(
            {JSONSourceField.JSON_NCT_ID.value: []}, 
            schema={JSONSourceField.JSON_NCT_ID.value: pl.Utf8}
        )
        
    json_records = _load_and_flatten_json_records(json_dir, nct_ids)
    if not json_records:
        return pl.DataFrame(
            {JSONSourceField.JSON_NCT_ID.value: []}, 
            schema={JSONSourceField.JSON_NCT_ID.value: pl.Utf8}
        )
        
    return pl.DataFrame(json_records)


def _standardize_csv_columns(csv_df: pl.DataFrame) -> pl.DataFrame:
    """Standardize CSV column names and types efficiently."""
    # Map CSV columns to harmonized names using enums for consistency
    column_mapping = {
        CSVFieldName.NCT_NUMBER.value: HarmonizedFieldName.NCT_ID.value,
        CSVFieldName.STUDY_TITLE.value: HarmonizedFieldName.TITLE.value,
        CSVFieldName.STUDY_URL.value: HarmonizedFieldName.STUDY_URL.value,
        CSVFieldName.ACRONYM.value: HarmonizedFieldName.ACRONYM.value,
        CSVFieldName.STUDY_STATUS.value: HarmonizedFieldName.OVERALL_STATUS.value,
        CSVFieldName.STUDY_RESULTS.value: HarmonizedFieldName.HAS_RESULTS.value,
        CSVFieldName.CONDITIONS.value: HarmonizedFieldName.CONDITIONS.value,
        CSVFieldName.INTERVENTIONS.value: HarmonizedFieldName.INTERVENTIONS.value,
        CSVFieldName.SPONSOR.value: HarmonizedFieldName.LEAD_SPONSOR.value,
        CSVFieldName.COLLABORATORS.value: HarmonizedFieldName.COLLABORATORS.value,
        CSVFieldName.SEX.value: HarmonizedFieldName.SEX.value,
        CSVFieldName.AGE.value: HarmonizedFieldName.MINIMUM_AGE.value,
        CSVFieldName.PHASES.value: HarmonizedFieldName.STUDY_PHASE.value,
        CSVFieldName.ENROLLMENT.value: HarmonizedFieldName.ENROLLMENT.value,
        CSVFieldName.START_DATE.value: HarmonizedFieldName.START_DATE.value,
        CSVFieldName.PRIMARY_COMPLETION_DATE.value: HarmonizedFieldName.PRIMARY_COMPLETION_DATE.value,
        CSVFieldName.COMPLETION_DATE.value: HarmonizedFieldName.COMPLETION_DATE.value,
        CSVFieldName.FIRST_POSTED.value: HarmonizedFieldName.FIRST_POSTED.value,
        CSVFieldName.LAST_UPDATE_POSTED.value: HarmonizedFieldName.LAST_UPDATE_POSTED.value,
        CSVFieldName.STUDY_DOCUMENTS.value: HarmonizedFieldName.DOCUMENT_URLS.value,
        CSVFieldName.LOCATIONS.value: HarmonizedFieldName.LOCATIONS.value,
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


def _load_and_flatten_json_records(json_dir: Path, nct_ids: NCTIdSet) -> list[JSONRecord]:
    """Load and flatten JSON records in parallel."""
    records = []
    
    def _process_file(nct_id: str) -> JSONRecord | None:
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
        future_to_id = {
            executor.submit(_process_file, nct_id): nct_id 
            for nct_id in nct_ids
        }
        for future in as_completed(future_to_id):
            result = future.result()
            if result:
                records.append(result)
                
    logger.info(
        f"Successfully loaded {len(records)} JSON records "
        f"out of {len(nct_ids)} requested"
    )
    return records


def _flatten_json_record(nct_id: str, record: ClinicalTrialJSONRecord) -> JSONRecord:
    """Flatten a validated JSON record into a single-level dictionary."""
    return {
        JSONSourceField.JSON_NCT_ID.value: nct_id,
        JSONSourceField.JSON_OFFICIAL_TITLE.value: record.official_title,
        JSONSourceField.JSON_BRIEF_TITLE.value: record.brief_title,
        JSONSourceField.JSON_ACRONYM.value: record.acronym,
        JSONSourceField.JSON_OVERALL_STATUS.value: record.overall_status,
        JSONSourceField.JSON_STUDY_TYPE.value: record.study_type,
        JSONSourceField.JSON_PHASES.value: record.phases,
        JSONSourceField.JSON_HAS_RESULTS.value: record.has_results,
        JSONSourceField.JSON_BRIEF_SUMMARY.value: record.brief_summary,
        JSONSourceField.JSON_DETAILED_DESCRIPTION.value: record.detailed_description,
        JSONSourceField.JSON_CONDITIONS.value: record.conditions,
        JSONSourceField.JSON_INTERVENTIONS.value: record.interventions,
        JSONSourceField.JSON_CONDITION_MESHES.value: record.mesh_terms,
        JSONSourceField.JSON_SEX.value: record.sex,
        JSONSourceField.JSON_MINIMUM_AGE.value: record.minimum_age,
        JSONSourceField.JSON_MAXIMUM_AGE.value: record.maximum_age,
        JSONSourceField.JSON_HEALTHY_VOLUNTEERS.value: record.healthy_volunteers,
        JSONSourceField.JSON_ENROLLMENT.value: record.enrollment,
        JSONSourceField.JSON_START_DATE.value: record.start_date,
        JSONSourceField.JSON_COMPLETION_DATE.value: record.completion_date,
        JSONSourceField.JSON_DOCUMENT_FILES.value: record.document_files,
    }