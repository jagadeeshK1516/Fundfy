"""Document API routes."""

import uuid

from fastapi import APIRouter, HTTPException, Query

from fundfy.api.schemas import DocumentGenerateRequest, DocumentResponse
from fundfy.config import settings

router = APIRouter(prefix="/api", tags=["documents"])

# In-memory store for documents
_documents: dict[str, dict] = {}


@router.post("/documents/generate", response_model=DocumentResponse)
async def generate_document(request: DocumentGenerateRequest):
    """Generate a new document."""
    if settings.background_jobs_enabled:
        from fundfy.worker.manager import BackgroundJobManager
        manager = BackgroundJobManager()
        job_id = await manager.enqueue_document_generation(
            request.business_id, request.doc_type, request.context or ""
        )
        return DocumentResponse(
            id=job_id,
            business_id=request.business_id,
            doc_type=request.doc_type,
            title="Generating...",
            content="",
            job_id=job_id,
        )

    # Synchronous execution path
    from fundfy.dependencies import get_document_generator

    generator = get_document_generator()
    result = await generator.generate(request.doc_type, request.business_id, request.context or "")

    doc_id = str(uuid.uuid4())
    doc_record = {
        "id": doc_id,
        "business_id": result["business_id"],
        "doc_type": result["doc_type"],
        "title": result["title"],
        "content": result["content"],
    }
    _documents[doc_id] = doc_record

    return DocumentResponse(**doc_record)


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get a document by ID."""
    doc = _documents.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(**doc)


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(business_id: str = Query(...)):
    """List documents for a business."""
    docs = [d for d in _documents.values() if d["business_id"] == business_id]
    return [DocumentResponse(**d) for d in docs]
