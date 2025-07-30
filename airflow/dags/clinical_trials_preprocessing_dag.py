"""
Clinical Trials Data Preprocessing Pipeline DAG

This DAG orchestrates the complete data harmonization and NLP preprocessing
pipeline for clinical trials data, including CSV/JSON harmonization,
document fetching, text processing, and ML feature generation.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.dask.operators.dask import DaskOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup

# Import our custom operators
from clintrai.airflow.operators.data_harmonization import DataHarmonizationOperator
from clintrai.airflow.operators.document_fetcher import DocumentFetcherOperator
from clintrai.airflow.operators.nlp_processor import NLPProcessorOperator
from clintrai.airflow.operators.text_augmentation import TextAugmentationOperator
from clintrai.airflow.operators.iceberg_storage import IcebergStorageOperator


# Default arguments for all tasks
default_args = {
    'owner': 'clintrai-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}

# DAG configuration
dag = DAG(
    'clinical_trials_preprocessing',
    default_args=default_args,
    description='Complete clinical trials data preprocessing pipeline',
    schedule_interval='@daily',  # Run daily to process new data
    max_active_runs=1,
    catchup=False,
    tags=['clinical-trials', 'nlp', 'data-processing'],
)

# Configuration for data paths
DATA_CONFIG = {
    'csv_path': '/home/mike/repos/clinTrAI/data/ctg-studies.csv',
    'json_dir': '/home/mike/repos/clinTrAI/data/studies',
    'output_dir': '/home/mike/repos/clinTrAI/data/processed',
    'batch_size': 1000,
    'shard_count': 256,
}

# =====================================================================
# TASK GROUP 1: DATA INGESTION AND VALIDATION
# =====================================================================

with TaskGroup("data_ingestion", dag=dag) as data_ingestion_group:
    
    validate_data_sources = PythonOperator(
        task_id='validate_data_sources',
        python_callable='clintrai.airflow.tasks.data_validation.validate_data_sources',
        op_kwargs=DATA_CONFIG,
    )
    
    analyze_data_overlap = DataHarmonizationOperator(
        task_id='analyze_data_overlap',
        csv_path=DATA_CONFIG['csv_path'],
        json_dir=DATA_CONFIG['json_dir'],
        output_path=f"{DATA_CONFIG['output_dir']}/overlap_analysis.json",
    )
    
    extract_document_urls = PythonOperator(
        task_id='extract_document_urls',
        python_callable='clintrai.airflow.tasks.url_extraction.extract_document_urls',
        op_kwargs={
            'csv_path': DATA_CONFIG['csv_path'],
            'output_path': f"{DATA_CONFIG['output_dir']}/document_urls.jsonl",
        },
    )
    
    validate_data_sources >> [analyze_data_overlap, extract_document_urls]

# =====================================================================
# TASK GROUP 2: DATA HARMONIZATION AND DEDUPLICATION
# =====================================================================

with TaskGroup("data_harmonization", dag=dag) as harmonization_group:
    
    harmonize_csv_json = DataHarmonizationOperator(
        task_id='harmonize_csv_json',
        csv_path=DATA_CONFIG['csv_path'],
        json_dir=DATA_CONFIG['json_dir'],
        output_path=f"{DATA_CONFIG['output_dir']}/harmonized_studies.parquet",
        deduplication_strategy='json_priority',
    )
    
    shard_data = PythonOperator(
        task_id='shard_data',
        python_callable='clintrai.airflow.tasks.data_sharding.create_md5_shards',
        op_kwargs={
            'input_path': f"{DATA_CONFIG['output_dir']}/harmonized_studies.parquet",
            'output_dir': f"{DATA_CONFIG['output_dir']}/sharded",
            'shard_count': DATA_CONFIG['shard_count'],
        },
    )
    
    harmonize_csv_json >> shard_data

# =====================================================================
# TASK GROUP 3: DOCUMENT FETCHING AND PROCESSING
# =====================================================================

with TaskGroup("document_processing", dag=dag) as document_group:
    
    fetch_documents = DocumentFetcherOperator(
        task_id='fetch_documents',
        url_file=f"{DATA_CONFIG['output_dir']}/document_urls.jsonl",
        output_dir=f"{DATA_CONFIG['output_dir']}/documents",
        max_concurrent=50,  # Limit concurrent downloads
        rate_limit_delay=0.1,  # 100ms between requests
    )
    
    parse_documents = PythonOperator(
        task_id='parse_documents',
        python_callable='clintrai.airflow.tasks.document_parsing.parse_pdf_documents',
        op_kwargs={
            'documents_dir': f"{DATA_CONFIG['output_dir']}/documents",
            'output_path': f"{DATA_CONFIG['output_dir']}/extracted_text.parquet",
        },
    )
    
    fetch_documents >> parse_documents

# =====================================================================
# TASK GROUP 4: NLP PREPROCESSING
# =====================================================================

with TaskGroup("nlp_preprocessing", dag=dag) as nlp_group:
    
    # Create dynamic tasks for each shard
    preprocess_tasks = []
    for shard_id in range(DATA_CONFIG['shard_count']):
        preprocess_task = NLPProcessorOperator(
            task_id=f'preprocess_shard_{shard_id:03d}',
            shard_path=f"{DATA_CONFIG['output_dir']}/sharded/shard_{shard_id:03d}.parquet",
            output_path=f"{DATA_CONFIG['output_dir']}/nlp_processed/shard_{shard_id:03d}.parquet",
            processing_steps=[
                'clean_text',
                'tokenize',
                'remove_stopwords',
                'generate_tfidf',
                'calculate_lexical_diversity',
                'extract_trigrams',
            ],
            batch_size=DATA_CONFIG['batch_size'],
        )
        preprocess_tasks.append(preprocess_task)
    
    # Combine results from all shards
    combine_nlp_results = PythonOperator(
        task_id='combine_nlp_results',
        python_callable='clintrai.airflow.tasks.data_combination.combine_processed_shards',
        op_kwargs={
            'input_dir': f"{DATA_CONFIG['output_dir']}/nlp_processed",
            'output_path': f"{DATA_CONFIG['output_dir']}/nlp_combined.parquet",
        },
    )
    
    preprocess_tasks >> combine_nlp_results

# =====================================================================
# TASK GROUP 5: TEXT AUGMENTATION AND MULTILINGUAL PROCESSING
# =====================================================================

with TaskGroup("text_augmentation", dag=dag) as augmentation_group:
    
    spanish_translation = TextAugmentationOperator(
        task_id='spanish_translation',
        input_path=f"{DATA_CONFIG['output_dir']}/nlp_combined.parquet",
        output_path=f"{DATA_CONFIG['output_dir']}/spanish_translations.parquet",
        augmentation_type='translation',
        target_language='es',
        batch_size=100,  # Smaller batches for translation
    )
    
    generate_paraphrases = TextAugmentationOperator(
        task_id='generate_paraphrases',
        input_path=f"{DATA_CONFIG['output_dir']}/nlp_combined.parquet",
        output_path=f"{DATA_CONFIG['output_dir']}/paraphrases.parquet",
        augmentation_type='paraphrase',
        model_name='t5-base',
        batch_size=50,  # GPU memory constraints
    )
    
    extract_synonyms = TextAugmentationOperator(
        task_id='extract_synonyms',
        input_path=f"{DATA_CONFIG['output_dir']}/nlp_combined.parquet",
        output_path=f"{DATA_CONFIG['output_dir']}/synonyms.parquet",
        augmentation_type='synonyms',
        source='wordnet',
        batch_size=1000,
    )
    
    generate_embeddings = TextAugmentationOperator(
        task_id='generate_embeddings',
        input_path=f"{DATA_CONFIG['output_dir']}/nlp_combined.parquet",
        output_path=f"{DATA_CONFIG['output_dir']}/embeddings.parquet",
        augmentation_type='embeddings',
        model_name='sentence-transformers/all-MiniLM-L6-v2',
        batch_size=100,
    )
    
    # Run translation and paraphrasing in parallel, then embeddings
    [spanish_translation, generate_paraphrases, extract_synonyms] >> generate_embeddings

# =====================================================================
# TASK GROUP 6: DATA STORAGE AND INDEXING
# =====================================================================

with TaskGroup("data_storage", dag=dag) as storage_group:
    
    store_iceberg_tables = IcebergStorageOperator(
        task_id='store_iceberg_tables',
        input_files=[
            f"{DATA_CONFIG['output_dir']}/nlp_combined.parquet",
            f"{DATA_CONFIG['output_dir']}/spanish_translations.parquet",
            f"{DATA_CONFIG['output_dir']}/paraphrases.parquet",
            f"{DATA_CONFIG['output_dir']}/synonyms.parquet",
        ],
        catalog_path=f"{DATA_CONFIG['output_dir']}/iceberg_catalog",
        table_prefix='clinical_trials',
    )
    
    store_vector_embeddings = PythonOperator(
        task_id='store_vector_embeddings',
        python_callable='clintrai.airflow.tasks.vector_storage.store_embeddings',
        op_kwargs={
            'embeddings_path': f"{DATA_CONFIG['output_dir']}/embeddings.parquet",
            'postgres_conn_id': 'postgres_vectordb',
            'table_name': 'clinical_trial_embeddings',
        },
    )
    
    create_model_deltas = PythonOperator(
        task_id='create_model_deltas',
        python_callable='clintrai.airflow.tasks.versioning.create_delta_versions',
        op_kwargs={
            'processed_data_dir': f"{DATA_CONFIG['output_dir']}",
            'delta_storage_dir': f"{DATA_CONFIG['output_dir']}/deltas",
            'base_version_hash': '{{ ds }}',  # Use execution date as version
        },
    )
    
    [store_iceberg_tables, store_vector_embeddings] >> create_model_deltas

# =====================================================================
# TASK GROUP 7: VALIDATION AND QUALITY CHECKS
# =====================================================================

with TaskGroup("validation", dag=dag) as validation_group:
    
    validate_data_quality = PythonOperator(
        task_id='validate_data_quality',
        python_callable='clintrai.airflow.tasks.validation.validate_processed_data',
        op_kwargs={
            'processed_data_dir': f"{DATA_CONFIG['output_dir']}",
            'quality_thresholds': {
                'min_studies_processed': 100000,
                'max_error_rate': 0.05,
                'min_translation_quality': 0.8,
            },
        },
    )
    
    generate_processing_report = PythonOperator(
        task_id='generate_processing_report',
        python_callable='clintrai.airflow.tasks.reporting.generate_pipeline_report',
        op_kwargs={
            'execution_date': '{{ ds }}',
            'processed_data_dir': f"{DATA_CONFIG['output_dir']}",
            'report_output_path': f"{DATA_CONFIG['output_dir']}/reports/pipeline_report_{{{{ ds }}}}.json",
        },
    )
    
    validate_data_quality >> generate_processing_report

# =====================================================================
# PIPELINE ORCHESTRATION
# =====================================================================

start_pipeline = DummyOperator(task_id='start_pipeline', dag=dag)
end_pipeline = DummyOperator(task_id='end_pipeline', dag=dag)

# Define task dependencies
start_pipeline >> data_ingestion_group
data_ingestion_group >> harmonization_group
harmonization_group >> [document_group, nlp_group]
[document_group, nlp_group] >> augmentation_group
augmentation_group >> storage_group
storage_group >> validation_group
validation_group >> end_pipeline

# =====================================================================
# DAG CONFIGURATION AND MONITORING
# =====================================================================

# Set up monitoring and alerting
dag.doc_md = """
# Clinical Trials Preprocessing Pipeline

This DAG processes clinical trials data through the following stages:

1. **Data Ingestion**: Validate sources and analyze overlap between CSV/JSON
2. **Harmonization**: Merge and deduplicate data from multiple sources
3. **Document Processing**: Fetch and parse external documents (PDFs)
4. **NLP Preprocessing**: Clean text, generate TF-IDF, extract features
5. **Text Augmentation**: Translation, paraphrasing, synonyms, embeddings
6. **Storage**: Save to Iceberg tables and vector database
7. **Validation**: Quality checks and reporting

## Resource Requirements
- **CPU**: AMD multi-core for parallel processing
- **GPU**: RTX 4090 for ML model inference
- **Memory**: 32GB+ recommended for large dataset processing
- **Storage**: 100GB+ for intermediate files

## Monitoring
- Task execution times and resource usage
- Data quality metrics and error rates
- Pipeline success/failure alerts
"""