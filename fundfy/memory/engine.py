"""Business Memory Engine — ChromaDB vector store with LangChain."""

from typing import Any

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from fundfy.config import settings
from fundfy.memory.embeddings import get_embeddings


class MemoryEngine:
    """RAG memory layer backed by ChromaDB."""

    def __init__(self, embeddings: Embeddings | None = None, persist_directory: str | None = None):
        self._embeddings = embeddings or get_embeddings()
        self._persist_directory = persist_directory or settings.chroma_persist_dir
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        self._vectorstore = Chroma(
            collection_name="fundfy_memory",
            embedding_function=self._embeddings,
            persist_directory=self._persist_directory,
        )

    def ingest(self, text: str, metadata: dict[str, Any] | None = None) -> list[str]:
        """Ingest text into the vector store after chunking.

        Returns the list of document IDs.
        """
        metadata = metadata or {}
        docs = self._splitter.create_documents([text], metadatas=[metadata])
        ids = self._vectorstore.add_documents(docs)
        return ids

    def query(self, question: str, filters: dict[str, Any] | None = None, k: int = 5) -> list[Document]:
        """Query the vector store for relevant documents."""
        search_kwargs: dict[str, Any] = {"k": k}
        if filters:
            search_kwargs["filter"] = filters
        results = self._vectorstore.similarity_search(question, **search_kwargs)
        return results

    def ingest_document(self, doc_id: str, content: str, metadata: dict[str, Any] | None = None) -> list[str]:
        """Ingest a document by ID with its content."""
        meta = metadata or {}
        meta["doc_id"] = doc_id
        return self.ingest(content, meta)
