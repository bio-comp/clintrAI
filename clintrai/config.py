"""Configuration management for ClinTrAI clinical trials processing pipeline."""

import os
from pathlib import Path

from pydantic import Field, field_validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from clintrai.models.types import DeduplicationStrategy


class QualityThresholds(BaseSettings):
    """Data quality validation thresholds for pipeline validation."""
    
    model_config = SettingsConfigDict(
        env_prefix="CLINTRAI_QUALITY_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    min_studies_processed: int = Field(
        default=100000,
        description="Minimum number of studies that must be processed successfully",
        ge=1,
    )
    
    max_error_rate: float = Field(
        default=0.05,
        description="Maximum acceptable error rate (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
    
    min_avg_tokens: int = Field(
        default=50,
        description="Minimum average token count for processed text",
        ge=1,
    )
    
    min_lexical_diversity: float = Field(
        default=0.1,
        description="Minimum lexical diversity score",
        ge=0.0,
        le=1.0,
    )


class ModelSettings(BaseSettings):
    """Model names and configuration for NLP and ML components."""
    
    model_config = SettingsConfigDict(
        env_prefix="CLINTRAI_MODEL_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Embedding model configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="SentenceTransformer model for text embeddings",
    )
    
    embedding_batch_size: int = Field(
        default=32,
        description="Batch size for embedding generation",
        ge=1,
        le=512,
    )
    
    # spaCy model configuration
    spacy_model: str = Field(
        default="en_core_web_sm",
        description="spaCy model for NLP processing",
    )
    
    spacy_batch_size: int = Field(
        default=1000,
        description="Batch size for spaCy processing",
        ge=1,
    )
    
    # Model caching
    model_cache_dir: Path = Field(
        default=Path("/tmp/clintrai_models"),
        description="Directory for caching downloaded models",
    )
    
    allow_model_download: bool = Field(
        default=False,
        description="Allow automatic model downloads (dev mode only)",
    )


class DatabaseSettings(BaseSettings):
    """Database connection and configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="CLINTRAI_DB_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # PostgreSQL with pgvector configuration
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port", ge=1, le=65535)
    username: str = Field(default="clintrai", description="Database username")
    password: SecretStr = Field(default="", description="Database password")
    database: str = Field(default="clintrai", description="Database name")
    
    # Connection pool settings
    min_connections: int = Field(default=5, description="Minimum pool connections", ge=1)
    max_connections: int = Field(default=20, description="Maximum pool connections", ge=1)
    
    # Vector settings for pgvector
    vector_dimension: int = Field(
        default=384,
        description="Embedding vector dimension (depends on model)",
        ge=1,
    )
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        # Use get_secret_value() to access the plain text password
        return (
            f"postgresql://{self.username}:{self.password.get_secret_value()}@"
            f"{self.host}:{self.port}/{self.database}"
        )


class ProcessingSettings(BaseSettings):
    """Data processing pipeline configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="CLINTRAI_PROCESSING_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Core processing parameters
    batch_size: int = Field(
        default=1000,
        description="Batch size for data processing",
        ge=1,
        le=10000,
    )
    
    shard_count: int = Field(
        default=256,
        description="Number of shards for parallel processing",
        ge=1,
        le=1024,
    )
    
    # Deduplication strategy
    dedup_strategy: DeduplicationStrategy = Field(
        default=DeduplicationStrategy.JSON_PRIORITY,
        description="Strategy for handling duplicate records",
    )
    
    # Hardware configuration
    enable_gpu: bool = Field(
        default=True,
        description="Enable GPU acceleration for ML operations",
    )
    
    max_workers: int = Field(
        default=os.cpu_count() or 4,
        description="Maximum number of worker processes",
        ge=1,
    )
    
    # File handling
    save_intermediate_shards: bool = Field(
        default=False,
        description="Save intermediate processing files for debugging",
    )
    
    output_compression: str = Field(
        default="snappy",
        description="Compression for output Parquet files",
    )
    
    @field_validator("dedup_strategy", mode="before")
    @classmethod
    def validate_dedup_strategy(cls, v):
        """Convert string to DeduplicationStrategy enum."""
        if isinstance(v, str):
            return DeduplicationStrategy(v)
        return v


class APISettings(BaseSettings):
    """ClinicalTrials.gov API configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="CLINTRAI_API_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # API endpoints
    base_url: str = Field(
        default="https://clinicaltrials.gov/api/v2",
        description="ClinicalTrials.gov API base URL",
    )
    
    # Rate limiting
    requests_per_second: float = Field(
        default=5.0,
        description="Maximum API requests per second",
        ge=0.1,
        le=100.0,
    )
    
    timeout_seconds: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
        ge=1.0,
        le=300.0,
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
        ge=0,
        le=10,
    )
    
    # Concurrent downloads
    max_concurrent_requests: int = Field(
        default=10,
        description="Maximum concurrent API requests",
        ge=1,
        le=100,
    )


class LoggingSettings(BaseSettings):
    """Logging configuration for the pipeline."""
    
    model_config = SettingsConfigDict(
        env_prefix="CLINTRAI_LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="Log message format",
    )
    
    json_output: bool = Field(
        default=False,
        description="Output logs in JSON format (for production)",
    )
    
    file_path: Path | None = Field(
        default=None,
        description="Log file path (None for stdout only)",
    )
    
    max_file_size: str = Field(
        default="10MB",
        description="Maximum log file size before rotation",
    )
    
    backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep",
        ge=0,
    )


class MetaflowSettings(BaseSettings):
    """Metaflow-specific configuration."""
    
    model_config = SettingsConfigDict(
        env_prefix="CLINTRAI_METAFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Resource allocation
    default_cpu: int = Field(
        default=2,
        description="Default CPU cores for Metaflow steps",
        ge=1,
    )
    
    default_memory: int = Field(
        default=8000,
        description="Default memory in MB for Metaflow steps",
        ge=512,
    )
    
    embedding_step_memory: int = Field(
        default=16000,
        description="Memory allocation for embedding generation step in MB",
        ge=1024,
    )
    
    # Retry configuration
    max_retry_attempts: int = Field(
        default=2,
        description="Maximum retry attempts for failed steps",
        ge=0,
        le=5,
    )
    
    # Project settings
    project_name: str = Field(
        default="clinical_trials",
        description="Metaflow project name",
    )
    
    # Scheduling
    enable_schedule: bool = Field(
        default=True,
        description="Enable daily pipeline scheduling",
    )


class Settings(BaseSettings):
    """
    Main configuration class for the ClinTrAI clinical trials processing pipeline.
    
    Loads settings from environment variables with CLINTRAI_ prefix or from .env file.
    Nested configuration models handle specific domains (database, processing, etc.).
    
    Example:
        >>> from clintrai.config import settings
        >>> print(settings.processing.batch_size)
        1000
        >>> print(settings.database.connection_string)
        postgresql://user:pass@localhost:5432/clintrai
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CLINTRAI_",
        case_sensitive=False,
    )
    
    # Environment and debugging
    environment: str = Field(
        default="development",
        description="Runtime environment (development, staging, production)",
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    
    # Default data paths (can be overridden by Metaflow parameters)
    # Note: Directory creation is handled by application logic, not configuration
    data_dir: Path = Field(
        default=Path("./data"),
        description="Base directory for data files",
    )
    
    output_dir: Path = Field(
        default=Path("./processed_output"),
        description="Default output directory for processed files",
    )
    
    # Nested configuration models
    quality: QualityThresholds = Field(
        default_factory=QualityThresholds,
        description="Data quality validation thresholds",
    )
    
    models: ModelSettings = Field(
        default_factory=ModelSettings,
        description="ML/NLP model configuration",
    )
    
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Database connection settings",
    )
    
    processing: ProcessingSettings = Field(
        default_factory=ProcessingSettings,
        description="Data processing configuration",
    )
    
    api: APISettings = Field(
        default_factory=APISettings,
        description="ClinicalTrials.gov API settings",
    )
    
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description="Logging configuration",
    )
    
    metaflow: MetaflowSettings = Field(
        default_factory=MetaflowSettings,
        description="Metaflow pipeline configuration",
    )
    
    # Removed ensure_paths_exist validator to avoid side effects during configuration loading.
    # Directory creation and validation should be handled by application logic
    # (e.g., in the Metaflow pipeline's start step) rather than during config initialization.
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Create a global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    This function provides dependency injection for testing and
    allows for easy mocking of configuration in tests.
    
    Returns:
        Global settings instance
    """
    return settings


def create_test_settings(**overrides) -> Settings:
    """
    Create test settings with overrides.
    
    Args:
        **overrides: Settings to override for testing
        
    Returns:
        Settings instance with test-specific configuration
    """
    test_defaults = {
        "environment": "testing",
        "debug": True,
        "processing": ProcessingSettings(
            batch_size=10,
            shard_count=2,
            save_intermediate_shards=True,
        ),
        "quality": QualityThresholds(
            min_studies_processed=1,
            max_error_rate=0.5,
        ),
        "models": ModelSettings(
            allow_model_download=True,
            embedding_batch_size=2,
            spacy_batch_size=10,
        ),
        "database": DatabaseSettings(
            password=SecretStr("test_password"),
        ),
    }
    
    # Merge test defaults with any provided overrides
    test_config = {**test_defaults, **overrides}
    
    return Settings(**test_config)