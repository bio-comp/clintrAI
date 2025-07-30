"""Compositional Pydantic models for ClinicalTrials.gov JSON data structure."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from clintrai.models.types import StudyStatus, StudyType, StudyPhase, Sex


class DateStruct(BaseModel):
    """Date structure used in JSON data."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    date: str | None = None
    type: str | None = None


class OrganizationInfo(BaseModel):
    """Organization information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    full_name: str | None = None
    class_: str | None = Field(None, alias="class")  # 'class' is a Python keyword


class OrgStudyIdInfo(BaseModel):
    """Organization study ID information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    id: str | None = None


class SecondaryIdInfo(BaseModel):
    """Secondary ID information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    id: str | None = None
    type: str | None = None
    link: str | None = None


class IdentificationModule(BaseModel):
    """Protocol section identification module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    nct_id: str
    org_study_id_info: OrgStudyIdInfo | None = None
    secondary_id_infos: list[SecondaryIdInfo] = Field(default_factory=list)
    organization: OrganizationInfo | None = None
    brief_title: str | None = None
    official_title: str | None = None
    acronym: str | None = None


class StatusModule(BaseModel):
    """Protocol section status module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    status_verified_date: str | None = None
    overall_status: StudyStatus | None = None
    expanded_access_info: dict[str, Any] | None = None
    start_date_struct: DateStruct | None = None
    completion_date_struct: DateStruct | None = None
    primary_completion_date_struct: DateStruct | None = None
    study_first_submit_date: str | None = None
    study_first_submit_qc_date: str | None = None
    study_first_post_date_struct: DateStruct | None = None
    last_update_submit_date: str | None = None
    last_update_post_date_struct: DateStruct | None = None


class SponsorInfo(BaseModel):
    """Sponsor information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    name: str
    class_: str | None = Field(None, alias="class")  # 'class' is a Python keyword


class SponsorCollaboratorsModule(BaseModel):
    """Protocol section sponsor/collaborators module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    lead_sponsor: SponsorInfo | None = None
    collaborators: list[SponsorInfo] = Field(default_factory=list)


class DescriptionModule(BaseModel):
    """Protocol section description module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    brief_summary: str | None = None
    detailed_description: str | None = None


class ConditionsModule(BaseModel):
    """Protocol section conditions module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    conditions: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class DesignInfo(BaseModel):
    """Design information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    allocation: str | None = None
    intervention_model: str | None = None
    primary_purpose: str | None = None
    observational_model: str | None = None
    time_perspective: str | None = None
    masking_info: dict[str, Any] | None = None


class EnrollmentInfo(BaseModel):
    """Enrollment information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    count: int | None = None
    type: str | None = None


# Phase mapping outside the class to avoid Pydantic field issues
PHASE_MAPPING = {
    "PHASE1": StudyPhase.PHASE_1,
    "PHASE2": StudyPhase.PHASE_2,
    "PHASE3": StudyPhase.PHASE_3,
    "PHASE4": StudyPhase.PHASE_4,
    "NA": StudyPhase.NA,
    "N/A": StudyPhase.NA,
    "NOT_APPLICABLE": StudyPhase.NOT_APPLICABLE,
    "EARLY_PHASE_1": StudyPhase.EARLY_PHASE_1,
    "PHASE_1": StudyPhase.PHASE_1,
    "PHASE_2": StudyPhase.PHASE_2,
    "PHASE_3": StudyPhase.PHASE_3,
    "PHASE_4": StudyPhase.PHASE_4,
    "PHASE_1_PHASE_2": StudyPhase.PHASE_1_PHASE_2,
    "PHASE_2_PHASE_3": StudyPhase.PHASE_2_PHASE_3,
}


class DesignModule(BaseModel):
    """Protocol section design module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    study_type: StudyType | None = None
    phases: list[StudyPhase] = Field(default_factory=list)
    design_info: DesignInfo | None = None
    enrollment_info: EnrollmentInfo | None = None
    
    @field_validator('phases', mode='before')
    @classmethod
    def validate_phases(cls, v: Any) -> list[StudyPhase]:
        """Convert phases to a list of StudyPhase enums."""
        if not isinstance(v, list):
            return []
        
        return [
            PHASE_MAPPING.get(str(phase).upper().replace(" ", "_"), StudyPhase.NA)
            for phase in v
        ]


class Intervention(BaseModel):
    """Intervention information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    type: str | None = None
    name: str | None = None
    description: str | None = None
    arm_group_labels: list[str] = Field(default_factory=list)
    other_names: list[str] = Field(default_factory=list)


class ArmsInterventionsModule(BaseModel):
    """Protocol section arms/interventions module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    interventions: list[Intervention] = Field(default_factory=list)


class EligibilityModule(BaseModel):
    """Protocol section eligibility module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    eligibility_criteria: str | None = None
    healthy_volunteers: bool | None = None
    sex: Sex | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    std_ages: list[str] = Field(default_factory=list)


class GeoPoint(BaseModel):
    """Geographic coordinates."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    lat: float | None = None
    lon: float | None = None


class LocationInfo(BaseModel):
    """Location information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    facility: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    zip: str | None = None
    geo_point: GeoPoint | None = None


class ContactsLocationsModule(BaseModel):
    """Protocol section contacts/locations module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    locations: list[LocationInfo] = Field(default_factory=list)


class Reference(BaseModel):
    """Reference information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    pmid: str | None = None
    type: str | None = None
    citation: str | None = None


class ReferencesModule(BaseModel):
    """Protocol section references module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    references: list[Reference] = Field(default_factory=list)


class ProtocolSection(BaseModel):
    """Main protocol section containing all protocol modules."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    identification_module: IdentificationModule | None = None
    status_module: StatusModule | None = None
    sponsor_collaborators_module: SponsorCollaboratorsModule | None = None
    description_module: DescriptionModule | None = None
    conditions_module: ConditionsModule | None = None
    design_module: DesignModule | None = None
    arms_interventions_module: ArmsInterventionsModule | None = None
    eligibility_module: EligibilityModule | None = None
    contacts_locations_module: ContactsLocationsModule | None = None
    references_module: ReferencesModule | None = None


class MeshTerm(BaseModel):
    """MeSH term information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    id: str | None = None
    term: str | None = None


class ConditionBrowseModule(BaseModel):
    """Derived section condition browse module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    meshes: list[MeshTerm] = Field(default_factory=list)
    ancestors: list[MeshTerm] = Field(default_factory=list)
    browse_leaves: list[dict[str, Any]] = Field(default_factory=list)
    browse_branches: list[dict[str, Any]] = Field(default_factory=list)


class InterventionBrowseModule(BaseModel):
    """Derived section intervention browse module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    meshes: list[MeshTerm] = Field(default_factory=list)
    ancestors: list[MeshTerm] = Field(default_factory=list)
    browse_leaves: list[dict[str, Any]] = Field(default_factory=list)
    browse_branches: list[dict[str, Any]] = Field(default_factory=list)


class MiscInfoModule(BaseModel):
    """Miscellaneous information module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    version_holder: str | None = None


class DerivedSection(BaseModel):
    """Derived section containing computed/derived information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    misc_info_module: MiscInfoModule | None = None
    condition_browse_module: ConditionBrowseModule | None = None
    intervention_browse_module: InterventionBrowseModule | None = None


class LargeDocument(BaseModel):
    """Large document information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    filename: str | None = None
    size: int | None = None
    version: str | None = None


class LargeDocumentModule(BaseModel):
    """Large document module."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    large_docs: list[LargeDocument] = Field(default_factory=list)


class DocumentSection(BaseModel):
    """Document section containing document information."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
    
    large_document_module: LargeDocumentModule | None = None


class ClinicalTrialJSONRecord(BaseModel):
    """Root model for ClinicalTrials.gov JSON data structure."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    protocol_section: ProtocolSection | None = None
    derived_section: DerivedSection | None = None
    document_section: DocumentSection | None = None
    has_results: bool = False
    
    # Pythonic properties using short-circuiting for safe nested access
    
    @property
    def nct_id(self) -> str | None:
        """The NCT ID from the identification module."""
        return (self.protocol_section and 
                self.protocol_section.identification_module and 
                self.protocol_section.identification_module.nct_id)
    
    @property
    def official_title(self) -> str | None:
        """The official title."""
        return (self.protocol_section and 
                self.protocol_section.identification_module and 
                self.protocol_section.identification_module.official_title)
    
    @property
    def brief_title(self) -> str | None:
        """The brief title."""
        return (self.protocol_section and 
                self.protocol_section.identification_module and 
                self.protocol_section.identification_module.brief_title)
    
    @property
    def overall_status(self) -> StudyStatus | None:
        """The overall status."""
        return (self.protocol_section and 
                self.protocol_section.status_module and 
                self.protocol_section.status_module.overall_status)
    
    @property
    def study_type(self) -> StudyType | None:
        """The study type."""
        return (self.protocol_section and 
                self.protocol_section.design_module and 
                self.protocol_section.design_module.study_type)
    
    @property
    def conditions(self) -> list[str]:
        """The conditions list."""
        return ((self.protocol_section and 
                 self.protocol_section.conditions_module and 
                 self.protocol_section.conditions_module.conditions) or [])
    
    @property
    def interventions(self) -> list[str]:
        """Intervention names."""
        if not (self.protocol_section and 
                self.protocol_section.arms_interventions_module):
            return []
        return [
            intervention.name
            for intervention in self.protocol_section.arms_interventions_module.interventions
            if intervention.name
        ]
    
    @property
    def mesh_terms(self) -> list[str]:
        """Condition MeSH terms."""
        if not (self.derived_section and 
                self.derived_section.condition_browse_module):
            return []
        return [
            mesh.term
            for mesh in self.derived_section.condition_browse_module.meshes
            if mesh.term
        ]
    
    @property
    def document_files(self) -> list[str]:
        """Document filenames."""
        if not (self.document_section and 
                self.document_section.large_document_module):
            return []
        return [
            doc.filename
            for doc in self.document_section.large_document_module.large_docs
            if doc.filename
        ]
    
    @property
    def sex(self) -> Sex | None:
        """Sex eligibility."""
        return (self.protocol_section and 
                self.protocol_section.eligibility_module and 
                self.protocol_section.eligibility_module.sex)
    
    @property
    def minimum_age(self) -> str | None:
        """Minimum age."""
        return (self.protocol_section and 
                self.protocol_section.eligibility_module and 
                self.protocol_section.eligibility_module.minimum_age)
    
    @property
    def maximum_age(self) -> str | None:
        """Maximum age."""
        return (self.protocol_section and 
                self.protocol_section.eligibility_module and 
                self.protocol_section.eligibility_module.maximum_age)
    
    @property
    def healthy_volunteers(self) -> bool | None:
        """Healthy volunteers status."""
        return (self.protocol_section and 
                self.protocol_section.eligibility_module and 
                self.protocol_section.eligibility_module.healthy_volunteers)
    
    @property
    def enrollment(self) -> int | None:
        """Enrollment count."""
        return (self.protocol_section and 
                self.protocol_section.design_module and
                self.protocol_section.design_module.enrollment_info and
                self.protocol_section.design_module.enrollment_info.count)
    
    @property
    def start_date(self) -> str | None:
        """Start date."""
        return (self.protocol_section and 
                self.protocol_section.status_module and
                self.protocol_section.status_module.start_date_struct and
                self.protocol_section.status_module.start_date_struct.date)
    
    @property
    def completion_date(self) -> str | None:
        """Completion date."""
        return (self.protocol_section and 
                self.protocol_section.status_module and
                self.protocol_section.status_module.completion_date_struct and
                self.protocol_section.status_module.completion_date_struct.date)
    
    @property
    def brief_summary(self) -> str | None:
        """Brief summary."""
        return (self.protocol_section and 
                self.protocol_section.description_module and 
                self.protocol_section.description_module.brief_summary)
    
    @property
    def detailed_description(self) -> str | None:
        """Detailed description."""
        return (self.protocol_section and 
                self.protocol_section.description_module and 
                self.protocol_section.description_module.detailed_description)
    
    @property
    def phases(self) -> list[StudyPhase]:
        """Study phases."""
        return ((self.protocol_section and 
                 self.protocol_section.design_module and 
                 self.protocol_section.design_module.phases) or [])
    
    @property
    def acronym(self) -> str | None:
        """Study acronym."""
        return (self.protocol_section and 
                self.protocol_section.identification_module and 
                self.protocol_section.identification_module.acronym)