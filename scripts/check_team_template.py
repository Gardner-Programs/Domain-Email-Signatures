"""Check team.lead@ group members for any with Template='branch_c' (should be 'branch_c_ii')."""
import os, sys
import pandas as pd

# Reuse Google_Workspace helpers
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
GW_SCRIPTS = os.path.join(THIS_DIR, '..', '..', 'Google_Workspace', 'scripts')
sys.path.insert(0, os.path.abspath(GW_SCRIPTS))
from _master import get_service, get_members  # noqa: E402

GROUP = "team.lead@company.com"
CSV = os.path.join(THIS_DIR, '..', 'output', 'signature_info_export.csv')

def main():
    service = get_service()
    print(f"Fetching members of {GROUP}...")
    members = get_members(service, GROUP) or []
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
