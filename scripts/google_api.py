"""Bulk email signature update script — updates all active domain users in parallel."""

from __future__ import annotations

import base64
import concurrent.futures
import time
import random
from email.message import EmailMessage
from email_templates import set_html_template
from authenticator import admin_directory_v1_api, gmail_v1_api, GmailBatchAuthenticator

# --- Constants ---
DOMAIN = "company.com"
ADMIN_EMAIL = "it@company.com"
SENDER_EMAIL = "formresponse@company.com"

# 15 is a sweet spot for Google API rate limits (avoiding 429 errors)
MAX_WORKERS = 15

def send_error_report(to: str, subject: str, error_list: list[str]) -> None:
    """Send a single summary email containing all logged errors."""
    if not error_list:
        return

    print("Sending error report...")
    body_text = "The following errors occurred during the signature update:\n\n" + "\n".join(error_list)

    try:
        gmail_service = gmail_v1_api(SENDER_EMAIL)
        message = EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body_text)

        encoded_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
        gmail_service.users().messages().send(userId="me", body=encoded_message).execute()
        print("Error report sent successfully.")
    except Exception as e:
        print(f"Failed to send error report: {e}")

def get_all_active_users() -> list[dict]:
    """Fetch all active, non-suspended domain users (excluding /Non-User Accounts)."""
    service = admin_directory_v1_api()
    all_users = []
    page_token = None

    print("Fetching full user directory...")

    # Query: Not suspended
    query = "isSuspended=false"

    while True:
        try:
            result = service.users().list(
                domain=DOMAIN,
                maxResults=500,
                orderBy="email",
                projection="full",
                query=query,
                pageToken=page_token
            ).execute()
        except Exception as e:
            print(f"Critical API Error fetching users: {e}")
            break

        users = result.get("users", [])

        for user in users:
            # Filter out non-user accounts locally
            if user.get("orgUnitPath") != "/Non-User Accounts":
                all_users.append(user)

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    print(f"Directory fetch complete. Found {len(all_users)} eligible users.")
    return all_users

def process_user_signature(user: dict) -> str | None:
    """Build and push the Gmail signature for a single user.

    Returns None on success or a formatted error string on failure.
    Safe to call from multiple threads — creates its own API connections.
    """
    # Safe extraction of data
    email = user.get("primaryEmail", "").lower()
    name_data = user.get("name", {})
    fullname = name_data.get("fullName", "Employee")

    custom_schemas = user.get("customSchemas", {})
    sig_data = custom_schemas.get("Signature_Info", {})

    title = sig_data.get("Title", "")
    location = sig_data.get("Location", "")

    # INDIVIDUAL OUTLIERS CHECK
    # Example entries — replace with your actual users
    INDIVIDUAL_OVERRIDES = {
        "john.doe@company.com": "office_template",
        "jane.smith@company.com": "office_template",
    }

    template = sig_data.get("Template", "default").lower().replace(" ", "_")

    # Safety net: If the template in the directory is still an old one, or
    # we need to ensure outliers get their exact template
    if email in INDIVIDUAL_OVERRIDES:
        template = INDIVIDUAL_OVERRIDES[email]

    params = {
        "template": template,
        "fullname": fullname,
        "title": title,
        "location": location,
        "email": email,
        "ext": sig_data.get("Extension", ""),
        "direct": sig_data.get("Direct_Line", ""),
        "cell": sig_data.get("Cell", ""),
        "ltl": sig_data.get("LTL_Disclaimer", False),
        "about": sig_data.get("About", "")
    }

    # --- ISOLATED AUTHENTICATOR ---
    # We initialize this HERE so each thread has its own connection.
    try:
        local_auth = GmailBatchAuthenticator()
    except Exception as e:
        error_msg = f"[CRITICAL AUTH FAIL] Could not init auth for {email}: {e}"
        print(error_msg)
        return error_msg

    for attempt in range(3):
        try:
            html = set_html_template(**params)

            # Use the local authenticator
            service = local_auth.get_service(email)

            data = {"signature": html}
            service.users().settings().sendAs().patch(
                userId="me",
                sendAsEmail=email,
                body=data
            ).execute()

            print(f"[SUCCESS] Updated {fullname}")
            return None

        except Exception as e:
            err_msg = str(e)

            # Filter out expected errors (Silent skip)
            if "HttpError 404" in err_msg:
                # Uncomment the line below if you want to see skips in the log
                # print(f"[SKIP] {email} (No Gmail Inbox)")
                return None

            if "400" in err_msg or "429" in err_msg or "500" in err_msg or "503" in err_msg:
                wait_time = (2 ** attempt) + random.uniform(1, 3)
                print(f"[RETRYING] {email} in {wait_time:.2f}s... (Server Error)")
                time.sleep(wait_time)
                continue

            # PRINT UNEXPECTED ERRORS IMMEDIATELY
            full_error = f"[FAILED] {email} | Template: {params['template']} | Error: {err_msg}"
            print(full_error)
            return full_error

    return f"FAILED: {email} - Max retries exceeded."

if __name__ == "__main__":
    all_errors = []

    # 1. GET USERS
    users_list = get_all_active_users()

    # 2. PROCESS IN PARALLEL
    if users_list:
        print(f"Starting updates with {MAX_WORKERS} workers...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for user in users_list:
                # Pass ONLY the user dictionary
                future = executor.submit(process_user_signature, user)
                futures.append(future)

                # Small delay to prevent hammering the API instantly
                time.sleep(0.01)

            # Gather results as they finish
            print("Tasks submitted. Processing...")
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    all_errors.append(result)

    # 3. REPORTING
    if all_errors:
        print(f"\nProcess finished with {len(all_errors)} errors.")
        print("-" * 40)
        for err in all_errors[:10]:
            print(err)
        if len(all_errors) > 10:
            print(f"...and {len(all_errors)-10} more.")
        print("-" * 40)

        send_error_report(ADMIN_EMAIL, "Script Errors: Email Signature Update", all_errors)
    else:
        print("\nProcess finished successfully with ZERO errors.")
