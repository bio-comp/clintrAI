"""ClinTrAI - Clinical Trials AI Data Engineering and Analysis Pipeline

A modern Python package for downloading, curating, and analyzing data from clinicaltrials.gov
"""

__version__ = "0.1.0"

from clintrai.api import create_hybrid_client, studies, stats
from clintrai.models.api_models import PagedStudies, Study

__all__ = [
    "create_hybrid_client", 
    "studies",
    "stats",
    "PagedStudies",
    "Study",
]