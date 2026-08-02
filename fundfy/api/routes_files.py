"""File download API routes."""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from fundfy.config import settings

router = APIRouter(prefix="/api", tags=["files"])


@router.get("/files/{file_id}")
async def download_file(file_id: str):
    """Download a generated file by ID (filename without extension or full filename)."""
    files_dir = Path(settings.generated_files_dir)

    if not files_dir.exists():
        raise HTTPException(status_code=404, detail="Generated files directory not found.")

    # Search for the file by ID (which is the filename)
    for filepath in files_dir.iterdir():
        if filepath.name == file_id or filepath.stem == file_id:
            return FileResponse(
                path=str(filepath),
                filename=filepath.name,
                media_type="application/octet-stream",
            )

    raise HTTPException(status_code=404, detail=f"File '{file_id}' not found.")


@router.get("/files")
async def list_files(business_id: str | None = None):
    """List generated files, optionally filtered by business_id in filename."""
    files_dir = Path(settings.generated_files_dir)

    if not files_dir.exists():
        return []

    files = []
    for filepath in files_dir.iterdir():
        if filepath.is_file() and filepath.name != ".gitkeep":
            file_info = {
                "file_id": filepath.stem,
                "file_name": filepath.name,
                "format": filepath.suffix.lstrip("."),
                "size": filepath.stat().st_size,
            }
            files.append(file_info)

    return files
