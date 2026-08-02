"""Document generation tool — produces real file exports."""

import os
from typing import Any

from pydantic import BaseModel

from fundfy.documents.generator import DocumentGenerator
from fundfy.tools.base import BaseTool
from fundfy.tools.exporters import (
    export_docx,
    export_financial_model_xlsx,
    export_markdown,
    export_pdf,
    export_pptx,
)
from fundfy.tools.schemas import ToolResult


class GenerateDocumentArgs(BaseModel):
    """Arguments for generate_document tool."""

    doc_type: str
    business_id: str
    content: str | None = None
    format: str = "markdown"


class GenerateDocumentTool(BaseTool):
    """Generate a business document and export it to a file (PDF, DOCX, PPTX, XLSX, or Markdown)."""

    name = "generate_document"
    description = "Generate a business document (business_plan, prd, pitch_deck, financial_model, etc.) and export it as PDF, DOCX, PPTX, XLSX, or Markdown."
    args_schema = GenerateDocumentArgs

    def __init__(self, document_generator: DocumentGenerator):
        self._generator = document_generator

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Generate and export a document."""
        args = GenerateDocumentArgs(**kwargs)

        if args.format not in ("pdf", "docx", "pptx", "xlsx", "markdown"):
            return ToolResult(
                success=False,
                error=f"Unsupported format: {args.format}. Use pdf, docx, pptx, xlsx, or markdown.",
            )

        try:
            # Get content — either provided or generated
            if args.content:
                content = args.content
                title = f"{args.doc_type.replace('_', ' ').title()}"
            else:
                result = await self._generator.generate(args.doc_type, args.business_id)
                content = result["content"]
                title = result["title"]

            # Export to the requested format
            if args.format == "xlsx":
                filepath = export_financial_model_xlsx(title, content)
            else:
                exporters = {
                    "pdf": export_pdf,
                    "docx": export_docx,
                    "pptx": export_pptx,
                    "markdown": export_markdown,
                }
                exporter = exporters[args.format]
                filepath = exporter(title, content)

            return ToolResult(
                success=True,
                data={
                    "file_path": filepath,
                    "file_name": os.path.basename(filepath),
                    "format": args.format,
                    "doc_type": args.doc_type,
                    "title": title,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Document generation failed: {str(e)}")
