"""Pydantic models for clinical trial data from clinicaltrials.gov."""

from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class StudyType(str, Enum):
    """Types of clinical studies."""
    
    INTERVENTIONAL = "Interventional"
    OBSERVATIONAL = "Observational"
    PATIENT_REGISTRY = "Patient Registry"
    EXPANDED_ACCESS = "Expanded Access"


class StudyPhase(str, Enum):
    """Clinical study phases."""
    
    NA = "N/A"
    EARLY_PHASE_1 = "Early Phase 1"
    PHASE_1 = "Phase 1"
    PHASE_1_2 = "Phase 1/Phase 2"
    PHASE_2 = "Phase 2"
    PHASE_2_3 = "Phase 2/Phase 3"
    PHASE_3 = "Phase 3"
    PHASE_4 = "Phase 4"


class StudyStatus(str, Enum):
    """Current status of clinical study."""
    
    NOT_YET_RECRUITING = "Not yet recruiting"
    RECRUITING = "Recruiting"
    ENROLLING_BY_INVITATION = "Enrolling by invitation"
    ACTIVE_NOT_RECRUITING = "Active, not recruiting"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"
    COMPLETED = "Completed"
    WITHDRAWN = "Withdrawn"
    UNKNOWN = "Unknown status"


class InterventionType(str, Enum):
    """Types of interventions in clinical trials."""
    
    DRUG = "Drug"
    DEVICE = "Device"
    BIOLOGICAL = "Biological"
    PROCEDURE = "Procedure"
    RADIATION = "Radiation"
    BEHAVIORAL = "Behavioral"
    GENETIC = "Genetic"
    DIETARY_SUPPLEMENT = "Dietary Supplement"
    COMBINATION_PRODUCT = "Combination Product"
    DIAGNOSTIC_TEST = "Diagnostic Test"
    OTHER = "Other"


class Gender(str, Enum):
    """Gender eligibility for studies."""
    
    ALL = "All"
    FEMALE = "Female"
    MALE = "Male"


class SamplingMethod(str, Enum):
    """Sampling methods for observational studies."""
    
    PROBABILITY_SAMPLE = "Probability Sample"
    NON_PROBABILITY_SAMPLE = "Non-Probability Sample"


class AllocationMethod(str, Enum):
    """Intervention allocation methods."""
    
    RANDOMIZED = "Randomized"
    NON_RANDOMIZED = "Non-Randomized"


class MaskingType(str, Enum):
    """Masking/blinding types."""
    
    NONE = "None (Open Label)"
    SINGLE = "Single"
    DOUBLE = "Double"
    TRIPLE = "Triple"
    QUADRUPLE = "Quadruple"


class Contact(BaseModel):
    """Contact information for study personnel."""
    
    name: str
    phone: str | None = Field(default=None)
    phone_ext: str | None = Field(default=None)
    email: str | None = Field(default=None)
    role: str | None = Field(default=None)


class Location(BaseModel):
    """Study location information."""
    
    facility: str
    city: str
    state: str | None = Field(default=None)
    country: str
    zip_code: str | None = Field(default=None)
    status: StudyStatus | None = Field(default=None)
    contact: Contact | None = Field(default=None)
    backup_contact: Contact | None = Field(default=None)
    investigator: Contact | None = Field(default=None)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)


class Sponsor(BaseModel):
    """Study sponsor information."""
    
    name: str
    agency_class: str | None = Field(default=None)
    role: str = Field(default="lead_sponsor")


class Eligibility(BaseModel):
    """Study eligibility criteria."""
    
    criteria: str
    gender: Gender = Field(default=Gender.ALL)
    gender_based: bool = Field(default=False)
    gender_description: str | None = Field(default=None)
    minimum_age: str | None = Field(default=None)
    maximum_age: str | None = Field(default=None)
    healthy_volunteers: bool = Field(default=False)
    sampling_method: SamplingMethod | None = Field(default=None)
    study_population: str | None = Field(default=None)


class Intervention(BaseModel):
    """Study intervention details."""
    
    intervention_type: InterventionType
    name: str
    description: str | None = Field(default=None)
    arm_group_labels: list[str] = Field(default_factory=list)
    other_names: list[str] = Field(default_factory=list)


class ArmGroup(BaseModel):
    """Study arm/group information."""
    
    label: str
    arm_group_type: str | None = Field(default=None)
    description: str | None = Field(default=None)
    intervention_names: list[str] = Field(default_factory=list)


class Outcome(BaseModel):
    """Study outcome measures."""
    
    measure: str
    time_frame: str
    description: str | None = Field(default=None)
    outcome_type: str = Field(default="primary")


class Reference(BaseModel):
    """Study reference/citation."""
    
    citation: str
    pmid: str | None = Field(default=None)
    reference_type: str | None = Field(default=None)


class StudyDesign(BaseModel):
    """Study design information."""
    
    allocation: AllocationMethod | None = Field(default=None)
    intervention_model: str | None = Field(default=None)
    intervention_model_description: str | None = Field(default=None)
    primary_purpose: str | None = Field(default=None)
    observational_model: str | None = Field(default=None)
    time_perspective: str | None = Field(default=None)
    masking: MaskingType | None = Field(default=None)
    masking_description: str | None = Field(default=None)
    who_masked: list[str] = Field(default_factory=list)


class Oversight(BaseModel):
    """Study oversight information."""
    
    has_dmc: bool | None = Field(default=None)
    is_fda_regulated_drug: bool | None = Field(default=None)
    is_fda_regulated_device: bool | None = Field(default=None)
    is_unapproved_device: bool | None = Field(default=None)
    is_ppsd: bool | None = Field(default=None)
    is_us_export: bool | None = Field(default=None)


class StudyInfo(BaseModel):
    """Basic study identification and administrative information."""
    
    nct_id: str = Field(..., description="ClinicalTrials.gov identifier")
    org_study_id: str | None = Field(default=None)
    secondary_ids: list[str] = Field(default_factory=list)
    first_submitted: date | None = Field(default=None)
    first_posted: date | None = Field(default=None)
    last_update_submitted: date | None = Field(default=None)
    last_update_posted: date | None = Field(default=None)
    study_first_submitted_qc: date | None = Field(default=None)
    study_first_posted_qc: date | None = Field(default=None)
    results_first_submitted: date | None = Field(default=None)
    results_first_posted: date | None = Field(default=None)
    disposition_first_submitted: date | None = Field(default=None)
    disposition_first_posted: date | None = Field(default=None)
    last_update_submitted_qc: date | None = Field(default=None)
    last_update_posted_qc: date | None = Field(default=None)
    verification_date: date | None = Field(default=None)


class ClinicalTrial(BaseModel):
    """Complete clinical trial data model."""
    
    id: UUID = Field(default_factory=uuid4)
    study_info: StudyInfo
    
    # Title and summary
    brief_title: str
    official_title: str | None = Field(default=None)
    acronym: str | None = Field(default=None)
    brief_summary: str | None = Field(default=None)
    detailed_description: str | None = Field(default=None)
    
    # Study classification
    study_type: StudyType
    study_phase: StudyPhase | None = Field(default=None)
    study_status: StudyStatus
    
    # Study design
    study_design: StudyDesign | None = Field(default=None)
    
    # Dates
    start_date: date | None = Field(default=None)
    start_date_type: str | None = Field(default=None)
    completion_date: date | None = Field(default=None)
    completion_date_type: str | None = Field(default=None)
    primary_completion_date: date | None = Field(default=None)
    primary_completion_date_type: str | None = Field(default=None)
    
    # Enrollment
    enrollment: int | None = Field(default=None)
    enrollment_type: str | None = Field(default=None)
    
    # Conditions and keywords
    conditions: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    
    # Eligibility
    eligibility: Eligibility | None = Field(default=None)
    
    # Study participants
    sponsors: list[Sponsor] = Field(default_factory=list)
    collaborators: list[Sponsor] = Field(default_factory=list)
    investigators: list[Contact] = Field(default_factory=list)
    overall_officials: list[Contact] = Field(default_factory=list)
    overall_contact: Contact | None = Field(default=None)
    overall_contact_backup: Contact | None = Field(default=None)
    
    # Locations
    locations: list[Location] = Field(default_factory=list)
    location_countries: list[str] = Field(default_factory=list)
    removed_location_countries: list[str] = Field(default_factory=list)
    
    # Arms and interventions
    arm_groups: list[ArmGroup] = Field(default_factory=list)
    interventions: list[Intervention] = Field(default_factory=list)
    
    # Outcomes
    primary_outcomes: list[Outcome] = Field(default_factory=list)
    secondary_outcomes: list[Outcome] = Field(default_factory=list)
    other_outcomes: list[Outcome] = Field(default_factory=list)
    
    # References and links
    references: list[Reference] = Field(default_factory=list)
    see_also_links: list[HttpUrl] = Field(default_factory=list)
    
    # Oversight
    oversight: Oversight | None = Field(default=None)
    
    # Data management
    patient_data_sharing_ipd: str | None = Field(default=None)
    patient_data_sharing_description: str | None = Field(default=None)
    
    # Metadata
    data_downloaded_at: datetime = Field(default_factory=datetime.now)
    source_url: HttpUrl | None = Field(default=None)
    raw_data: dict[str, Any] | None = Field(default=None)
    
    class Config:
        """Pydantic model configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }