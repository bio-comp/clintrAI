# clintrai/metaflow/embeddings.py
"""Embedding generation functions for clinical trials pipeline."""

import torch
from loguru import logger
from sentence_transformers import SentenceTransformer
import polars as pl


def load_embedding_model(model_name, device=None):
    """
    Load sentence transformer model.
    
    Args:
        model_name: Name of the model to load
        device: Device to use (cuda/cpu), auto-detect if None
        
    Returns:
        tuple: (model, device_used)
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    
    logger.info(f"Loading embedding model {model_name} on {device}")
    model = SentenceTransformer(model_name, device=device)
    
    return model, device


def prepare_texts_for_embedding(dataframe, text_columns, max_length=500):
    """
    Prepare texts from dataframe for embedding generation using vectorized operations.
    
    Args:
        dataframe: Polars DataFrame with text data
        text_columns: List of column names to combine for embedding
        max_length: Maximum length per text field
        
    Returns:
        tuple: (texts_list, nct_ids_list)
    """
    # Vectorized text preparation
    text_exprs = []
    for col in text_columns:
        if col == "brief_summary":
            # Limit summary length
            text_exprs.append(
                pl.col(col).fill_null("").str.slice(0, max_length)
            )
        else:
            text_exprs.append(pl.col(col).fill_null(""))
    
    # Combine text columns and filter non-empty texts
    df_with_text = dataframe.with_columns(
        pl.concat_str(text_exprs, separator=" ").alias("combined_text")
    ).filter(
        pl.col("combined_text").str.strip_chars().str.len_chars() > 0
    )
    
    texts = df_with_text["combined_text"].to_list()
    nct_ids = df_with_text["nct_id"].to_list()
    
    logger.info(f"Prepared {len(texts)} texts for embedding")
    return texts, nct_ids


def create_embeddings_dataframe(nct_ids, embeddings):
    """
    Create a Polars DataFrame with embeddings.
    
    Args:
        nct_ids: List of NCT identifiers
        embeddings: List of embedding vectors
        
    Returns:
        pl.DataFrame: DataFrame with nct_id and embedding columns
    """
    return pl.DataFrame({
        "nct_id": nct_ids,
        "embedding": embeddings,
    })


def generate_embeddings(
    dataframe, 
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    text_columns=None,
    batch_size=32,
    device=None
):
    """
    Generate embeddings for clinical trial texts using vectorized operations.
    
    Args:
        dataframe: Polars DataFrame with text data
        model_name: Name of the embedding model
        text_columns: Columns to use for embedding (default: title, brief_summary)
        batch_size: Batch size for processing
        device: Device to use (cuda/cpu)
        
    Returns:
        tuple: (embeddings_dataframe, statistics_dict)
    """
    if text_columns is None:
        text_columns = ["title", "brief_summary"]
    
    try:
        # Load model
        model, device_used = load_embedding_model(model_name, device)
        
        # Prepare texts using vectorized operations
        texts, nct_ids = prepare_texts_for_embedding(dataframe, text_columns)
        
        if not texts:
            logger.warning("No texts to embed")
            return create_empty_embeddings_dataframe(), {"error": "No texts to embed"}
        
        # Generate embeddings - let SentenceTransformer handle batching
        logger.info(f"Generating embeddings for {len(texts)} texts")
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_tensor=False
        ).tolist()
        
        # Create dataframe
        embeddings_df = create_embeddings_dataframe(nct_ids, embeddings)
        
        # Statistics
        stats = {
            "total_embeddings": len(embeddings_df),
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            "model_name": model_name,
            "device": device_used,
        }
        
        logger.info(
            f"Generated {stats['total_embeddings']} embeddings "
            f"with dimension {stats['embedding_dimension']}"
        )
        
        return embeddings_df, stats
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return create_empty_embeddings_dataframe(), {"error": str(e)}


def create_empty_embeddings_dataframe():
    """
    Create an empty embeddings DataFrame.
    
    Returns:
        pl.DataFrame: Empty DataFrame with expected schema
    """
    return pl.DataFrame({
        "nct_id": [],
        "embedding": [],
    })