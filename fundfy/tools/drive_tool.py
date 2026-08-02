"""Google Drive tool for the AI agent."""

from typing import Any

from pydantic import BaseModel

from fundfy.tools.base import BaseTool
from fundfy.tools.schemas import ToolResult


class UploadToDriveArgs(BaseModel):
    """Arguments for upload_to_drive tool."""

    file_path: str
    folder_name: str = "Documents"
    founder_id: str


class UploadToDriveTool(BaseTool):
    """Uploads a generated document to Google Drive and returns a share link."""

    name = "upload_to_drive"
    description = "Upload a generated document to Google Drive and return a shareable link."
    args_schema = UploadToDriveArgs

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Upload a file to Drive."""
        args = UploadToDriveArgs(**kwargs)

        try:
            from fundfy.integrations.google_auth import get_access_token
            from google.oauth2.credentials import Credentials
            from fundfy.integrations.drive import DriveService

            access_token = await get_access_token(args.founder_id)
            if not access_token:
                return ToolResult(
                    success=False,
                    error="Google account not connected. Please connect via Integrations settings.",
                )

            credentials = Credentials(token=access_token)
            drive = DriveService(credentials)
            result = drive.upload_file(args.file_path, args.folder_name)
            share_link = drive.get_share_link(result["id"])

            return ToolResult(
                success=True,
                data={
                    "file_id": result["id"],
                    "file_name": result.get("name"),
                    "share_link": share_link,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to upload to Drive: {str(e)}")
