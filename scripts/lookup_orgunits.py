"""Look up org unit paths for branch_c / branch_c_ii users from the signature CSV."""

from __future__ import annotations

import os

import pandas as pd
from authenticator import admin_directory_v1_api

CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output', 'signature_info_export.csv')


def main() -> None:
    """Print email, full name, template, and org unit for branch_c/branch_c_ii users."""
    df = pd.read_csv(CSV)
    branch_c_users = df[df['Template'].isin(['branch_c', 'branch_c_ii'])].copy()

    service = admin_directory_v1_api()
    org_units = []
    for email in branch_c_users['Email']:
        u = service.users().get(userKey=email, projection='basic').execute()
        org_units.append(u.get('orgUnitPath', ''))

    branch_c_users['OrgUnit'] = org_units
    print(branch_c_users[['Email', 'Full Name', 'Template', 'OrgUnit']].to_string(index=False))


if __name__ == "__main__":
    main()
