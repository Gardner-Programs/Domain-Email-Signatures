"""
Google API authenticator for Email Signature scripts.

Resolves credential file paths in the following priority order:
    1. KEY_PATH / SECRET_PATH environment variables
    2. Current working directory
    3. /home/ubuntu/.creds (Linux server deploy)
    4. ../Keys/ relative to this repo

Required files (place in any of the above locations):
    service-account-key.json  — Google service account key
    credentials.json          — OAuth2 client secrets (only needed for admin_reports_v1_api)
    .env                      — Optional: KEY_PATH, SECRET_PATH, ENV_PATH, ADMIN_EMAIL

Environment variables:
    ADMIN_EMAIL   — Default delegated admin email for API calls
    KEY_PATH      — Absolute path to service-account-key.json
    SECRET_PATH   — Absolute path to credentials.json
    ENV_PATH      — Absolute path to .env file
"""

from __future__ import annotations

import os
import os.path
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, build_from_document
from google.oauth2 import service_account
from dotenv import load_dotenv

# --- File names ---
KEY_FILE = "service-account-key.json"
SECRET_FILE = "credentials.json"
ENV_FILE = ".env"

# --- Default path roots ---
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_KEYS_DIR = os.path.join(_REPO_ROOT, "Keys")
_LINUX_CREDS_DIR = "/home/ubuntu/.creds"

# --- Resolve .env location ---
_env_override = os.environ.get("ENV_PATH", "").strip()
if _env_override and os.path.exists(_env_override):
    env_path = _env_override
elif os.path.exists(os.path.join(os.getcwd(), ENV_FILE)):
    env_path = os.path.join(os.getcwd(), ENV_FILE)
elif os.path.exists(os.path.join(_LINUX_CREDS_DIR, ENV_FILE)):
    env_path = os.path.join(_LINUX_CREDS_DIR, ENV_FILE)
else:
    env_path = os.path.join(_DEFAULT_KEYS_DIR, ENV_FILE)

load_dotenv(dotenv_path=env_path)

# --- Resolve credential file paths ---
_env_key_path = os.environ.get("KEY_PATH", "").strip()
_env_secret_path = os.environ.get("SECRET_PATH", "").strip()

if _env_key_path and os.path.exists(_env_key_path):
    key_path = _env_key_path
    secret_path = _env_secret_path or os.path.join(os.path.dirname(_env_key_path), SECRET_FILE)
elif os.path.exists(os.path.join(os.getcwd(), KEY_FILE)):
    key_path = os.path.join(os.getcwd(), KEY_FILE)
    secret_path = os.path.join(os.getcwd(), SECRET_FILE)
elif os.path.exists(os.path.join(_LINUX_CREDS_DIR, KEY_FILE)):
    key_path = os.path.join(_LINUX_CREDS_DIR, KEY_FILE)
    secret_path = os.path.join(_LINUX_CREDS_DIR, SECRET_FILE)
else:
    key_path = os.path.join(_DEFAULT_KEYS_DIR, KEY_FILE)
    secret_path = os.path.join(_DEFAULT_KEYS_DIR, SECRET_FILE)

# --- Default admin email ---
_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", os.environ.get("EMAIL", ""))


# --- API builders ---

def sheets_credentials() -> service_account.Credentials:
    """Return service account credentials scoped for Google Sheets and Drive."""
    return service_account.Credentials.from_service_account_file(
        key_path,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://spreadsheets.google.com/feeds",
        ],
    )


def gmail_v1_api(user: str = "") -> object:
    """Return a Gmail API v1 service delegated to *user* (defaults to ADMIN_EMAIL)."""
    user = user or _ADMIN_EMAIL
    scopes = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://mail.google.com/",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.settings.basic",
        "https://www.googleapis.com/auth/gmail.settings.sharing",
    ]
    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return build("gmail", "v1", credentials=credentials.with_subject(user), cache_discovery=False)


def admin_directory_v1_api(user: str = "") -> object:
    """Return an Admin Directory API v1 service delegated to *user* (defaults to ADMIN_EMAIL)."""
    user = user or _ADMIN_EMAIL
    scopes = [
        "https://www.googleapis.com/auth/admin.directory.user",
        "https://www.googleapis.com/auth/admin.directory.orgunit",
        "https://www.googleapis.com/auth/admin.directory.group",
        "https://www.googleapis.com/auth/admin.directory.device.mobile.readonly",
        "https://www.googleapis.com/auth/admin.directory.device.chromeos.readonly",
        "https://www.googleapis.com/auth/admin.directory.userschema",
    ]
    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return build("admin", "directory_v1", credentials=credentials.with_subject(user), cache_discovery=False)


def drive_v3_api(user: str = "") -> object:
    """Return a Drive API v3 service delegated to *user* (defaults to ADMIN_EMAIL)."""
    user = user or _ADMIN_EMAIL
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]
    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return build("drive", "v3", credentials=credentials.with_subject(user), cache_discovery=False)


def drive_v2_api(user: str = "") -> object:
    """Return a Drive API v2 service delegated to *user* (defaults to ADMIN_EMAIL)."""
    user = user or _ADMIN_EMAIL
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]
    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return build("drive", "v2", credentials=credentials.with_subject(user), cache_discovery=False)


def calendar_v3_api(user: str = "") -> object:
    """Return a Calendar API v3 service delegated to *user* (defaults to ADMIN_EMAIL)."""
    user = user or _ADMIN_EMAIL
    credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=credentials.with_subject(user), cache_discovery=False)


def cloud_identity_v1_api(user: str = "") -> object:
    """Return a Cloud Identity API v1 service delegated to *user* (defaults to ADMIN_EMAIL)."""
    user = user or _ADMIN_EMAIL
    credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/cloud-identity.devices.readonly"]
    )
    return build("cloudidentity", "v1", credentials=credentials.with_subject(user), cache_discovery=False)


def admin_reports_v1_api() -> object:
    """Return an Admin Reports API v1 service via OAuth2 user flow.

    Prompts for browser authentication on first run; caches token in token.json.
    """
    scopes = ["https://www.googleapis.com/auth/admin.reports.audit.readonly"]
    token_path = "token.json"
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secret_path, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("admin", "reports_v1", credentials=creds, cache_discovery=False)


def custom_api_build(service_name: str, version: str, scopes: list[str], user: str = "") -> object:
    """Return an arbitrary Google API service delegated to *user*.

    Args:
        service_name: Google API name (e.g. "gmail", "admin")
        version: API version string (e.g. "v1", "directory_v1")
        scopes: List of OAuth2 scope URLs
        user: Email to delegate to; defaults to ADMIN_EMAIL
    """
    user = user or _ADMIN_EMAIL
    credentials = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return build(service_name, version, credentials=credentials.with_subject(user))


class GmailBatchAuthenticator:
    """Optimized authenticator for concurrent Gmail batch operations.

    Loads the service account credentials and Gmail API discovery document once,
    then builds per-user delegated services cheaply from the cached resources.
    This avoids ~700 redundant network calls when processing large user lists.
    """

    def __init__(self) -> None:
        self.base_creds = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=[
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://mail.google.com/",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/gmail.settings.basic",
                "https://www.googleapis.com/auth/gmail.settings.sharing",
            ],
        )
        response = requests.get("https://gmail.googleapis.com/$discovery/rest?version=v1")
        self.discovery_doc = response.json()

    def get_service(self, user_email: str) -> object:
        """Return a Gmail API service delegated to *user_email* using cached credentials."""
        delegated_creds = self.base_creds.with_subject(user_email)
        return build_from_document(self.discovery_doc, credentials=delegated_creds)
