"""Pydantic models for CSV clinical trial data with proper alias handling."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, BeforeValidator, computed_field
from pydantic.alias_generators import to_snake

from clintrai.models.types import (
    DataSource, DocumentSource, DocumentType, CSVFieldName, HarmonizedFieldAlias, 
    StudyStatus, StudyType, StudyResults, Sex, StudyPhase
)


def parse_flexible_date(v: Any) -> date | None:
    """Try parsing a date with multiple common formats."""
    if not isinstance(v, str) or not v.strip():
        return None
    
    # Add day if only year-month is provided
    if len(v.strip()) == 7 and v.count('-') == 1:
        v = f"{v.strip()}-01"

    # Try multiple date formats
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(v.strip(), fmt).date()
        except ValueError:
            continue
    
    # If all formats fail, return None
    return None


class ClinicalTrialCSVRecord(BaseModel):
    """Pydantic model for clinical trial CSV data with snake_case conversion."""
    
    model_config = ConfigDict(
        alias_generator=to_snake,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    # Core identification - NCT Number is required, others may be missing
    nct_number: str = Field(..., alias=CSVFieldName.NCT_NUMBER, description="ClinicalTrials.gov NCT identifier")
    study_title: str | None = Field(None, alias=CSVFieldName.STUDY_TITLE, description="Primary study title")
    study_url: HttpUrl | None = Field(None, alias=CSVFieldName.STUDY_URL, description="ClinicalTrials.gov study URL")
    acronym: str | None = Field(None, alias=CSVFieldName.ACRONYM, description="Study acronym")
    
    # Status and classification - these fields are typically present but may be empty
    study_status: StudyStatus | None = Field(None, alias=CSVFieldName.STUDY_STATUS, description="Current recruitment status")
    study_results: StudyResults | None = Field(None, alias=CSVFieldName.STUDY_RESULTS, description="Results availability status")
    study_type: StudyType | None = Field(None, alias=CSVFieldName.STUDY_TYPE, description="Type of study (Interventional, Observational)")
    study_design: str | None = Field(None, alias=CSVFieldName.STUDY_DESIGN, description="Study design details")
    
    # Summary and conditions - brief_summary is usually present, conditions may be missing
    brief_summary: str | None = Field(None, alias=CSVFieldName.BRIEF_SUMMARY, description="Brief study description")
    conditions: str | None = Field(None, alias=CSVFieldName.CONDITIONS, description="Pipe-separated list of conditions")
    interventions: str | None = Field(None, alias=CSVFieldName.INTERVENTIONS, description="Pipe-separated list of interventions")
    
    # Outcome measures - these are often missing for many studies
    primary_outcome_measures: str | None = Field(None, alias=CSVFieldName.PRIMARY_OUTCOME_MEASURES, description="Primary outcomes")
    secondary_outcome_measures: str | None = Field(None, alias=CSVFieldName.SECONDARY_OUTCOME_MEASURES, description="Secondary outcomes")
    other_outcome_measures: str | None = Field(None, alias=CSVFieldName.OTHER_OUTCOME_MEASURES, description="Other outcomes")
    
    # Sponsorship - sponsor is usually present, collaborators often missing
    sponsor: str | None = Field(None, alias=CSVFieldName.SPONSOR, description="Lead sponsor organization")
    collaborators: str | None = Field(None, alias=CSVFieldName.COLLABORATORS, description="Collaborating organizations")
    funder_type: str | None = Field(None, alias=CSVFieldName.FUNDER_TYPE, description="Type of funding organization")
    
    # Demographics and eligibility
    sex: Sex | None = Field(None, alias=CSVFieldName.SEX, description="Sex eligibility (All, Female, Male)")
    age: str | None = Field(None, alias=CSVFieldName.AGE, description="Age eligibility criteria")
    phases: StudyPhase | None = Field(None, alias=CSVFieldName.PHASES, description="Study phases")
    enrollment: int | None = Field(None, alias=CSVFieldName.ENROLLMENT, description="Target/actual enrollment number")
    
    # Dates - these are often missing or incomplete
    start_date: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, alias=CSVFieldName.START_DATE, description="Study start date")
    primary_completion_date: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, alias=CSVFieldName.PRIMARY_COMPLETION_DATE, description="Primary completion date")
    completion_date: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, alias=CSVFieldName.COMPLETION_DATE, description="Study completion date")
    first_posted: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, alias=CSVFieldName.FIRST_POSTED, description="First posted date")
    results_first_posted: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, alias=CSVFieldName.RESULTS_FIRST_POSTED, description="Results first posted date")
    last_update_posted: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, alias=CSVFieldName.LAST_UPDATE_POSTED, description="Last update posted date")
    
    # Location and documents
    locations: str | None = Field(None, alias=CSVFieldName.LOCATIONS, description="Study locations")
    study_documents: str | None = Field(None, alias=CSVFieldName.STUDY_DOCUMENTS, description="Study documents with URLs")
    other_ids: str | None = Field(None, alias=CSVFieldName.OTHER_IDS, description="Other study identifiers")
    
    
    @field_validator('nct_number')
    @classmethod
    def validate_nct_number(cls, v: str) -> str:
        """Validate NCT number format."""
        if not v.upper().startswith('NCT'):
            raise ValueError('NCT number must start with "NCT"')
        return v.upper()
    
    
    @field_validator('*', mode='before')
    @classmethod
    def convert_empty_strings_to_none(cls, v: Any) -> Any:
        """Convert empty strings to None for all optional string fields."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
    
    
    @computed_field
    @property
    def document_urls(self) -> list[str]:
        """Extract URLs from the study_documents field."""
        if not self.study_documents:
            return []
        
        url_pattern = r'https?://[^\s,]+'
        urls = re.findall(url_pattern, self.study_documents)
        return [url.strip() for url in urls]
    
    @computed_field
    @property
    def conditions_list(self) -> list[str]:
        """Extract conditions as a list from pipe-separated string."""
        if not self.conditions:
            return []
        return [condition.strip() for condition in self.conditions.split('|') if condition.strip()]
    
    @computed_field
    @property
    def interventions_list(self) -> list[str]:
        """Extract interventions as a list from pipe-separated string."""
        if not self.interventions:
            return []
        return [intervention.strip() for intervention in self.interventions.split('|') if intervention.strip()]


class HarmonizedClinicalTrial(BaseModel):
    """
    Harmonized model combining CSV and JSON data with proper field mapping.
    Uses snake_case internally but can accept both camelCase and snake_case inputs.
    """
    
    model_config = ConfigDict(
        alias_generator=to_snake, 
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    # Core identification (required fields)
    nct_id: str = Field(..., alias=HarmonizedFieldAlias.NCT_ID, description="ClinicalTrials.gov NCT identifier")
    data_source: DataSource = Field(..., alias=HarmonizedFieldAlias.DATA_SOURCE, description="Source of primary data")
    
    # Basic information - these should be present in most records
    official_title: str | None = Field(None, alias=HarmonizedFieldAlias.OFFICIAL_TITLE, description="Official study title")
    brief_title: str | None = Field(None, alias=HarmonizedFieldAlias.BRIEF_TITLE, description="Brief study title") 
    acronym: str | None = Field(None, description="Study acronym")
    
    # Status and classification - critical fields that should be present
    overall_status: StudyStatus | None = Field(None, alias=HarmonizedFieldAlias.OVERALL_STATUS, description="Current study status")
    study_type: StudyType | None = Field(None, alias=HarmonizedFieldAlias.STUDY_TYPE, description="Type of study")
    study_phase: StudyPhase | None = Field(None, alias=HarmonizedFieldAlias.STUDY_PHASE, description="Study phase")
    has_results: bool | None = Field(None, alias=HarmonizedFieldAlias.HAS_RESULTS, description="Whether results are available")
    
    # Descriptions - brief_summary should usually be present
    brief_summary: str | None = Field(None, alias=HarmonizedFieldAlias.BRIEF_SUMMARY, description="Brief study summary")
    detailed_description: str | None = Field(None, alias=HarmonizedFieldAlias.DETAILED_DESCRIPTION, description="Detailed study description")
    
    # Conditions and interventions - use lists with defaults since we process these
    conditions: list[str] = Field(default_factory=list, description="Study conditions")
    interventions: list[str] = Field(default_factory=list, description="Study interventions")
    
    # Outcome measures - often missing, so nullable
    primary_outcomes: list[str] = Field(default_factory=list, description="Primary outcome measures")
    secondary_outcomes: list[str] = Field(default_factory=list, description="Secondary outcome measures")
    other_outcomes: list[str] = Field(default_factory=list, description="Other outcome measures")
    
    # Sponsorship - lead_sponsor should usually be present
    lead_sponsor: str | None = Field(None, alias=HarmonizedFieldAlias.LEAD_SPONSOR, description="Lead sponsor organization")
    collaborators: list[str] = Field(default_factory=list, description="Collaborating organizations")
    
    # Eligibility - these are often missing or incomplete
    eligibility_criteria: str | None = Field(None, description="Eligibility criteria text")
    sex: Sex | None = Field(None, description="Sex eligibility")
    minimum_age: str | None = Field(None, description="Minimum age")
    maximum_age: str | None = Field(None, description="Maximum age")
    healthy_volunteers: bool | None = Field(None, description="Accepts healthy volunteers")
    
    # Enrollment and dates - enrollment often missing, dates frequently incomplete
    enrollment: int | None = Field(None, description="Target or actual enrollment")
    start_date: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, description="Study start date")
    primary_completion_date: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, description="Primary completion date") 
    completion_date: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, description="Study completion date")
    
    # Administrative dates - these should be present for posted studies
    first_posted: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, description="First posted on ClinicalTrials.gov")
    last_update_posted: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, description="Last update posted")
    
    # Documents and references - use lists since we process these
    document_urls: list[str] = Field(default_factory=list, description="URLs to study documents")
    document_filenames: list[str] = Field(default_factory=list, description="Names of document files")
    
    # Location information
    locations: list[str] = Field(default_factory=list, description="Study locations")
    
    # Metadata for processing - required for our pipeline
    shard_hash: str | None = Field(None, description="MD5 hash for sharding")
    
    # JSON-specific enriched data (only present when JSON data available)
    json_condition_meshes: str | None = Field(None, description="MeSH terms from JSON")
    json_phases: str | None = Field(None, description="Phases from JSON")
    json_design_allocation: str | None = Field(None, description="Design allocation from JSON")
    json_masking: str | None = Field(None, description="Masking information from JSON")
    
    @field_validator('nct_id')
    @classmethod
    def validate_nct_id(cls, v: str) -> str:
        """Validate NCT ID format."""
        if not v.startswith('NCT'):
            raise ValueError('NCT ID must start with "NCT"')
        return v.upper()
    
    
    
    @property
    def document_count(self) -> int:
        """Get total number of associated documents."""
        return len(self.document_urls) + len(self.document_filenames)
    
    @property
    def has_json_data(self) -> bool:
        """Check if this record includes JSON-derived data."""
        return self.data_source in {DataSource.JSON_PRIORITY, DataSource.CSV_FALLBACK}
    
    @property
    def is_interventional(self) -> bool:
        """Check if this is an interventional study."""
        return self.study_type == StudyType.INTERVENTIONAL
    
    @property
    def is_recruiting(self) -> bool:
        """Check if the study is currently recruiting."""
        if self.overall_status is None:
            return False
        
        recruiting_statuses = {
            StudyStatus.RECRUITING,
            StudyStatus.NOT_YET_RECRUITING,
            StudyStatus.ENROLLING_BY_INVITATION
        }
        
        return self.overall_status in recruiting_statuses


class DocumentReference(BaseModel):
    """Model for document references extracted from studies."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    # Required fields
    nct_id: str = Field(..., description="Associated NCT ID")
    source: DocumentSource = Field(..., description="Source of document reference")
    
    # Document details - these may be missing depending on source
    document_type: DocumentType = Field(DocumentType.OTHER, description="Type of document")
    filename: str | None = Field(None, description="Document filename")
    url: HttpUrl | None = Field(None, description="Direct URL to document")
    size_bytes: int | None = Field(None, description="Document size in bytes")
    upload_date: Annotated[date | None, BeforeValidator(parse_flexible_date)] = Field(None, description="Document upload date")
    
    @property
    def file_extension(self) -> str | None:
        """Extract file extension from filename or URL."""
        if self.filename:
            return self.filename.split('.')[-1].lower() if '.' in self.filename else None
        elif self.url:
            url_str = str(self.url)
            return url_str.split('.')[-1].split('?')[0].lower() if '.' in url_str else None
        return None
    
    @property
    def is_pdf(self) -> bool:
        """Check if this is a PDF document."""
        return self.file_extension == 'pdf'


class DataHarmonizationStats(BaseModel):
    """Statistics from the data harmonization process."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    # Required statistics - these should always be computable
    csv_study_count: int = Field(..., description="Total studies in CSV")
    json_study_count: int = Field(..., description="Total studies with JSON files")
    overlap_count: int = Field(..., description="Studies present in both CSV and JSON")
    csv_only_count: int = Field(..., description="Studies only in CSV")
    json_only_count: int = Field(..., description="Studies only in JSON")
    harmonized_count: int = Field(..., description="Total harmonized studies output")
    document_url_count: int = Field(..., description="Studies with document URLs")
    
    # Optional error tracking
    processing_errors: int = Field(default=0, description="Number of processing errors")
    
    @property
    def overlap_percentage(self) -> float:
        """Calculate overlap as percentage of CSV studies."""
        return (self.overlap_count / self.csv_study_count * 100) if self.csv_study_count > 0 else 0.0
    
    @property 
    def json_coverage_percentage(self) -> float:
        """Calculate JSON coverage as percentage of CSV studies."""
        return (self.json_study_count / self.csv_study_count * 100) if self.csv_study_count > 0 else 0.0