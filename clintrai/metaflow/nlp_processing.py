# clintrai/metaflow/nlp_processing.py
"""NLP processing functions for clinical trials pipeline."""

import subprocess
from collections import Counter

import nltk
import polars as pl
import spacy
from loguru import logger
from nltk.corpus import stopwords


def load_spacy_model(model_name="en_core_web_sm", allow_download=False):
    """
    Load spaCy model with optional download fallback.
    
    Args:
        model_name: Name of the spaCy model to load
        allow_download: Whether to download model if not found (dev mode only)
        
    Returns:
        spacy.Language: Loaded spaCy model
        
    Raises:
        OSError: If model not found and download not allowed
    """
    try:
        return spacy.load(model_name)
    except OSError as e:
        if allow_download:
            logger.warning(
                f"Model {model_name} not found. Downloading (dev mode only). "
                "For production, pre-install models in container."
            )
            subprocess.run(
                ["python", "-m", "spacy", "download", model_name],
                check=True
            )
            return spacy.load(model_name)
        else:
            logger.error(
                f"spaCy model '{model_name}' not found. "
                "For production, ensure models are pre-installed in the container. "
                "For development, set allow_download=True."
            )
            raise OSError(
                f"Model '{model_name}' not available. Pre-install in production environment."
            ) from e


def get_stopwords(language="english"):
    """
    Get NLTK stopwords with automatic download if needed.
    
    Args:
        language: Language for stopwords
        
    Returns:
        set: Set of stopwords
    """
    try:
        nltk.data.find("stopwords")
    except LookupError:
        logger.info("Downloading NLTK stopwords")
        nltk.download("stopwords")
    
    return set(stopwords.words(language))


def extract_nlp_features(text, nlp_model, stop_words, max_text_length=1000000):
    """
    Extract NLP features from text.
    
    Args:
        text: Text to process
        nlp_model: Loaded spaCy model
        stop_words: Set of stopwords
        max_text_length: Maximum text length to process
        
    Returns:
        dict: Extracted NLP features
    """
    # Process with spaCy (limit text length)
    doc = nlp_model(text[:max_text_length])
    
    # Extract tokens
    tokens = [
        token.text.lower() 
        for token in doc 
        if not token.is_stop and token.is_alpha
    ]
    
    # Extract named entities
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    # Calculate metrics
    word_freq = Counter(tokens)
    lexical_diversity = len(set(tokens)) / len(tokens) if tokens else 0
    
    return {
        "token_count": len(tokens),
        "unique_tokens": len(set(tokens)),
        "lexical_diversity": lexical_diversity,
        "entity_count": len(entities),
        "top_words": dict(word_freq.most_common(10)),
        "named_entities": entities[:20],  # Limit to top 20
    }


def process_shard(shard_path, text_columns, nlp_model, stop_words):
    """
    Process NLP for a single data shard using vectorized operations.
    
    Args:
        shard_path: Path to the shard file
        text_columns: List of text column names to process
        nlp_model: Loaded spaCy model
        stop_words: Set of stopwords
        
    Returns:
        pl.DataFrame: DataFrame with NLP features
    """
    logger.info(f"Processing shard: {shard_path}")
    
    # Load shard data
    df = pl.read_parquet(shard_path)
    
    # Combine text columns into a single column
    text_exprs = [pl.col(c).fill_null("").cast(pl.Utf8) for c in text_columns]
    df = df.with_columns(
        pl.concat_str(text_exprs, separator=" ").alias("combined_text")
    )
    
    # Process each text using map_elements for complex NLP operations
    def process_text(text):
        """Process a single text entry."""
        if text and text.strip():
            return extract_nlp_features(text, nlp_model, stop_words)
        else:
            # Return empty features without nct_id (will be added later)
            return {
                "token_count": 0,
                "unique_tokens": 0,
                "lexical_diversity": 0,
                "entity_count": 0,
                "top_words": {},
                "named_entities": [],
            }
    
    # Apply NLP processing to combined text
    features_df = df.select(
        pl.col("nct_id"),
        pl.col("combined_text").map_elements(
            process_text,
            return_dtype=pl.Struct([
                pl.Field("token_count", pl.Int64),
                pl.Field("unique_tokens", pl.Int64),
                pl.Field("lexical_diversity", pl.Float64),
                pl.Field("entity_count", pl.Int64),
                pl.Field("top_words", pl.Object),
                pl.Field("named_entities", pl.Object),
            ])
        ).alias("features")
    ).unnest("features")
    
    return features_df



def combine_nlp_results(nlp_dataframes):
    """
    Combine NLP results from multiple shards.
    
    Args:
        nlp_dataframes: List of Polars DataFrames with NLP features
        
    Returns:
        tuple: (combined_dataframe, aggregate_statistics)
    """
    logger.info(f"Combining {len(nlp_dataframes)} NLP result shards")
    
    if nlp_dataframes:
        combined_df = pl.concat(nlp_dataframes)
    else:
        # Create empty dataframe with expected schema
        combined_df = pl.DataFrame({
            "nct_id": [],
            "token_count": [],
            "unique_tokens": [],
            "lexical_diversity": [],
            "entity_count": [],
        })
    
    # Calculate aggregate statistics
    stats = {
        "total_processed": len(combined_df),
        "avg_token_count": (
            combined_df["token_count"].mean() 
            if len(combined_df) > 0 else 0
        ),
        "avg_lexical_diversity": (
            combined_df["lexical_diversity"].mean() 
            if len(combined_df) > 0 else 0
        ),
        "total_unique_entities": (
            combined_df["entity_count"].sum() 
            if len(combined_df) > 0 else 0
        ),
    }
    
    logger.info(f"Combined {stats['total_processed']:,} NLP-processed records")
    
    return combined_df, stats