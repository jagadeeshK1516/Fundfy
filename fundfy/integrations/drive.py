"""Google Drive integration."""

from typing import Any


class DriveService:
    """Wraps the Google Drive API."""

    def __init__(self, credentials: Any):
        """Initialize with Google OAuth credentials."""
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload  # noqa: F401

        self._service = build("drive", "v3", credentials=credentials)
        self._fundfy_folder_id: str | None = None

    def _get_or_create_fundfy_folder(self) -> str:
        """Get or create the Fundfy/ root folder."""
        if self._fundfy_folder_id:
            return self._fundfy_folder_id

        # Search for existing Fundfy folder
        results = self._service.files().list(
            q="name='Fundfy' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces="drive",
            fields="files(id, name)",
        ).execute()
        files = results.get("files", [])

        if files:
            self._fundfy_folder_id = files[0]["id"]
        else:
            # Create it
            folder_metadata = {
                "name": "Fundfy",
                "mimeType": "application/vnd.google-apps.folder",
            }
            folder = self._service.files().create(
                body=folder_metadata, fields="id"
            ).execute()
            self._fundfy_folder_id = folder["id"]

        return self._fundfy_folder_id

    def create_folder(self, name: str, parent_id: str | None = None) -> str:
        """Create a folder in Drive."""
        parent = parent_id or self._get_or_create_fundfy_folder()
        folder_metadata: dict[str, Any] = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent],
        }
        folder = self._service.files().create(
            body=folder_metadata, fields="id"
        ).execute()
        return folder["id"]

    def upload_file(self, file_path: str, folder_name: str | None = None) -> dict:
        """Upload a file to Drive. Returns file metadata with ID."""
        import os
        from googleapiclient.http import MediaFileUpload

        parent_id = self._get_or_create_fundfy_folder()
        if folder_name:
            # Create or find sub-folder
            results = self._service.files().list(
                q=f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces="drive",
                fields="files(id)",
            ).execute()
            sub_folders = results.get("files", [])
            if sub_folders:
                parent_id = sub_folders[0]["id"]
            else:
                parent_id = self.create_folder(folder_name, parent_id)

        file_metadata: dict[str, Any] = {
            "name": os.path.basename(file_path),
            "parents": [parent_id],
        }
        media = MediaFileUpload(file_path, resumable=True)
        result = self._service.files().create(
            body=file_metadata, media_body=media, fields="id,name,webViewLink"
        ).execute()
        return result

    def list_files(self, folder_id: str | None = None) -> list[dict]:
        """List files in a folder."""
        parent = folder_id or self._get_or_create_fundfy_folder()
        results = self._service.files().list(
            q=f"'{parent}' in parents and trashed=false",
            spaces="drive",
            fields="files(id, name, mimeType, webViewLink, createdTime)",
        ).execute()
        return results.get("files", [])

    def get_share_link(self, file_id: str) -> str:
        """Make a file shareable and return its link."""
        self._service.permissions().create(
            fileId=file_id,
            body={"type": "anyone", "role": "reader"},
        ).execute()
        file = self._service.files().get(
            fileId=file_id, fields="webViewLink"
        ).execute()
        return file.get("webViewLink", "")
