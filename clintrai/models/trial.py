"""Pydantic models for clinical trial data from clinicaltrials.gov."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, ConfigDict, PlainSerializer

from clintrai.models.types import StudyType, StudyPhase, StudyStatus, Sex

# ✅ Modern Pydantic V2 reusable serializers (replaces deprecated json_encoders)
ISODatetime = Annotated[
    datetime, 
    PlainSerializer(lambda dt: dt.isoformat(), return_type=str)
]

ISODate = Annotated[
    date, 
    PlainSerializer(lambda d: d.isoformat(), return_type=str)
]

StringUUID = Annotated[
    UUID, 
    PlainSerializer(lambda u: str(u), return_type=str)
]


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
    
    name: str = Field(description="Full name of the contact person")
    phone: str | None = Field(default=None, description="Primary phone number")
    phone_ext: str | None = Field(default=None, description="Phone extension")
    email: str | None = Field(default=None, description="Email address")
    role: str | None = Field(default=None, description="Role or title of the contact person")


class Location(BaseModel):
    """Study location information."""
    
    facility: str = Field(description="Name of the study facility")
    city: str = Field(description="City where the facility is located")
    state: str | None = Field(default=None, description="State or province")
    country: str = Field(description="Country where the facility is located")
    zip_code: str | None = Field(default=None, description="Postal/ZIP code")
    status: StudyStatus | None = Field(default=None, description="Recruitment status at this location")
    contact: Contact | None = Field(default=None, description="Primary contact for this location")
    backup_contact: Contact | None = Field(default=None, description="Backup contact for this location")
    investigator: Contact | None = Field(default=None, description="Principal investigator at this location")
    latitude: float | None = Field(default=None, description="Geographic latitude coordinate")
    longitude: float | None = Field(default=None, description="Geographic longitude coordinate")


class Sponsor(BaseModel):
    """Study sponsor information."""
    
    name: str
    agency_class: str | None = Field(default=None)
    role: str = Field(default="lead_sponsor")


class Eligibility(BaseModel):
    """Study eligibility criteria."""
    
    criteria: str = Field(description="Detailed eligibility criteria text")
    gender: Sex = Field(default=Sex.ALL, description="Gender eligibility requirements")
    gender_based: bool = Field(default=False, description="Whether eligibility is based on gender identity")
    gender_description: str | None = Field(default=None, description="Additional description of gender-based eligibility")
    minimum_age: str | None = Field(default=None, description="Minimum age for participation")
    maximum_age: str | None = Field(default=None, description="Maximum age for participation")
    healthy_volunteers: bool = Field(default=False, description="Whether healthy volunteers are accepted")
    sampling_method: SamplingMethod | None = Field(default=None, description="Sampling method for observational studies")
    study_population: str | None = Field(default=None, description="Description of the target study population")


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
    
    allocation: AllocationMethod | None = Field(
        default=None, 
        description="Method of assigning participants to an arm"
    )
    intervention_model: str | None = Field(
        default=None,
        description="General design of the intervention (e.g., 'Single Group Assignment')"
    )
    intervention_model_description: str | None = Field(
        default=None, 
        description="Additional details about the intervention model"
    )
    primary_purpose: str | None = Field(
        default=None, 
        description="Primary purpose of the study (e.g., 'Treatment', 'Prevention')"
    )
    observational_model: str | None = Field(
        default=None, 
        description="Design of observational studies (e.g., 'Cohort', 'Case-Control')"
    )
    time_perspective: str | None = Field(
        default=None, 
        description="Time perspective for observational studies (e.g., 'Prospective', 'Retrospective')"
    )
    masking: MaskingType | None = Field(
        default=None, 
        description="Type of masking/blinding used in the study"
    )
    masking_description: str | None = Field(
        default=None, 
        description="Additional details about masking procedures"
    )
    who_masked: list[str] = Field(
        default_factory=list, 
        description="List of parties who are masked/blinded"
    )


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
    first_submitted: ISODate | None = Field(default=None)
    first_posted: ISODate | None = Field(default=None)
    last_update_submitted: ISODate | None = Field(default=None)
    last_update_posted: ISODate | None = Field(default=None)
    study_first_submitted_qc: ISODate | None = Field(default=None)
    study_first_posted_qc: ISODate | None = Field(default=None)
    results_first_submitted: ISODate | None = Field(default=None)
    results_first_posted: ISODate | None = Field(default=None)
    disposition_first_submitted: ISODate | None = Field(default=None)
    disposition_first_posted: ISODate | None = Field(default=None)
    last_update_submitted_qc: ISODate | None = Field(default=None)
    last_update_posted_qc: ISODate | None = Field(default=None)
    verification_date: ISODate | None = Field(default=None)


class ClinicalTrial(BaseModel):
    """Complete clinical trial data model."""
    
    id: StringUUID = Field(default_factory=uuid4)
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
    start_date: ISODate | None = Field(default=None)
    start_date_type: str | None = Field(default=None)
    completion_date: ISODate | None = Field(default=None)
    completion_date_type: str | None = Field(default=None)
    primary_completion_date: ISODate | None = Field(default=None)
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
    data_downloaded_at: ISODatetime = Field(default_factory=datetime.now)
    source_url: HttpUrl | None = Field(default=None)
    raw_data: dict[str, Any] | None = Field(default=None)
    
    # ✅ Pydantic V2 style configuration
    model_config = ConfigDict(
        populate_by_name=True,  # Often useful when mapping from camelCase APIs
    )