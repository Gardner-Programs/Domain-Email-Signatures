"""Check team.lead@ group members for any with Template='branch_c' (should be 'branch_c_ii')."""

from __future__ import annotations

import os

import pandas as pd
from authenticator import admin_directory_v1_api

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
GROUP = "team.lead@company.com"
CSV = os.path.join(THIS_DIR, '..', 'output', 'signature_info_export.csv')

def _get_members(service: object, group_email: str) -> list[dict]:
    """Return all members of *group_email* using the Admin Directory API."""
    members: list[dict] = []
    page_token = None
    while True:
        result = service.members().list(groupKey=group_email, pageToken=page_token).execute()
        members.extend(result.get("members", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return members


def main() -> None:
    """Print group members whose Template is 'branch_c' when it should be 'branch_c_ii'."""
    service = admin_directory_v1_api()
    print(f"Fetching members of {GROUP}...")
    members = _get_members(service, GROUP)
    member_emails = {m.get("email", "").lower() for m in members if m.get("email")}
    print(f"Found {len(member_emails)} members.\n")

    df = pd.read_csv(CSV)
    df["Email_lower"] = df["Email"].str.lower()
    in_group = df[df["Email_lower"].isin(member_emails)].copy()

    print(f"Matched {len(in_group)} group members against signature CSV.\n")

    cols = ["Email", "Full Name", "Template", "Location"]
    cols = [c for c in cols if c in in_group.columns]

    print("=== All group members (Template / Location) ===")
    print(in_group[cols].to_string(index=False))

    print("\n=== Flagged: Template == 'branch_c' (should be 'branch_c_ii') ===")
    flagged = in_group[in_group["Template"].astype(str).str.lower() == "branch_c"]
    if flagged.empty:
        print("None — no members listed as plain 'branch_c'.")
    else:
        print(flagged[cols].to_string(index=False))

    print("\n=== Members in group but missing from CSV ===")
    missing = member_emails - set(df["Email_lower"])
    for e in sorted(missing):
        print(f"  {e}")

if __name__ == "__main__":
    main()
