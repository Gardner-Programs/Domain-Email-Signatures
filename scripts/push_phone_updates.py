"""
One-time script: Push missing/incorrect Direct_Line numbers for office template users.
Update the UPDATES list with the correct email addresses and phone numbers before running.
"""

from __future__ import annotations

import time
from authenticator import admin_directory_v1_api

SCHEMA_NAME = "Signature_Info"

# Example entries — replace with your actual users
UPDATES = [
    {"email": "john.doe@company.com",  "direct": "555-000-0001"},
    {"email": "jane.smith@company.com", "direct": "555-000-0002"},
]


def push_phone_updates(updates: list[dict]) -> None:
    """Patch the Direct_Line field in Signature_Info for each entry in *updates*."""
    service = admin_directory_v1_api()
    for person in updates:
        email = person["email"]
        try:
            body = {
                "customSchemas": {
                    SCHEMA_NAME: {
                        "Direct_Line": person["direct"]
                    }
                }
            }
            service.users().patch(userKey=email, body=body).execute()
            print(f"[OK] {email} -> {person['direct']}")
            time.sleep(0.3)
        except Exception as e:
            print(f"[ERROR] {email}: {e}")

    print("\nDone.")


if __name__ == "__main__":
    push_phone_updates(UPDATES)
