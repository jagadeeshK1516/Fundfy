"""Embedding factory function."""

from langchain_openai import OpenAIEmbeddings

from fundfy.config import settings


def get_embeddings() -> OpenAIEmbeddings:
    """Return an OpenAIEmbeddings instance configured from settings."""
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        openai_api_key=settings.openai_api_key,
    )
