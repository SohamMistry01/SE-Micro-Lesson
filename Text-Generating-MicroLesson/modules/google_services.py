from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from modules.config import settings
import io

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_creds():
    return service_account.Credentials.from_service_account_file(
        settings.CREDENTIALS_FILE, scopes=SCOPES
    )


def fetch_input_data():
    """Reads the Input Sheet."""
    creds = get_creds()
    service = build("sheets", "v4", credentials=creds)

    range_name = f"{settings.SHEET_NAME_INPUT}!A:C"
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=settings.SPREADSHEET_ID, range=range_name)
        .execute()
    )
    return result.get("values", [])


def update_row_status(row_index: int, new_status: str = "Yes"):
    """Updates the Status column for a specific row."""
    creds = get_creds()
    service = build("sheets", "v4", credentials=creds)

    range_name = f"{settings.SHEET_NAME_INPUT}!C{row_index}"
    body = {"values": [[new_status]]}
    service.spreadsheets().values().update(
        spreadsheetId=settings.SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body,
    ).execute()


def append_output_data(data: list):
    """Appends data to Output Sheet."""
    creds = get_creds()
    service = build("sheets", "v4", credentials=creds)

    range_name = f"{settings.SHEET_NAME_OUTPUT}!A:D"
    body = {"values": [data]}
    service.spreadsheets().values().append(
        spreadsheetId=settings.SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body=body,
    ).execute()


def upload_to_drive(filename: str, content: bytes, mime_type: str) -> str:
    """Uploads file to Google Drive and returns the webViewLink."""
    creds = get_creds()
    service = build("drive", "v3", credentials=creds)

    file_metadata = {"name": filename, "parents": [settings.DRIVE_FOLDER_ID]}

    media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)

    file = (
        service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
            supportsAllDrives=True,
        )
        .execute()
    )

    return file.get("webViewLink")


# --- NEW FUNCTION TO FIX YOUR ERROR ---
def download_drive_text_content(file_id: str) -> str:
    """Downloads a text file content directly from Drive API using File ID."""
    creds = get_creds()
    service = build("drive", "v3", credentials=creds)

    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()

        # Reset pointer and read
        fh.seek(0)
        content = fh.read().decode("utf-8")
        return content
    except Exception as e:
        print(f"Error downloading Drive file {file_id}: {e}")
        return ""


def get_and_parse_drive_file(file_id: str) -> str:
    """
    Identifies the Google Drive file type and securely extracts its textual content.
    Uses Google's Native backend to convert PDFs for bulletproof text extraction.
    """
    try:
        creds = get_creds()
        drive_service = build("drive", "v3", credentials=creds)

        file_metadata = (
            drive_service.files()
            .get(fileId=file_id, fields="mimeType, name", supportsAllDrives=True)
            .execute()
        )
        mime_type = file_metadata.get("mimeType", "")

        # 1. Handle Google Docs (Export directly to Text)
        if "application/vnd.google-apps.document" in mime_type:
            request = drive_service.files().export_media(
                fileId=file_id, mimeType="text/plain"
            )
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return fh.getvalue().decode("utf-8").strip()

        # 2. ✅ FIX: Handle PDFs using Google's Native Conversion Engine
        elif "application/pdf" in mime_type:
            print("   Using Google Native Engine to extract PDF text...")

            # A. Ask Google Drive to copy the PDF and turn it into a Google Doc
            copy_metadata = {"mimeType": "application/vnd.google-apps.document"}
            temp_doc = (
                drive_service.files()
                .copy(fileId=file_id, body=copy_metadata, supportsAllDrives=True)
                .execute()
            )
            temp_doc_id = temp_doc.get("id")

            try:
                # B. Export the newly created Google Doc as pure text
                request = drive_service.files().export_media(
                    fileId=temp_doc_id, mimeType="text/plain"
                )
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                extracted_text = fh.getvalue().decode("utf-8")
                return extracted_text.strip()

            finally:
                # C. Always delete the temporary Google Doc to keep the Drive clean
                try:
                    drive_service.files().delete(
                        fileId=temp_doc_id, supportsAllDrives=True
                    ).execute()
                except Exception as cleanup_err:
                    print(
                        f"   Warning: Could not delete temp file {temp_doc_id}: {cleanup_err}"
                    )

        # 3. Handle Standard Text Files
        else:
            request = drive_service.files().get_media(
                fileId=file_id, supportsAllDrives=True
            )
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return fh.getvalue().decode("utf-8").strip()

    except Exception as e:
        print(f"❌ Error parsing Google Drive file {file_id}: {e}")
        return ""
