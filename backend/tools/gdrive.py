import os
import io
import json
import logging
from typing import Dict, Any
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from backend.config import Config

logger = logging.getLogger("GDriveTool")

class GDriveTool:
    def __init__(self, folder_id: str = Config.GDRIVE_FOLDER_ID):
        self.folder_id = folder_id

    def _get_service(self):
        # 1. Try OAuth2 Refresh Token (Best for Personal 5TB Google Drive)
        client_id = os.getenv("GDRIVE_CLIENT_ID", "").strip()
        client_secret = os.getenv("GDRIVE_CLIENT_SECRET", "").strip()
        refresh_token = os.getenv("GDRIVE_REFRESH_TOKEN", "").strip()

        if client_id and client_secret and refresh_token:
            try:
                creds = Credentials(
                    token=None,
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret
                )
                service = build('drive', 'v3', credentials=creds)
                return service, None
            except Exception as e:
                logger.error(f"Failed OAuth2 init: {e}")

        # 2. Fallback to Service Account JSON
        raw_json = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON", "").strip()
        if not raw_json:
            return None, "Google Drive credentials not set (Requires OAuth2 or Service Account)."
        
        try:
            raw_clean = raw_json.replace('\\n', '\n')
            cred_dict = json.loads(raw_clean, strict=False)
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace('\\n', '\n')
                
            creds = service_account.Credentials.from_service_account_info(cred_dict, scopes=['https://www.googleapis.com/auth/drive'])
            service = build('drive', 'v3', credentials=creds)
            return service, None
        except Exception as e:
            logger.error(f"Failed Service Account init: {e}")
            return None, str(e)

    def sync_file_info(self, file_name: str, file_content: str) -> Dict[str, Any]:
        """
        Uploads or updates a file directly in the Google Drive 5TB storage folder.
        """
        service, err = self._get_service()
        if not service:
            return {
                "status": "pending_credentials",
                "error": err,
                "folder_id": self.folder_id,
                "file_name": file_name
            }

        try:
            query = f"'{self.folder_id}' in parents and name = '{file_name}' and trashed = false"
            results = service.files().list(
                q=query, 
                fields="files(id, name)"
            ).execute()
            files = results.get('files', [])

            fh = io.BytesIO(file_content.encode('utf-8'))
            media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)

            if files:
                file_id = files[0]['id']
                updated_file = service.files().update(
                    fileId=file_id,
                    media_body=media,
                    fields='id, name, webViewLink'
                ).execute()
                logger.info(f"Updated file {file_name} on Google Drive (ID: {file_id})")
                return {"status": "success", "action": "updated", "file_id": file_id, "link": updated_file.get("webViewLink")}
            else:
                file_metadata = {
                    'name': file_name,
                    'parents': [self.folder_id]
                }
                created_file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink'
                ).execute()
                logger.info(f"Created file {file_name} on Google Drive (ID: {created_file.get('id')})")
                return {"status": "success", "action": "created", "file_id": created_file.get("id"), "link": created_file.get("webViewLink")}
        except Exception as e:
            logger.error(f"Google Drive API upload error: {e}")
            return {"status": "error", "message": str(e)}
