"""Export all domain users' Signature_Info custom schema fields to a CSV file."""

from __future__ import annotations

import os
import time
import pandas as pd
from authenticator import admin_directory_v1_api

# --- CONFIGURATION ---
SCHEMA_NAME = "Signature_Info"
DOMAIN = "company.com"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
CSV_FILENAME = os.path.join(OUTPUT_DIR, "signature_info_export.csv")

def export_schema_to_csv(domain_name: str) -> None:
    """Fetch all active users and write their Signature_Info schema fields to CSV."""
    service = admin_directory_v1_api()
    page_token = None
    all_rows = []
    user_count = 0

    print(f"--- Starting Export for {domain_name} ---")
    print(f"--- Pulling all data from Schema: '{SCHEMA_NAME}' ---")

    while True:
        try:
            # projection="full" is required to see customSchemas
            results = service.users().list(
                domain=domain_name,
                maxResults=500,
                orderBy="email",
                query="isSuspended=false",
                projection="full",
                pageToken=page_token
            ).execute()

            users = results.get('users', [])

            if not users:
                if not page_token: break

            for user in users:
                user_email = user.get("primaryEmail")
                fullname = user.get("name", {}).get("fullName", "N/A")

                # Safely grab the specific custom schema dict
                # Returns empty dict {} if schema doesn't exist for that user
                custom_schemas = user.get("customSchemas", {})
                schema_data = custom_schemas.get(SCHEMA_NAME, {})

                # Create a row with Email first, then unpack all schema fields
                row = {"Email": user_email, "Full Name": fullname}

                # This dynamically adds whatever fields exist in the schema
                # (e.g., Template, LTL_Disclaimer, Title, Cell, etc.)
                row.update(schema_data)

                all_rows.append(row)
                user_count += 1

            # Pagination
            page_token = results.get('nextPageToken')
            if not page_token: break
            time.sleep(0.5)  # Gentle rate limiting

        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            break

    # Convert to DataFrame and Save
    if all_rows:
        df = pd.DataFrame(all_rows)
        # Move 'Email' to the first column explicitly if needed, though usually automatic
        cols = ['Email'] + [c for c in df.columns if c != 'Email']
        df = df[cols]

        df.to_csv(CSV_FILENAME, index=False)
        print(f"Export Complete. Scanned {user_count} users.")
        print(f"Data saved to: {CSV_FILENAME}")
    else:
        print("No data found to export.")

if __name__ == "__main__":
    export_schema_to_csv(DOMAIN)
