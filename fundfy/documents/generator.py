"""Document generation engine — LLM-powered document writing."""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from fundfy.config import settings
from fundfy.documents.templates import DOCUMENT_TEMPLATES
from fundfy.memory.engine import MemoryEngine


class DocumentGenerator:
    """Generates business documents using LLM and RAG context."""

    def __init__(self, llm: Any = None, memory_engine: MemoryEngine | None = None):
        self._llm = llm or ChatOpenAI(
            model=settings.openai_model,
            openai_api_key=settings.openai_api_key,
            temperature=0.5,
        )
        self._memory = memory_engine

    async def generate(self, doc_type: str, business_id: str, additional_context: str = "") -> dict[str, str]:
        """Generate a document of the specified type.

        Args:
            doc_type: Type of document (e.g., 'business_plan', 'prd').
            business_id: The business ID for context retrieval.
            additional_context: Extra context to include in the prompt.

        Returns:
            Dictionary with 'doc_type', 'title', and 'content' keys.
        """
        template = DOCUMENT_TEMPLATES.get(doc_type)
        if not template:
            raise ValueError(f"Unknown document type: {doc_type}. Available: {list(DOCUMENT_TEMPLATES.keys())}")

        # Retrieve relevant context from memory
        context_text = additional_context
        if self._memory:
            docs = self._memory.query(f"{doc_type} business context", filters=None, k=5)
            memory_text = "\n\n".join(d.page_content for d in docs)
            context_text = f"{memory_text}\n\n{additional_context}" if memory_text else additional_context

        prompt = template.format(context=context_text or "No additional context provided.")

        messages = [
            SystemMessage(content="You are a professional business document writer. Generate comprehensive, well-structured documents."),
            HumanMessage(content=prompt),
        ]

        response = await self._llm.ainvoke(messages)
        content = response.content

        # Generate title
        title = f"{doc_type.replace('_', ' ').title()}"

        # Ingest generated document back into memory
        if self._memory:
            self._memory.ingest(
                content,
                {"source_type": "document", "doc_type": doc_type, "business_id": business_id},
            )

        return {
            "doc_type": doc_type,
            "title": title,
            "content": content,
            "business_id": business_id,
        }
