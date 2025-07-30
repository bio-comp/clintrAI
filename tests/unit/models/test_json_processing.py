"""Tests for JSON clinical trial data processing and validation."""

import json
import pytest
from pathlib import Path

from clintrai.airflow.operators.preparation import (
    get_nested_val,
    _flatten_json_record
)
from clintrai.models.types import JSONFieldPath, StudyStatus, StudyType, Sex, StudyPhase


class TestJSONProcessing:
    """Test cases for JSON data processing functions."""
    
    @pytest.fixture
    def sample_json_data(self):
        """Real JSON data structure from NCT04619758."""
        return {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT04619758",
                    "orgStudyIdInfo": {"id": "819/RC/KEMU"},
                    "organization": {
                        "fullName": "King Edward Medical University",
                        "class": "OTHER"
                    },
                    "briefTitle": "Emollient Therapy In Preterm & Low Birth Weight Neonates: A Randomized Clinical Trial",
                    "officialTitle": "Emollient Therapy In Preterm & Low Birth Weight Neonates: A Randomized Clinical Trial"
                },
                "statusModule": {
                    "statusVerifiedDate": "2020-11",
                    "overallStatus": StudyStatus.COMPLETED,
                    "expandedAccessInfo": {"hasExpandedAccess": False},
                    "startDateStruct": {"date": "2018-01-01", "type": "ACTUAL"},
                    "primaryCompletionDateStruct": {"date": "2018-06-30", "type": "ACTUAL"},
                    "completionDateStruct": {"date": "2018-06-30", "type": "ACTUAL"}
                },
                "descriptionModule": {
                    "briefSummary": "The objective of this study is to assess the impact of emollient therapy on gain in weight and length among preterm and low birth weight babies.",
                    "detailedDescription": "The study will be conducted at the Department of Pediatric Medicine unit 1, KEMU / Mayo Hospital Lahore. Total of 140 neonates fulfilling the eligibility criteria will be enrolled."
                },
                "conditionsModule": {
                    "conditions": ["Weight Gain"],
                    "keywords": ["Emollient Low birth weight Preterm Weight Length."]
                },
                "designModule": {
                    "studyType": StudyType.INTERVENTIONAL,
                    "phases": [StudyPhase.NA],
                    "enrollmentInfo": {"count": 140, "type": "ACTUAL"}
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {
                            "type": "OTHER",
                            "name": "Emollient (sunflower oil)",
                            "description": "In group A, mothers will be advised to massage their babies with sunflower oil",
                            "armGroupLabels": ["Emollient Group"]
                        }
                    ]
                },
                "eligibilityModule": {
                    "sex": Sex.ALL,
                    "minimumAge": "1 Day",
                    "maximumAge": "28 Days",
                    "healthyVolunteers": True
                }
            },
            "derivedSection": {
                "conditionBrowseModule": {
                    "meshes": [
                        {"id": "D001835", "term": "Body Weight"},
                        {"id": "D015430", "term": "Weight Gain"}
                    ]
                }
            },
            "documentSection": {
                "largeDocumentModule": {
                    "largeDocs": [
                        {"filename": "protocol_v1.pdf"},
                        {"filename": "statistical_analysis_plan.pdf"}
                    ]
                }
            },
            "hasResults": False
        }
    
    def test_get_nested_val_success(self, sample_json_data):
        """Test successful nested value extraction."""
        # Test simple nested access
        nct_id = get_nested_val(sample_json_data, ["protocolSection", "identificationModule", "nctId"])
        assert nct_id == "NCT04619758"
        
        # Test deeper nesting
        org_name = get_nested_val(sample_json_data, ["protocolSection", "identificationModule", "organization", "fullName"])
        assert org_name == "King Edward Medical University"
        
        # Test list access
        condition = get_nested_val(sample_json_data, ["protocolSection", "conditionsModule", "conditions"])
        assert condition == ["Weight Gain"]
    
    def test_get_nested_val_missing_key(self, sample_json_data):
        """Test nested value extraction with missing keys."""
        # Test missing intermediate key
        result = get_nested_val(sample_json_data, ["protocolSection", "missingModule", "someField"])
        assert result is None
        
        # Test missing final key
        result = get_nested_val(sample_json_data, ["protocolSection", "identificationModule", "missingField"])
        assert result is None
        
        # Test completely wrong path
        result = get_nested_val(sample_json_data, ["wrongSection", "wrongModule"])
        assert result is None
    
    def test_get_nested_val_type_error(self):
        """Test nested value extraction with type errors."""
        # Test accessing key on non-dict
        data = {"field": "string_value"}
        result = get_nested_val(data, ["field", "subfield"])
        assert result is None
        
        # Test with None value
        data = {"field": None}
        result = get_nested_val(data, ["field", "subfield"])
        assert result is None
    
    def test_flatten_json_record_complete(self, sample_json_data):
        """Test complete JSON record flattening with real data."""
        nct_id = "NCT04619758"
        flattened = _flatten_json_record(nct_id, sample_json_data)
        
        # Test basic identification fields
        assert flattened["json_nct_id"] == "NCT04619758"
        assert flattened["json_official_title"] == "Emollient Therapy In Preterm & Low Birth Weight Neonates: A Randomized Clinical Trial"
        assert flattened["json_brief_title"] == "Emollient Therapy In Preterm & Low Birth Weight Neonates: A Randomized Clinical Trial"
        
        # Test status fields
        assert flattened["json_overall_status"] == StudyStatus.COMPLETED
        assert flattened["json_study_type"] == StudyType.INTERVENTIONAL
        assert flattened["json_has_results"] is False
        
        # Test description fields
        assert "impact of emollient therapy" in flattened["json_brief_summary"]
        assert "Department of Pediatric Medicine" in flattened["json_detailed_description"]
        
        # Test conditions and interventions
        assert flattened["json_conditions"] == ["Weight Gain"]
        assert len(flattened["json_interventions"]) == 1
        assert flattened["json_interventions"][0] == "Emollient (sunflower oil)"
        
        # Test MeSH terms
        assert len(flattened["json_condition_meshes"]) == 2
        assert "Body Weight" in flattened["json_condition_meshes"]
        assert "Weight Gain" in flattened["json_condition_meshes"]
        
        # Test eligibility fields
        assert flattened["json_sex"] == Sex.ALL
        assert flattened["json_minimum_age"] == "1 Day"
        assert flattened["json_maximum_age"] == "28 Days"
        assert flattened["json_healthy_volunteers"] is True
        
        # Test enrollment
        assert flattened["json_enrollment"] == 140
        
        # Test dates
        assert flattened["json_start_date"] == "2018-01-01"
        assert flattened["json_completion_date"] == "2018-06-30"
        
        # Test document files
        assert len(flattened["json_document_files"]) == 2
        assert "protocol_v1.pdf" in flattened["json_document_files"]
        assert "statistical_analysis_plan.pdf" in flattened["json_document_files"]
    
    def test_flatten_json_record_missing_sections(self):
        """Test JSON flattening with missing sections."""
        minimal_data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT99999999",
                    "briefTitle": "Minimal Study"
                }
            },
            "hasResults": True
        }
        
        nct_id = "NCT99999999"
        flattened = _flatten_json_record(nct_id, minimal_data)
        
        # Test that basic fields are extracted
        assert flattened["json_nct_id"] == "NCT99999999"
        assert flattened["json_brief_title"] == "Minimal Study"
        assert flattened["json_has_results"] is True
        
        # Test that missing fields are None or empty lists
        assert flattened["json_official_title"] is None
        assert flattened["json_overall_status"] is None
        assert flattened["json_conditions"] == []
        assert flattened["json_interventions"] == []
        assert flattened["json_condition_meshes"] == []
        assert flattened["json_document_files"] == []
        
        # Test missing dates
        assert flattened["json_start_date"] is None
        assert flattened["json_completion_date"] is None
    
    def test_flatten_json_record_interventions_extraction(self):
        """Test intervention name extraction from complex structure."""
        data_with_interventions = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678"},
                "armsInterventionsModule": {
                    "interventions": [
                        {"type": "DRUG", "name": "Drug A", "dosage": "10mg"},
                        {"type": "DRUG", "name": "Drug B", "dosage": "20mg"},
                        {"type": "PROCEDURE", "name": "Surgery"},
                        {"type": "OTHER"},  # Missing name
                        {"name": "Behavioral Intervention"}  # Missing type
                    ]
                }
            },
            "hasResults": False
        }
        
        flattened = _flatten_json_record("NCT12345678", data_with_interventions)
        
        # Should extract only interventions with names
        expected_interventions = ["Drug A", "Drug B", "Surgery", "Behavioral Intervention"]
        assert flattened["json_interventions"] == expected_interventions
    
    def test_flatten_json_record_mesh_terms_extraction(self):
        """Test MeSH term extraction from derived section."""
        data_with_mesh = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678"}
            },
            "derivedSection": {
                "conditionBrowseModule": {
                    "meshes": [
                        {"id": "D123", "term": "Diabetes"},
                        {"id": "D456", "term": "Hypertension"},
                        {"id": "D789"},  # Missing term
                        {"term": "Heart Disease"}  # Missing id
                    ]
                }
            },
            "hasResults": False
        }
        
        flattened = _flatten_json_record("NCT12345678", data_with_mesh)
        
        # Should extract only terms that exist
        expected_terms = ["Diabetes", "Hypertension", "Heart Disease"]
        assert flattened["json_condition_meshes"] == expected_terms
    
    def test_flatten_json_record_document_files_extraction(self):
        """Test document filename extraction."""
        data_with_docs = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678"}
            },
            "documentSection": {
                "largeDocumentModule": {
                    "largeDocs": [
                        {"filename": "protocol.pdf", "size": 1024},
                        {"filename": "consent_form.pdf"},
                        {"size": 2048},  # Missing filename
                        {"filename": "appendix.docx", "version": "1.0"}
                    ]
                }
            },
            "hasResults": False
        }
        
        flattened = _flatten_json_record("NCT12345678", data_with_docs)
        
        # Should extract only filenames that exist
        expected_files = ["protocol.pdf", "consent_form.pdf", "appendix.docx"]
        assert flattened["json_document_files"] == expected_files
    
    def test_flatten_json_record_empty_lists_and_nulls(self):
        """Test handling of empty lists and null values."""
        data_with_empties = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678"},
                "conditionsModule": {"conditions": []},
                "armsInterventionsModule": {"interventions": []},
                "designModule": {"phases": None}
            },
            "derivedSection": {
                "conditionBrowseModule": {"meshes": []}
            },
            "documentSection": {
                "largeDocumentModule": {"largeDocs": []}
            },
            "hasResults": False
        }
        
        flattened = _flatten_json_record("NCT12345678", data_with_empties)
        
        # Test that empty lists are preserved as empty lists
        assert flattened["json_conditions"] == []
        assert flattened["json_interventions"] == []
        assert flattened["json_condition_meshes"] == []
        assert flattened["json_document_files"] == []
        
        # Test that None values become empty lists where expected
        assert flattened["json_phases"] == []


class TestJSONFieldPathConstants:
    """Test that JSONFieldPath constants match actual JSON structure."""
    
    @pytest.fixture
    def sample_json_data(self):
        """Sample JSON data for testing field paths."""
        return {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT04619758",
                    "officialTitle": "Test Official Title",
                    "briefTitle": "Test Brief Title"
                },
                "statusModule": {
                    "overallStatus": StudyStatus.COMPLETED,
                    "startDateStruct": {"date": "2018-01-01"},
                    "completionDateStruct": {"date": "2018-06-30"}
                },
                "descriptionModule": {},
                "conditionsModule": {},
                "designModule": {
                    "studyType": StudyType.INTERVENTIONAL,
                    "phases": ["NA"]
                },
                "armsInterventionsModule": {},
                "eligibilityModule": {}
            },
            "derivedSection": {
                "conditionBrowseModule": {}
            },
            "documentSection": {
                "largeDocumentModule": {}
            },
            "hasResults": False
        }
    
    def test_json_field_paths_validity(self, sample_json_data):
        """Test that JSONFieldPath constants work with real data."""
        # Test top-level sections
        assert JSONFieldPath.PROTOCOL_SECTION.value in sample_json_data
        assert JSONFieldPath.DERIVED_SECTION.value in sample_json_data
        assert JSONFieldPath.DOCUMENT_SECTION.value in sample_json_data
        assert JSONFieldPath.HAS_RESULTS.value in sample_json_data
        
        protocol = sample_json_data[JSONFieldPath.PROTOCOL_SECTION.value]
        
        # Test protocol section modules
        assert JSONFieldPath.IDENTIFICATION_MODULE.value in protocol
        assert JSONFieldPath.STATUS_MODULE.value in protocol
        assert JSONFieldPath.DESCRIPTION_MODULE.value in protocol
        assert JSONFieldPath.CONDITIONS_MODULE.value in protocol
        assert JSONFieldPath.DESIGN_MODULE.value in protocol
        assert JSONFieldPath.ARMS_INTERVENTIONS_MODULE.value in protocol
        assert JSONFieldPath.ELIGIBILITY_MODULE.value in protocol
        
        # Test specific field paths work
        id_module = protocol[JSONFieldPath.IDENTIFICATION_MODULE.value]
        assert JSONFieldPath.OFFICIAL_TITLE.value in id_module
        assert JSONFieldPath.BRIEF_TITLE.value in id_module
        
        status_module = protocol[JSONFieldPath.STATUS_MODULE.value]
        assert JSONFieldPath.OVERALL_STATUS.value in status_module
        assert JSONFieldPath.START_DATE_STRUCT.value in status_module
        assert JSONFieldPath.COMPLETION_DATE_STRUCT.value in status_module
        
        # Test nested date structure
        start_date_struct = status_module[JSONFieldPath.START_DATE_STRUCT.value]
        assert JSONFieldPath.DATE.value in start_date_struct