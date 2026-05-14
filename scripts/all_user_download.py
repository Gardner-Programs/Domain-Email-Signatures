"""Export all active domain users to a CSV file."""

from __future__ import annotations

import os
import pandas
from google_api import get_all_active_users

DOMAIN = "company.com"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def main() -> None:
    """Fetch all active users and write them to all_active_users.csv."""
    users = get_all_active_users()
    pandas.DataFrame(users).to_csv(os.path.join(OUTPUT_DIR, "all_active_users.csv"), index=False)
    print(f"Exported {len(users)} users to all_active_users.csv")


if __name__ == "__main__":
    main()
