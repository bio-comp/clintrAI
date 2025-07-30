"""Tests for CSV clinical trial Pydantic models."""

import pytest
from datetime import date
from pydantic import ValidationError

from clintrai.models.csv_models import (
    ClinicalTrialCSVRecord,
    HarmonizedClinicalTrial,
    DocumentReference,
    DataHarmonizationStats
)
from clintrai.models.types import (
    DataSource, DocumentSource, DocumentType, StudyStatus, StudyType, 
    StudyResults, Sex, StudyPhase
)


class TestClinicalTrialCSVRecord:
    """Test cases for ClinicalTrialCSVRecord model."""
    
    def test_valid_csv_record_creation(self):
        """Test creating a valid CSV record with real data."""
        # Real data from first row of ctg-studies.csv
        csv_data = {
            "NCT Number": "NCT01588665",
            "Study Title": "Relative Contributions of Red Cell Catabolism and Dietary Absorption to Fetal Iron Accretion During Pregnancy",
            "Study URL": "https://clinicaltrials.gov/study/NCT01588665",
            "Acronym": "",
            "Study Status": "COMPLETED",
            "Brief Summary": "The two specific aims of this study are 1) to assess the relative contributions of two major maternal iron sources (i.e. dietary iron intake and red cell catabolism) at supplying iron to the fetus, and 2) to determine the impact of maternal and fetal iron status on placental transfer of these two iron sources in pregnant women and adolescents during the last trimester of pregnancy.",
            "Study Results": "NO",
            "Conditions": "Iron Deficiency",
            "Interventions": "",
            "Primary Outcome Measures": "Transfer of iron to the fetus, The delivery study will be undertaken over a 24 h period",
            "Secondary Outcome Measures": "Maternal and neonatal micronutrient status, Participants will be followed over the course of the pregnancy for an average of 28 weeks. The delivery study will be undertaken over a 24 h period.",
            "Other Outcome Measures": "",
            "Sponsor": "Cornell University",
            "Collaborators": "University of Rochester",
            "Sex": "FEMALE",
            "Age": "CHILD, ADULT",
            "Phases": "",
            "Enrollment": "23",
            "Funder Type": "OTHER",
            "Study Type": "OBSERVATIONAL",
            "Study Design": "Observational Model: |Time Perspective: p",
            "Other IDs": "IRB 1203002861",
            "Start Date": "2012-04",
            "Primary Completion Date": "2015-06",
            "Completion Date": "2022-01-20",
            "First Posted": "2012-05-01",
            "Results First Posted": "",
            "Last Update Posted": "2023-07-12",
            "Locations": "Highland Hospital, Rochester, New York, 14642, United States",
            "Study Documents": ""
        }
        
        record = ClinicalTrialCSVRecord(**csv_data)
        
        # Test core fields
        assert record.nct_number == "NCT01588665"
        assert record.study_title == "Relative Contributions of Red Cell Catabolism and Dietary Absorption to Fetal Iron Accretion During Pregnancy"
        assert str(record.study_url) == "https://clinicaltrials.gov/study/NCT01588665"
        assert record.study_status == StudyStatus.COMPLETED
        assert record.sex == Sex.FEMALE
        assert record.enrollment == 23
        
        # Test that empty strings are converted to None
        assert record.acronym is None
        assert record.interventions is None
        assert record.phases is None
        
        # Test that we can extract lists
        conditions = record.conditions_list
        assert conditions == ["Iron Deficiency"]
    
    def test_csv_record_with_pipe_separated_values(self):
        """Test CSV record with pipe-separated lists."""
        csv_data = {
            "NCT Number": "NCT03750565",
            "Study Title": "Multiple Dose Ethnobridging PK Study in Healthy Subjects",
            "Study URL": "https://clinicaltrials.gov/study/NCT03750565",
            "Study Status": "COMPLETED",
            "Conditions": "Inflammatory Bowel Diseases|IBD",
            "Interventions": "DRUG: TD-1473 - Dose A|DRUG: TD-1473 - Dose B|DRUG: TD-1473 - Dose C|DRUG: Placebo",
            "Collaborators": "Multiple Sponsors|Test University|Research Center"
        }
        
        record = ClinicalTrialCSVRecord(**csv_data)
        
        # Test extraction of pipe-separated lists
        conditions = record.conditions_list
        assert conditions == ["Inflammatory Bowel Diseases", "IBD"]
        
        interventions = record.interventions_list
        expected_interventions = [
            "DRUG: TD-1473 - Dose A",
            "DRUG: TD-1473 - Dose B", 
            "DRUG: TD-1473 - Dose C",
            "DRUG: Placebo"
        ]
        assert interventions == expected_interventions
    
    def test_nct_number_validation(self):
        """Test NCT number validation."""
        # Valid NCT number
        record = ClinicalTrialCSVRecord(nct_number="NCT01234567")
        assert record.nct_number == "NCT01234567"
        
        # Invalid NCT number (missing NCT prefix)
        with pytest.raises(ValidationError) as exc_info:
            ClinicalTrialCSVRecord(nct_number="01234567")
        assert "NCT number must start with" in str(exc_info.value)
        
        # Test case insensitivity - should be converted to uppercase
        record = ClinicalTrialCSVRecord(nct_number="nct01234567")
        assert record.nct_number == "NCT01234567"
    
    def test_document_url_extraction(self):
        """Test extraction of URLs from study documents field."""
        csv_data = {
            "NCT Number": "NCT01234567",
            "Study Documents": "Protocol: https://example.com/protocol.pdf, Results: https://example.com/results.pdf"
        }
        
        record = ClinicalTrialCSVRecord(**csv_data)
        urls = record.document_urls
        
        expected_urls = [
            "https://example.com/protocol.pdf",
            "https://example.com/results.pdf"
        ]
        assert urls == expected_urls
    
    def test_empty_study_documents(self):
        """Test handling of empty study documents field."""
        record = ClinicalTrialCSVRecord(nct_number="NCT01234567")
        
        # Test with None
        assert record.document_urls == []
        
        # Test with empty string after validation
        record.study_documents = ""
        assert record.document_urls == []


class TestHarmonizedClinicalTrial:
    """Test cases for HarmonizedClinicalTrial model."""
    
    def test_harmonized_trial_creation(self):
        """Test creating a harmonized clinical trial."""
        trial_data = {
            "nct_id": "NCT01588665",
            "data_source": DataSource.JSON_PRIORITY,
            "official_title": "Study of Iron Metabolism During Pregnancy",
            "brief_title": "Iron Study",
            "overall_status": StudyStatus.COMPLETED,
            "study_type": StudyType.OBSERVATIONAL,
            "has_results": False,
            "conditions": ["Iron Deficiency", "Pregnancy"],
            "interventions": [],
            "lead_sponsor": "Cornell University",
            "sex": Sex.FEMALE,
            "enrollment": 23
        }
        
        trial = HarmonizedClinicalTrial(**trial_data)
        
        assert trial.nct_id == "NCT01588665"
        assert trial.data_source == DataSource.JSON_PRIORITY
        assert trial.conditions == ["Iron Deficiency", "Pregnancy"]
        assert trial.interventions == []
        assert trial.has_results is False
        
        # Test helper methods
        assert trial.has_json_data is True
        assert trial.is_interventional is False
        assert trial.is_recruiting is False
        assert trial.document_count == 0
    
    def test_harmonized_trial_with_camel_case_input(self):
        """Test that camelCase input is properly converted to snake_case."""
        trial_data = {
            "nctId": "NCT01234567",
            "dataSource": "json_priority",
            "officialTitle": "Test Study",
            "overallStatus": StudyStatus.RECRUITING,
            "hasResults": True,
            "leadSponsor": "Test University"
        }
        
        trial = HarmonizedClinicalTrial(**trial_data)
        
        # Should be accessible via snake_case attributes
        assert trial.nct_id == "NCT01234567"
        assert trial.data_source == DataSource.JSON_PRIORITY
        assert trial.official_title == "Test Study"
        assert trial.overall_status == StudyStatus.RECRUITING
        assert trial.has_results is True
        assert trial.lead_sponsor == "Test University"
    
    def test_recruiting_status_detection(self):
        """Test detection of recruiting status."""
        recruiting_statuses = [
            StudyStatus.RECRUITING,
            StudyStatus.NOT_YET_RECRUITING, 
            StudyStatus.ENROLLING_BY_INVITATION
        ]
        
        for status in recruiting_statuses:
            trial = HarmonizedClinicalTrial(
                nct_id="NCT01234567",
                data_source=DataSource.CSV_ONLY,
                overall_status=status
            )
            assert trial.is_recruiting is True
        
        # Test non-recruiting status
        trial = HarmonizedClinicalTrial(
            nct_id="NCT01234567",
            data_source=DataSource.CSV_ONLY,
            overall_status=StudyStatus.COMPLETED
        )
        assert trial.is_recruiting is False
    
    def test_interventional_study_detection(self):
        """Test detection of interventional studies."""
        trial = HarmonizedClinicalTrial(
            nct_id="NCT01234567",
            data_source=DataSource.CSV_ONLY,
            study_type=StudyType.INTERVENTIONAL
        )
        assert trial.is_interventional is True
        
        trial = HarmonizedClinicalTrial(
            nct_id="NCT01234567", 
            data_source=DataSource.CSV_ONLY,
            study_type="OBSERVATIONAL"
        )
        assert trial.is_interventional is False
    
    def test_document_counting(self):
        """Test document counting functionality."""
        trial = HarmonizedClinicalTrial(
            nct_id="NCT01234567",
            data_source=DataSource.MERGED,
            document_urls=["https://example.com/protocol.pdf"],
            document_filenames=["results.pdf", "appendix.pdf"]
        )
        
        assert trial.document_count == 3


class TestDocumentReference:
    """Test cases for DocumentReference model."""
    
    def test_document_reference_creation(self):
        """Test creating a document reference."""
        doc_data = {
            "nct_id": "NCT01234567",
            "source": DocumentSource.CSV,
            "document_type": DocumentType.PROTOCOL,
            "filename": "protocol.pdf",
            "url": "https://example.com/protocol.pdf",
            "size_bytes": 1024000
        }
        
        doc = DocumentReference(**doc_data)
        
        assert doc.nct_id == "NCT01234567"
        assert doc.source == DocumentSource.CSV
        assert doc.document_type == DocumentType.PROTOCOL
        assert doc.filename == "protocol.pdf"
        assert doc.size_bytes == 1024000
        
        # Test helper methods
        assert doc.file_extension == "pdf"
        assert doc.is_pdf is True
    
    def test_file_extension_extraction(self):
        """Test file extension extraction from filename and URL."""
        # Test with filename
        doc = DocumentReference(
            nct_id="NCT01234567",
            source=DocumentSource.JSON,
            filename="study_protocol.pdf"
        )
        assert doc.file_extension == "pdf"
        
        # Test with URL when no filename
        doc = DocumentReference(
            nct_id="NCT01234567",
            source=DocumentSource.EXTERNAL,
            url="https://example.com/document.docx"
        )
        assert doc.file_extension == "docx"
        
        # Test with URL containing query parameters
        doc = DocumentReference(
            nct_id="NCT01234567",
            source=DocumentSource.EXTERNAL,
            url="https://example.com/document.pdf?version=1"
        )
        assert doc.file_extension == "pdf"
        
        # Test with no extension
        doc = DocumentReference(
            nct_id="NCT01234567",
            source=DocumentSource.CSV,
            filename="document"
        )
        assert doc.file_extension is None
    
    def test_pdf_detection(self):
        """Test PDF document detection."""
        # Test PDF file
        doc = DocumentReference(
            nct_id="NCT01234567",
            source=DocumentSource.JSON,
            filename="protocol.PDF"  # Test case insensitivity
        )
        assert doc.is_pdf is True
        
        # Test non-PDF file
        doc = DocumentReference(
            nct_id="NCT01234567",
            source=DocumentSource.CSV,
            filename="data.xlsx"
        )
        assert doc.is_pdf is False


class TestDataHarmonizationStats:
    """Test cases for DataHarmonizationStats model."""
    
    def test_stats_creation_and_calculations(self):
        """Test creating stats and calculated properties."""
        stats = DataHarmonizationStats(
            csv_study_count=1000,
            json_study_count=800,
            overlap_count=600,
            csv_only_count=400,
            json_only_count=200,
            harmonized_count=1000,
            document_url_count=300
        )
        
        assert stats.csv_study_count == 1000
        assert stats.overlap_count == 600
        assert stats.harmonized_count == 1000
        
        # Test calculated properties
        assert stats.overlap_percentage == 60.0  # 600/1000 * 100
        assert stats.json_coverage_percentage == 80.0  # 800/1000 * 100
    
    def test_stats_with_zero_csv_studies(self):
        """Test stats calculations when no CSV studies exist."""
        stats = DataHarmonizationStats(
            csv_study_count=0,
            json_study_count=100,
            overlap_count=0,
            csv_only_count=0,
            json_only_count=100,
            harmonized_count=100,
            document_url_count=50
        )
        
        # Should handle division by zero gracefully
        assert stats.overlap_percentage == 0.0
        assert stats.json_coverage_percentage == 0.0
    
    def test_stats_with_processing_errors(self):
        """Test stats with processing errors tracking."""
        stats = DataHarmonizationStats(
            csv_study_count=100,
            json_study_count=80,
            overlap_count=60,
            csv_only_count=40,
            json_only_count=20,
            harmonized_count=95,  # 5 failed to harmonize
            document_url_count=30,
            processing_errors=5
        )
        
        assert stats.processing_errors == 5
        assert stats.harmonized_count == 95