"""
Bulk-update a single Signature_Info field across a list of users.

Use this when many users all need the same field set to the same value
(e.g. flip a whole team from Template='branch_c' to 'branch_c_ii'). For mixed
updates where each user gets different values, use update_sig_info.py.

Usage:
    python update_sig_field.py             # dry-run (default)
    python update_sig_field.py --apply     # commit changes

Edit FIELD, NEW_VALUE, EXPECTED_CURRENT, and TARGETS at the top of the file.
EXPECTED_CURRENT acts as a safety guard: users whose current value doesn't
match are skipped (set to None to disable the guard).
"""
from __future__ import annotations

import sys
import time

from authenticator import admin_directory_v1_api

SCHEMA_NAME = "Signature_Info"
DOMAIN = "company.com"

# ---- EDIT FOR EACH RUN ----
FIELD = "Template"               # Signature_Info field name (case-sensitive)
NEW_VALUE = "branch_c_ii"
EXPECTED_CURRENT = "branch_c"   # set to None to skip the guard
# Example entries — replace with your actual users
TARGETS = [
    "john.doe@company.com",
    "jane.smith@company.com",
]


def run_updates(dry_run: bool = True) -> None:
    """Apply (or preview) a bulk field update for all TARGETS.

    Args:
        dry_run: When True, print intended changes without writing to the API.
    """
    service = admin_directory_v1_api()
    errors, changes, skipped = [], [], []

    for email in TARGETS:
        try:
            result = service.users().list(
                domain=DOMAIN, maxResults=1, orderBy="email",
                query=f"email={email}", projection="full",
            ).execute()
            users = result.get("users", [])
            if not users:
                errors.append(f"[NOT FOUND] {email}")
                continue
        except Exception as e:
            errors.append(f"[FETCH ERROR] {email}: {e}")
            continue

        sig_data = users[0].get("customSchemas", {}).get(SCHEMA_NAME, {})
        default = False if isinstance(NEW_VALUE, bool) else ""
        current = sig_data.get(FIELD, default)

        if current == NEW_VALUE:
            print(f"[NO CHANGE] {email} ({FIELD}={NEW_VALUE!r})")
            skipped.append(email)
            continue

        if EXPECTED_CURRENT is not None and current != EXPECTED_CURRENT:
            print(f"[SKIP] {email} — {FIELD} is {current!r}, not {EXPECTED_CURRENT!r}. Refusing to overwrite.")
            skipped.append(email)
            continue

        print(f"[UPDATE] {email}")
        print(f"  {FIELD}: {current!r} -> {NEW_VALUE!r}")
        changes.append(email)

        if not dry_run:
            try:
                body = {"customSchemas": {SCHEMA_NAME: {FIELD: NEW_VALUE}}}
                service.users().patch(userKey=email, body=body).execute()
                print("  >> Updated successfully")
                time.sleep(0.3)
            except Exception as e:
                err = f"[UPDATE ERROR] {email}: {e}"
                print(f"  >> {err}")
                errors.append(err)

    print(f"\n{'='*60}")
    print(f"{'DRY RUN ' if dry_run else ''}SUMMARY")
    print(f"{'='*60}")
    print(f"  Field:         {FIELD} -> {NEW_VALUE!r}")
    if EXPECTED_CURRENT is not None:
        print(f"  Guard:         only update if current == {EXPECTED_CURRENT!r}")
    print(f"  Targets:       {len(TARGETS)}")
    print(f"  Will update:   {len(changes)}")
    print(f"  Skipped:       {len(skipped)}")
    print(f"  Errors:        {len(errors)}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e}")
    if dry_run and changes:
        print("\nDRY RUN — re-run with --apply to commit.")


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    run_updates(dry_run=dry)
