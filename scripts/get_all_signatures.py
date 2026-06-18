"""Export every active user's live Gmail signature HTML to a shared Google Drive folder."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from authenticator import GmailBatchAuthenticator, admin_directory_v1_api, drive_v3_api
from googleapiclient.http import MediaInMemoryUpload

# Configuration
DOMAIN = 'company.com'
SHARED_DRIVE_FOLDER_ID = 'YOUR_FOLDER_ID_HERE'
MAX_RETRIES = 3
MAX_WORKERS = 20  # Thread-local services prevent SSL errors, safe to go higher

_thread_local = threading.local()


def _get_drive_service():
    """Return a per-thread Drive API service instance (avoids sharing SSL connections)."""
    if not hasattr(_thread_local, "drive_service"):
        _thread_local.drive_service = drive_v3_api()
    return _thread_local.drive_service


def get_existing_files() -> dict[str, str]:
    """Pre-fetch all files in the shared Drive folder and return ``{filename: file_id}``."""
    drive_service = drive_v3_api()
    existing = {}
    page_token = None

    print("Pre-fetching existing files from Drive...")

    while True:
        results = drive_service.files().list(
            q=f"'{SHARED_DRIVE_FOLDER_ID}' in parents and trashed = false",
            fields="nextPageToken, files(id, name)",
            pageSize=1000,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            pageToken=page_token
        ).execute()

        for f in results.get("files", []):
            existing[f["name"]] = f["id"]

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    print(f"Found {len(existing)} existing files in Drive.")
    return existing

def upload_to_drive(filename: str, content: str, existing_files: dict[str, str]) -> None:
    """Upload or update an HTML file in the shared Drive folder."""
    drive_service = _get_drive_service()
    media = MediaInMemoryUpload(content.encode("utf-8"), mimetype="text/html")

    file_id = existing_files.get(filename)
    if file_id:
        # Update existing file
        drive_service.files().update(
            fileId=file_id,
            media_body=media,
            supportsAllDrives=True
        ).execute()
    else:
        # Create new file
        file_metadata = {
            "name": filename,
            "parents": [SHARED_DRIVE_FOLDER_ID]
        }
        drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True
        ).execute()

def get_all_active_users() -> list[dict]:
    """Fetch all active, non-suspended domain users (excluding /Non-User Accounts)."""
    service = admin_directory_v1_api()
    users_list = []
    page_token = None

    print("Fetching user list from Google Admin...")

    while True:
        result = service.users().list(
            domain=DOMAIN,
            maxResults=500,
            orderBy='email',
            query='isSuspended=false',
            pageToken=page_token
        ).execute()

        users = result.get('users', [])

        for user in users:
            if user.get("orgUnitPath") != "/Non-User Accounts":
                users_list.append(user)

        page_token = result.get('nextPageToken')
        if not page_token:
            break

    print(f"Found {len(users_list)} active users. Starting signature export...")
    return users_list

def save_signature(
    gmail_batch: GmailBatchAuthenticator,
    existing_files: dict[str, str],
    user: dict,
    index: int,
    total: int,
) -> str:
    """Fetch and upload a single user's Gmail signature to Drive. Returns 'success', 'skipped', or 'error'."""
    user_email = user.get("primaryEmail")
    user_name = user.get("name", {}).get("fullName", "Unknown_Name")
    start = time.time()

    for attempt in range(MAX_RETRIES):
        try:
            gmail_service = gmail_batch.get_service(user_email)
            aliases = gmail_service.users().settings().sendAs().list(userId='me').execute()
            send_as_list = aliases.get("sendAs", [])

            if not send_as_list:
                print(f"[{index}/{total}] Skipped {user_name}: No aliases found. ({time.time() - start:.1f}s)")
                return "skipped"

            signature_html = send_as_list[0].get("signature")

            if not signature_html:
                print(f"[{index}/{total}] Skipped {user_name}: No signature set. ({time.time() - start:.1f}s)")
                return "skipped"

            safe_filename = f"{user_name}.html"
            upload_to_drive(safe_filename, signature_html, existing_files)
            print(f"[{index}/{total}] Done: {safe_filename} ({time.time() - start:.1f}s)")
            return "success"

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"[{index}/{total}] Error: {user_name} ({user_email}): {str(e)} ({time.time() - start:.1f}s)")
            return "error"

def main() -> None:
    """Fetch all user signatures and upload them to the shared Drive folder."""
    # 1. Get the list of users
    users = get_all_active_users()

    # 2. Pre-fetch existing files & initialize batch authenticator
    existing_files = get_existing_files()
    gmail_batch = GmailBatchAuthenticator()

    # 3. Process users concurrently
    total = len(users)
    success = 0
    skipped = 0
    errors = 0
    overall_start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(save_signature, gmail_batch, existing_files, user, i + 1, total): user for i, user in enumerate(users)}
        for future in as_completed(futures):
            result = future.result()
            if result == "success":
                success += 1
            elif result == "skipped":
                skipped += 1
            else:
                errors += 1

    elapsed = time.time() - overall_start
    print(f"\nScript finished in {elapsed:.1f}s — {success} saved, {skipped} skipped, {errors} errors.")

if __name__ == "__main__":
    main()
