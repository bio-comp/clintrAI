"""Tests for JSON clinical trial data processing and validation."""

import json
import pytest
from pathlib import Path

from clintrai.airflow.operators.preparation import _flatten_json_record
from clintrai.models.json_models import ClinicalTrialJSONRecord
from clintrai.models.types import StudyStatus, StudyType, Sex, StudyPhase


class TestJSONModels:
    """Test cases for JSON Pydantic models."""
    
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
    
    def test_json_record_validation_success(self, sample_json_data):
        """Test successful JSON record validation with Pydantic model."""
        record = ClinicalTrialJSONRecord(**sample_json_data)
        
        # Test basic identification fields
        assert record.nct_id == "NCT04619758"
        assert record.official_title == "Emollient Therapy In Preterm & Low Birth Weight Neonates: A Randomized Clinical Trial"
        assert record.brief_title == "Emollient Therapy In Preterm & Low Birth Weight Neonates: A Randomized Clinical Trial"
        
        # Test status fields
        assert record.overall_status == StudyStatus.COMPLETED
        assert record.study_type == StudyType.INTERVENTIONAL
        assert record.has_results is False
        
        # Test description fields
        assert "impact of emollient therapy" in record.brief_summary
        assert "Department of Pediatric Medicine" in record.detailed_description
        
        # Test conditions and interventions
        assert record.conditions == ["Weight Gain"]
        assert len(record.interventions) == 1
        assert record.interventions[0] == "Emollient (sunflower oil)"
        
        # Test MeSH terms
        assert len(record.mesh_terms) == 2
        assert "Body Weight" in record.mesh_terms
        assert "Weight Gain" in record.mesh_terms
        
        # Test eligibility fields
        assert record.sex == Sex.ALL
        assert record.minimum_age == "1 Day"
        assert record.maximum_age == "28 Days"
        assert record.healthy_volunteers is True
        
        # Test enrollment
        assert record.enrollment == 140
        
        # Test dates
        assert record.start_date == "2018-01-01"
        assert record.completion_date == "2018-06-30"
        
        # Test document files
        assert len(record.document_files) == 2
        assert "protocol_v1.pdf" in record.document_files
        assert "statistical_analysis_plan.pdf" in record.document_files
        
        # Test phases
        assert len(record.phases) == 1
        assert record.phases[0] == StudyPhase.NA
    
    def test_json_record_missing_sections(self):
        """Test JSON record with missing sections."""
        minimal_data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT99999999",
                    "briefTitle": "Minimal Study"
                }
            },
            "hasResults": True
        }
        
        record = ClinicalTrialJSONRecord(**minimal_data)
        
        # Test that basic fields are extracted
        assert record.nct_id == "NCT99999999"
        assert record.brief_title == "Minimal Study"
        assert record.has_results is True
        
        # Test that missing fields are None or empty lists
        assert record.official_title is None
        assert record.overall_status is None
        assert record.conditions == []
        assert record.interventions == []
        assert record.mesh_terms == []
        assert record.document_files == []
        
        # Test missing dates
        assert record.start_date is None
        assert record.completion_date is None
    
    def test_flatten_json_record_with_pydantic_model(self, sample_json_data):
        """Test flattening with validated Pydantic model."""
        record = ClinicalTrialJSONRecord(**sample_json_data)
        nct_id = "NCT04619758"
        flattened = _flatten_json_record(nct_id, record)
        
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
    
    def test_interventions_extraction(self):
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
        
        record = ClinicalTrialJSONRecord(**data_with_interventions)
        
        # Should extract only interventions with names
        expected_interventions = ["Drug A", "Drug B", "Surgery", "Behavioral Intervention"]
        assert record.interventions == expected_interventions
    
    def test_mesh_terms_extraction(self):
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
        
        record = ClinicalTrialJSONRecord(**data_with_mesh)
        
        # Should extract only terms that exist
        expected_terms = ["Diabetes", "Hypertension", "Heart Disease"]
        assert record.mesh_terms == expected_terms
    
    def test_document_files_extraction(self):
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
        
        record = ClinicalTrialJSONRecord(**data_with_docs)
        
        # Should extract only filenames that exist
        expected_files = ["protocol.pdf", "consent_form.pdf", "appendix.docx"]
        assert record.document_files == expected_files
    
    def test_empty_lists_and_nulls(self):
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
        
        record = ClinicalTrialJSONRecord(**data_with_empties)
        
        # Test that empty lists are preserved as empty lists
        assert record.conditions == []
        assert record.interventions == []
        assert record.mesh_terms == []
        assert record.document_files == []
        
        # Test that None values become empty lists where expected
        assert record.phases == []
    
    def test_phase_mapping_validation(self):
        """Test that phase mapping works correctly."""
        data_with_phases = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT12345678"},
                "designModule": {
                    "phases": ["PHASE1", "PHASE2", "PHASE 3", "INVALID_PHASE"]
                }
            },
            "hasResults": False
        }
        
        record = ClinicalTrialJSONRecord(**data_with_phases)
        
        # Test phase mapping
        expected_phases = [StudyPhase.PHASE_1, StudyPhase.PHASE_2, StudyPhase.PHASE_3, StudyPhase.NA]
        assert record.phases == expected_phases


class TestRealJSONFiles:
    """Test with actual JSON files from the dataset."""
    
    def test_real_json_file_validation(self):
        """Test validation with real JSON files."""
        test_files = [
            "NCT00000102.json",
            "NCT00001500.json", 
            "NCT00000122.json"
        ]
        
        for filename in test_files:
            file_path = Path("data/studies") / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Should validate without errors
                record = ClinicalTrialJSONRecord(**data)
                
                # Basic sanity checks
                assert record.nct_id is not None
                assert record.nct_id.startswith("NCT")
                
                # Should be able to flatten
                flattened = _flatten_json_record(record.nct_id, record)
                assert flattened["json_nct_id"] == record.nct_id