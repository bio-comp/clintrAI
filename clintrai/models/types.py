# clintrai/models/types.py
"""Shared types and enums for clinical trial data models."""

from __future__ import annotations

from enum import Enum


class DeduplicationStrategy(str, Enum):
    """Strategy for handling duplicate records between CSV and JSON sources."""
    
    JSON_PRIORITY = "json_priority"
    CSV_PRIORITY = "csv_priority"
    MERGE_ALL = "merge_all"


class DataSource(str, Enum):
    """Source of clinical trial data."""
    
    CSV_ONLY = "csv_only"
    JSON_ONLY = "json_only"
    JSON_PRIORITY = "json_priority"
    CSV_FALLBACK = "csv_fallback"
    MERGED = "merged"


class DocumentSource(str, Enum):
    """Source of document reference."""
    
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"
    EXTERNAL = "external"


class DocumentType(str, Enum):
    """Type of clinical trial document."""
    
    PROTOCOL = "protocol"
    SAP = "sap"  # Statistical Analysis Plan
    ICF = "icf"  # Informed Consent Form
    CSR = "csr"  # Clinical Study Report
    RESULTS = "results"
    SUMMARY = "summary"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """Status of data processing."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FileFormat(str, Enum):
    """Supported file formats."""
    
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    PDF = "pdf"
    TXT = "txt"
    XML = "xml"


class CSVFieldName(str, Enum):
    """CSV column names as they appear in the actual CSV file."""
    
    # Core identification
    NCT_NUMBER = "NCT Number"
    STUDY_TITLE = "Study Title" 
    STUDY_URL = "Study URL"
    ACRONYM = "Acronym"
    
    # Status and classification
    STUDY_STATUS = "Study Status"
    STUDY_RESULTS = "Study Results"
    STUDY_TYPE = "Study Type"
    STUDY_DESIGN = "Study Design"
    
    # Summary and conditions
    BRIEF_SUMMARY = "Brief Summary"
    CONDITIONS = "Conditions"
    INTERVENTIONS = "Interventions"
    
    # Outcome measures
    PRIMARY_OUTCOME_MEASURES = "Primary Outcome Measures"
    SECONDARY_OUTCOME_MEASURES = "Secondary Outcome Measures"
    OTHER_OUTCOME_MEASURES = "Other Outcome Measures"
    
    # Sponsorship
    SPONSOR = "Sponsor"
    COLLABORATORS = "Collaborators"
    FUNDER_TYPE = "Funder Type"
    
    # Demographics
    SEX = "Sex"
    AGE = "Age"
    PHASES = "Phases"
    ENROLLMENT = "Enrollment"
    
    # Dates
    START_DATE = "Start Date"
    PRIMARY_COMPLETION_DATE = "Primary Completion Date"
    COMPLETION_DATE = "Completion Date"
    FIRST_POSTED = "First Posted"
    RESULTS_FIRST_POSTED = "Results First Posted"
    LAST_UPDATE_POSTED = "Last Update Posted"
    
    # Location and documents
    LOCATIONS = "Locations"
    STUDY_DOCUMENTS = "Study Documents"
    OTHER_IDS = "Other IDs"


class JSONSourceField(str, Enum):
    """Field names for flattened JSON data columns."""
    
    # Core identification
    JSON_NCT_ID = "json_nct_id"
    JSON_OFFICIAL_TITLE = "json_official_title"
    JSON_BRIEF_TITLE = "json_brief_title"
    JSON_ACRONYM = "json_acronym"
    JSON_ORG_STUDY_ID = "json_org_study_id"
    
    # Status and classification
    JSON_OVERALL_STATUS = "json_overall_status"
    JSON_STUDY_TYPE = "json_study_type"
    JSON_PHASES = "json_phases"
    JSON_HAS_RESULTS = "json_has_results"
    
    # Summary and conditions
    JSON_BRIEF_SUMMARY = "json_brief_summary"
    JSON_DETAILED_DESCRIPTION = "json_detailed_description"
    JSON_CONDITIONS = "json_conditions"
    JSON_INTERVENTIONS = "json_interventions"
    JSON_CONDITION_MESHES = "json_condition_meshes"
    
    # Demographics
    JSON_SEX = "json_sex"
    JSON_MINIMUM_AGE = "json_minimum_age"
    JSON_MAXIMUM_AGE = "json_maximum_age"
    JSON_HEALTHY_VOLUNTEERS = "json_healthy_volunteers"
    JSON_ENROLLMENT = "json_enrollment"
    
    # Dates
    JSON_START_DATE = "json_start_date"
    JSON_COMPLETION_DATE = "json_completion_date"
    
    # Documents
    JSON_DOCUMENT_FILES = "json_document_files"


class JSONFieldPath(str, Enum):
    """JSON field paths for clinical trial data."""
    
    # Top level sections
    PROTOCOL_SECTION = "protocolSection"
    RESULTS_SECTION = "resultsSection"
    ANNOTATION_SECTION = "annotationSection"
    DOCUMENT_SECTION = "documentSection"
    DERIVED_SECTION = "derivedSection"
    HAS_RESULTS = "hasResults"
    
    # Protocol section modules
    IDENTIFICATION_MODULE = "identificationModule"
    STATUS_MODULE = "statusModule"
    DESCRIPTION_MODULE = "descriptionModule"
    CONDITIONS_MODULE = "conditionsModule"
    DESIGN_MODULE = "designModule"
    ARMS_INTERVENTIONS_MODULE = "armsInterventionsModule"
    ELIGIBILITY_MODULE = "eligibilityModule"
    
    # Field names within modules
    OFFICIAL_TITLE = "officialTitle"
    BRIEF_TITLE = "briefTitle"
    ORG_STUDY_ID_INFO = "orgStudyIdInfo"
    ID = "id"
    ACRONYM = "acronym"
    OVERALL_STATUS = "overallStatus"
    START_DATE_STRUCT = "startDateStruct"
    COMPLETION_DATE_STRUCT = "completionDateStruct"
    DATE = "date"
    BRIEF_SUMMARY = "briefSummary"
    DETAILED_DESCRIPTION = "detailedDescription"
    STUDY_TYPE = "studyType"
    PHASES = "phases"
    CONDITIONS = "conditions"
    INTERVENTIONS = "interventions"
    NAME = "name"
    SEX = "sex"
    MINIMUM_AGE = "minimumAge"
    MAXIMUM_AGE = "maximumAge"
    HEALTHY_VOLUNTEERS = "healthyVolunteers"
    ENROLLMENT_INFO = "enrollmentInfo"
    COUNT = "count"
    
    # Derived section
    CONDITION_BROWSE_MODULE = "conditionBrowseModule"
    MESHES = "meshes"
    TERM = "term"
    
    # Document section
    LARGE_DOCUMENT_MODULE = "largeDocumentModule"
    LARGE_DOCS = "largeDocs"
    FILENAME = "filename"


class HarmonizedFieldName(str, Enum):
    """Field names for harmonized output data."""
    
    # Core identification
    NCT_ID = "nct_id"
    TITLE = "title"
    OFFICIAL_TITLE = "official_title"
    BRIEF_TITLE = "brief_title"
    STUDY_URL = "study_url"
    ACRONYM = "acronym"
    
    # Status and classification
    OVERALL_STATUS = "overall_status"
    STUDY_TYPE = "study_type"
    STUDY_PHASE = "study_phase"
    HAS_RESULTS = "has_results"
    
    # Summary and descriptions
    BRIEF_SUMMARY = "brief_summary"
    DETAILED_DESCRIPTION = "detailed_description"
    
    # Conditions and interventions
    CONDITIONS = "conditions"
    INTERVENTIONS = "interventions"
    CONDITION_MESHES = "condition_meshes"
    
    # Eligibility
    SEX = "sex"
    MINIMUM_AGE = "minimum_age"
    MAXIMUM_AGE = "maximum_age"
    HEALTHY_VOLUNTEERS = "healthy_volunteers"
    ENROLLMENT = "enrollment"
    
    # Dates
    START_DATE = "start_date"
    PRIMARY_COMPLETION_DATE = "primary_completion_date"
    COMPLETION_DATE = "completion_date"
    FIRST_POSTED = "first_posted"
    LAST_UPDATE_POSTED = "last_update_posted"
    
    # Sponsorship
    LEAD_SPONSOR = "lead_sponsor"
    COLLABORATORS = "collaborators"
    
    # Documents and locations
    DOCUMENT_URLS = "document_urls"
    DOCUMENT_FILES = "document_files"
    LOCATIONS = "locations"
    
    # Metadata
    DATA_SOURCE = "data_source"
    SHARD_HASH = "shard_hash"
    PROCESSING_TIMESTAMP = "processing_timestamp"


class HarmonizedFieldAlias(str, Enum):
    """CamelCase aliases for HarmonizedClinicalTrial input fields."""
    
    # Core identification (required fields)
    NCT_ID = "nctId"
    DATA_SOURCE = "dataSource"
    
    # Basic information
    OFFICIAL_TITLE = "officialTitle"
    BRIEF_TITLE = "briefTitle"
    
    # Status and classification
    OVERALL_STATUS = "overallStatus"
    STUDY_TYPE = "studyType"
    STUDY_PHASE = "studyPhase"
    HAS_RESULTS = "hasResults"
    
    # Summary and descriptions
    BRIEF_SUMMARY = "briefSummary"
    DETAILED_DESCRIPTION = "detailedDescription"
    
    # Eligibility
    MINIMUM_AGE = "minimumAge"
    MAXIMUM_AGE = "maximumAge"
    HEALTHY_VOLUNTEERS = "healthyVolunteers"
    
    # Dates
    START_DATE = "startDate"
    PRIMARY_COMPLETION_DATE = "primaryCompletionDate"
    COMPLETION_DATE = "completionDate"
    FIRST_POSTED = "firstPosted"
    LAST_UPDATE_POSTED = "lastUpdatePosted"
    
    # Sponsorship
    LEAD_SPONSOR = "leadSponsor"
    
    # Documents and locations
    DOCUMENT_URLS = "documentUrls"
    DOCUMENT_FILES = "documentFiles"
    
    # Metadata
    SHARD_HASH = "shardHash"
    PROCESSING_TIMESTAMP = "processingTimestamp"


class StudyStatus(str, Enum):
    """Clinical trial study status values."""
    
    COMPLETED = "COMPLETED"
    RECRUITING = "RECRUITING"
    NOT_YET_RECRUITING = "NOT_YET_RECRUITING"
    ENROLLING_BY_INVITATION = "ENROLLING_BY_INVITATION"
    ACTIVE_NOT_RECRUITING = "ACTIVE_NOT_RECRUITING"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"
    WITHDRAWN = "WITHDRAWN"
    UNKNOWN = "UNKNOWN"


class StudyType(str, Enum):
    """Clinical trial study type values."""
    
    INTERVENTIONAL = "INTERVENTIONAL"
    OBSERVATIONAL = "OBSERVATIONAL"
    EXPANDED_ACCESS = "EXPANDED_ACCESS"


class StudyPhase(str, Enum):
    """Clinical trial phase values."""
    
    EARLY_PHASE_1 = "EARLY_PHASE_1"
    PHASE_1 = "PHASE_1"
    PHASE_1_PHASE_2 = "PHASE_1_PHASE_2"
    PHASE_2 = "PHASE_2"
    PHASE_2_PHASE_3 = "PHASE_2_PHASE_3"
    PHASE_3 = "PHASE_3"
    PHASE_4 = "PHASE_4"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NA = "NA"


class Sex(str, Enum):
    """Sex eligibility values."""
    
    ALL = "ALL"
    FEMALE = "FEMALE"
    MALE = "MALE"


class StudyResults(str, Enum):
    """Study results availability values."""
    
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"