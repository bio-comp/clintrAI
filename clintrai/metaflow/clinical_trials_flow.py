# clintrai/metaflow/clinical_trials_flow.py
"""Clinical trials data processing pipeline using Metaflow."""

import json
from datetime import datetime
from pathlib import Path

import polars as pl
from loguru import logger
from metaflow import (
    FlowSpec,
    Parameter,
    catch,
    current,
    environment,
    project,
    resources,
    retry,
    schedule,
    step,
)

from clintrai.config import settings
from clintrai.metaflow.embeddings import generate_embeddings
from clintrai.metaflow.harmonization import (
    analyze_overlap,
    create_shards,
    harmonize_data,
)
from clintrai.metaflow.nlp_processing import (
    combine_nlp_results,
    get_stopwords,
    load_spacy_model,
    process_shard,
)
from clintrai.models.types import DeduplicationStrategy


@project(name="clinical_trials")
@schedule(daily=True)
class ClinicalTrialsFlow(FlowSpec):
    """
    Clinical trials data processing pipeline.
    
    Processes clinical trials data through:
    1. Data ingestion and validation
    2. Data harmonization and deduplication
    3. NLP preprocessing (distributed)
    4. Text embedding generation
    5. Quality validation
    """
    
    # Parameters
    csv_path = Parameter(
        "csv_path",
        help="Path to the CSV file with clinical trials data",
        required=True,
    )
    
    json_dir = Parameter(
        "json_dir",
        help="Directory containing JSON study files",
        required=True,
    )
    
    output_dir = Parameter(
        "output_dir",
        help="Directory for processed output files",
        default="./processed_output",
    )
    
    # Configuration loaded from centralized settings
    # These can still be overridden via Parameters if needed for specific runs
    
    @step
    def start(self):
        """Initialize the flow and validate input data sources."""
        logger.info(f"Starting Clinical Trials Pipeline - {datetime.now()}")
        logger.info(f"Flow ID: {current.run_id}")
        
        # Convert parameters to proper types
        self.csv_path_obj = Path(self.csv_path)
        self.json_dir_obj = Path(self.json_dir)
        self.output_dir_obj = Path(self.output_dir)
        
        # Load configuration from centralized settings
        self.dedup_strategy_enum = settings.processing.dedup_strategy
        self.shard_count = settings.processing.shard_count
        self.enable_gpu = settings.processing.enable_gpu
        self.save_intermediate_shards = settings.processing.save_intermediate_shards
        
        # Validate paths
        if not self.csv_path_obj.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        if not self.json_dir_obj.exists():
            raise FileNotFoundError(f"JSON directory not found: {self.json_dir}")
        
        # Create and validate output directory (moved from config validation)
        self.output_dir_obj.mkdir(parents=True, exist_ok=True)
        if self.output_dir_obj.exists() and not self.output_dir_obj.is_dir():
            raise ValueError(f"Output path {self.output_dir_obj} exists but is not a directory")
        
        # Ensure other configured directories exist if needed
        settings.models.model_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Store configuration from settings and run parameters
        self.config = {
            "csv_path": str(self.csv_path_obj),
            "json_dir": str(self.json_dir_obj),
            "output_dir": str(self.output_dir_obj),
            "dedup_strategy": self.dedup_strategy_enum.value,
            "shard_count": self.shard_count,
            "enable_gpu": self.enable_gpu,
            "save_intermediate_shards": self.save_intermediate_shards,
            "environment": settings.environment,
            "run_id": current.run_id,
            "timestamp": datetime.now().isoformat(),
            "settings_snapshot": {
                "processing": settings.processing.model_dump(),
                "models": settings.models.model_dump(),
                "quality": settings.quality.model_dump(),
                "metaflow": settings.metaflow.model_dump(),
            },
        }
        
        logger.info("Validation complete")
        self.next(self.analyze_data_overlap)
    
    @step
    def analyze_data_overlap(self):
        """Analyze overlap between CSV and JSON data sources."""
        self.overlap_stats = analyze_overlap(
            self.csv_path_obj,
            self.json_dir_obj
        )
        self.next(self.harmonize_data)
    
    @step
    @resources(
        cpu=settings.metaflow.default_cpu * 2,  # Use more CPU for harmonization
        memory=settings.metaflow.default_memory * 2
    )
    @retry(times=settings.metaflow.max_retry_attempts)
    def harmonize_data(self):
        """Harmonize CSV and JSON data."""
        self.harmonized_df, self.harmonization_stats = harmonize_data(
            self.csv_path_obj,
            self.json_dir_obj,
            self.overlap_stats,
            self.dedup_strategy_enum
        )
        
        # Optional: Save harmonized data for inspection (not required for flow)
        output_path = self.output_dir_obj / "harmonized_studies.parquet"
        self.harmonized_df.write_parquet(output_path)
        self.harmonization_stats["output_path"] = str(output_path)
        
        self.next(self.create_shards)
    
    @step
    def create_shards(self):
        """Create data shards for parallel processing."""
        self.shards = create_shards(
            self.harmonized_df,
            self.shard_count,
            self.output_dir_obj
        )
        self.next(self.process_nlp, foreach="shards")
    
    @step
    @resources(
        cpu=settings.metaflow.default_cpu,
        memory=settings.metaflow.default_memory
    )
    @retry(times=settings.metaflow.max_retry_attempts)
    @catch(var="nlp_error")
    def process_nlp(self):
        """Process NLP for each shard in parallel."""
        shard = self.input
        logger.info(
            f"Processing NLP for shard {shard['shard_id']} "
            f"({shard['record_count']} records)"
        )
        
        # Load NLP resources using centralized settings
        nlp_model = load_spacy_model(
            model_name=settings.models.spacy_model,
            allow_download=settings.models.allow_model_download
        )
        stop_words = get_stopwords()
        
        # Process shard
        text_columns = ["title", "brief_summary", "detailed_description"]
        self.nlp_df = process_shard(
            shard["path"],
            text_columns,
            nlp_model,
            stop_words
        )
        
        # Conditionally save processed shard for debugging
        if self.save_intermediate_shards:
            output_path = (
                self.output_dir_obj / "nlp_processed" / 
                f"shard_{shard['shard_id']:03d}.parquet"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.nlp_df.write_parquet(output_path)
            
            self.nlp_stats = {
                "shard_id": shard["shard_id"],
                "processed_records": len(self.nlp_df),
                "output_path": str(output_path),
            }
        else:
            self.nlp_stats = {
                "shard_id": shard["shard_id"],
                "processed_records": len(self.nlp_df),
                "output_path": None,  # No file saved
            }
        
        logger.info(f"Shard {shard['shard_id']} NLP processing complete")
        self.next(self.combine_nlp_results)
    
    @step
    @resources(
        cpu=settings.metaflow.default_cpu * 2,
        memory=settings.metaflow.default_memory * 2
    )
    def combine_nlp_results(self, inputs):
        """Combine NLP results from all shards."""
        # Collect all processed shards and check for errors
        nlp_dfs = []
        failed_shards = []
        
        for input_data in inputs:
            if hasattr(input_data, "nlp_error"):
                # Log NLP processing errors from parallel steps
                failed_shards.append({
                    "shard_id": getattr(input_data, "input", {}).get("shard_id", "unknown"),
                    "error": str(input_data.nlp_error)
                })
                logger.warning(f"Shard processing failed: {input_data.nlp_error}")
            elif hasattr(input_data, "nlp_df"):
                nlp_dfs.append(input_data.nlp_df)
        
        # Report failed shards
        if failed_shards:
            logger.error(f"Failed to process {len(failed_shards)} shards: {failed_shards}")
            self.failed_shards = failed_shards
        else:
            self.failed_shards = []
        
        # Combine results
        self.combined_nlp_df, self.nlp_aggregate_stats = combine_nlp_results(
            nlp_dfs
        )
        
        # Add failure information to stats
        self.nlp_aggregate_stats["failed_shards"] = len(failed_shards)
        self.nlp_aggregate_stats["successful_shards"] = len(nlp_dfs)
        
        # Save combined results
        output_path = self.output_dir_obj / "nlp_combined.parquet"
        self.combined_nlp_df.write_parquet(output_path)
        self.nlp_aggregate_stats["output_path"] = str(output_path)
        
        self.next(self.generate_embeddings)
    
    @step
    @resources(
        cpu=settings.metaflow.default_cpu * 4,
        memory=settings.metaflow.embedding_step_memory,
        gpu=1 if settings.processing.enable_gpu else 0
    )
    @retry(times=settings.metaflow.max_retry_attempts)
    @environment(vars={"TOKENIZERS_PARALLELISM": "false"})
    def generate_embeddings(self):
        """Generate embeddings for text using sentence transformers."""
        logger.info("Generating text embeddings")
        
        # Use harmonized data artifact directly (no disk I/O needed)
        device = "cuda" if self.enable_gpu else "cpu"
        batch_size = (
            settings.models.embedding_batch_size if device == "cuda" 
            else settings.models.embedding_batch_size // 2
        )
        
        self.embeddings_df, self.embedding_stats = generate_embeddings(
            self.harmonized_df,  # Use artifact from harmonize_data step
            model_name=settings.models.embedding_model,
            text_columns=["title", "brief_summary"],
            batch_size=batch_size,
            device=device
        )
        
        # Optional: Save embeddings for inspection
        output_path = self.output_dir_obj / "embeddings.parquet"
        self.embeddings_df.write_parquet(output_path)
        self.embedding_stats["output_path"] = str(output_path)
        
        self.next(self.validate_quality)
    
    @step
    def validate_quality(self):
        """Validate data quality and generate processing report."""
        logger.info("Validating data quality")
        
        # Quality thresholds from centralized configuration
        thresholds = settings.quality.model_dump()
        
        # Calculate quality metrics
        total_expected = self.overlap_stats["csv_total"]
        total_processed = len(self.harmonized_df)
        error_rate = (
            1 - (total_processed / total_expected) 
            if total_expected > 0 else 1
        )
        
        quality_metrics = {
            "total_expected": total_expected,
            "total_processed": total_processed,
            "processing_rate": (
                (total_processed / total_expected) * 100 
                if total_expected > 0 else 0
            ),
            "error_rate": error_rate,
            "nlp_processed": self.nlp_aggregate_stats["total_processed"],
            "avg_token_count": self.nlp_aggregate_stats["avg_token_count"],
            "avg_lexical_diversity": self.nlp_aggregate_stats["avg_lexical_diversity"],
            "embeddings_generated": self.embedding_stats.get("total_embeddings", 0),
        }
        
        # Check quality thresholds
        quality_passed = True
        quality_issues = []
        
        if total_processed < thresholds["min_studies_processed"]:
            quality_issues.append(
                f"Processed studies ({total_processed}) below "
                f"threshold ({thresholds['min_studies_processed']})"
            )
            quality_passed = False
        
        if error_rate > thresholds["max_error_rate"]:
            quality_issues.append(
                f"Error rate ({error_rate:.2%}) above "
                f"threshold ({thresholds['max_error_rate']:.2%})"
            )
            quality_passed = False
        
        if quality_metrics["avg_token_count"] < thresholds["min_avg_tokens"]:
            quality_issues.append(
                f"Average tokens ({quality_metrics['avg_token_count']:.1f}) "
                f"below threshold ({thresholds['min_avg_tokens']})"
            )
        
        if quality_metrics["avg_lexical_diversity"] < thresholds["min_lexical_diversity"]:
            quality_issues.append(
                f"Average lexical diversity ({quality_metrics['avg_lexical_diversity']:.3f}) "
                f"below threshold ({thresholds['min_lexical_diversity']})"
            )
        
        self.quality_report = {
            "metrics": quality_metrics,
            "thresholds": thresholds,
            "passed": quality_passed,
            "issues": quality_issues,
        }
        
        status = "PASSED" if quality_passed else "FAILED"
        logger.info(f"Quality validation {status}")
        
        self.next(self.end)
    
    @step
    def end(self):
        """Complete the flow and generate final report."""
        logger.info("=" * 60)
        logger.info("CLINICAL TRIALS PIPELINE COMPLETE")
        logger.info("=" * 60)
        
        # Generate final summary
        # Alternative: use current.flow.parameters to access run parameters
        # flow_params = dict(current.flow.parameters)
        summary = {
            "run_id": current.run_id,
            "timestamp": datetime.now().isoformat(),
            "configuration": self.config,  # or flow_params for runtime parameters only
            "overlap_stats": self.overlap_stats,
            "harmonization_stats": self.harmonization_stats,
            "nlp_stats": self.nlp_aggregate_stats,
            "embedding_stats": self.embedding_stats,
            "quality_report": self.quality_report,
        }
        
        # Save summary report
        report_path = self.output_dir_obj / f"pipeline_report_{current.run_id}.json"
        with open(report_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Studies Processed: {self.harmonization_stats['output_records']:,}")
        logger.info(f"NLP Processed: {self.nlp_aggregate_stats['total_processed']:,}")
        logger.info(f"Embeddings Generated: {self.embedding_stats.get('total_embeddings', 0):,}")
        logger.info(f"Quality Status: {'PASSED' if self.quality_report['passed'] else 'FAILED'}")
        logger.info(f"Report saved to: {report_path}")


if __name__ == "__main__":
    ClinicalTrialsFlow()