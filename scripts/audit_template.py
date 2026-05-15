"""Audit office-template users against SOP requirements and export a compliance CSV."""

from __future__ import annotations

import os
import pandas as pd
from authenticator import admin_directory_v1_api

# --- Configuration ---
DOMAIN = "company.com"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
OFFICE_ORG_UNIT = "/All Sites/Branch G-II"
VALID_OFFICE_TEMPLATES = {"office_template", "carrier_sales_template", "office_template_track_trace"}
CARRIER_SALES_TITLES = {"carrier sales rep", "carrier team lead", "carrier sales manager"}

def get_office_users() -> list[dict]:
    """Fetch all active users in the office-template org unit."""
    service = admin_directory_v1_api()
    all_users = []
    page_token = None

    print("Fetching office template users...")
    while True:
        result = service.users().list(
            domain=DOMAIN,
            maxResults=500,
            orderBy="email",
            projection="full",
            query=f"isSuspended=false orgUnitPath='{OFFICE_ORG_UNIT}'",
            pageToken=page_token
        ).execute()

        users = result.get("users", [])
        all_users.extend(users)

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    print(f"Found {len(all_users)} active users in {OFFICE_ORG_UNIT}.\n")
    return all_users

def audit_user(user: dict) -> dict:
    """Check a single user against SOP requirements and return a findings dict."""
    email = user.get("primaryEmail", "").lower()
    fullname = user.get("name", {}).get("fullName", "Unknown")
    sig_data = user.get("customSchemas", {}).get("Signature_Info", {})
    template = sig_data.get("Template", "").lower().replace(" ", "_")
    location = sig_data.get("Location", "")
    cell = sig_data.get("Cell", "")
    direct = sig_data.get("Direct_Line", "")
    title = sig_data.get("Title", "")
    ltl = sig_data.get("LTL_Disclaimer", False)

    issues = []

    # 1. Template must be a valid office template
    if template not in VALID_OFFICE_TEMPLATES:
        issues.append(f"TEMPLATE: '{template}' is not a valid office template")

    # 2. LTL disclaimer (template now forces it, but flag if directory field is False for awareness)
    if not ltl:
        issues.append("LTL: Not set in directory (template will force it)")

    # 3. Cell phone should be populated
    if not cell:
        issues.append("CELL: Empty (requires direct dial listed as Cell Phone)")

    # 4. Carrier sales roles must have escalation template
    if title:
        title_lower = title.lower()
        is_carrier_sales_role = any(role in title_lower for role in CARRIER_SALES_TITLES)
        if is_carrier_sales_role and template != "carrier_sales_template":
            issues.append(f"ESCALATION: Title '{title}' requires carrier_sales_template, has '{template}'")

    return {
        "Email": email,
        "Name": fullname,
        "Title": title,
        "Template": template,
        "Location": location,
        "Cell": cell,
        "Direct": direct,
        "LTL": ltl,
        "Issues": " | ".join(issues) if issues else "OK"
    }

if __name__ == "__main__":
    users = get_office_users()

    if not users:
        print("No users found. Check the org unit path.")
        exit()

    results = [audit_user(u) for u in users]
    df = pd.DataFrame(results)

    # Summary
    ok_count = len(df[df["Issues"] == "OK"])
    issue_count = len(df[df["Issues"] != "OK"])

    print(f"{'='*80}")
    print(f"OFFICE TEMPLATE SOP AUDIT - {len(results)} employees")
    print(f"{'='*80}")
    print(f"  Compliant: {ok_count}")
    print(f"  Issues:    {issue_count}")
    print(f"{'='*80}\n")

    # Print issues
    issues_df = df[df["Issues"] != "OK"]
    if not issues_df.empty:
        print("USERS WITH ISSUES:\n")
        for _, row in issues_df.iterrows():
            print(f"  {row['Name']} ({row['Email']})")
            print(f"    Template: {row['Template']} | Title: {row['Title']}")
            for issue in row['Issues'].split(' | '):
                print(f"    >> {issue}")
            print()

    # Save full report
    output_file = os.path.join(OUTPUT_DIR, "office_template_audit.csv")
    df.to_csv(output_file, index=False)
    print(f"Full report saved to {output_file}")
