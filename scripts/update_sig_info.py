"""
Generic Signature_Info reconciliation script.

Updates the standard Google profile title AND the Signature_Info custom schema
for any user listed in ROSTER. Only fields present in each roster entry are
patched — omit fields you don't want to touch.

Usage:
    python update_sig_info.py            # dry-run (default)
    python update_sig_info.py --apply    # apply changes

Roster entry shape — only 'email' is required, every other field is optional:
    {
        "email":          "user@company.com",
        "template":       "office_template",   # Signature_Info.Template
        "title":          "Account Manager",   # schema Title AND profile organizations[0].title
        "location":       "Branch G",          # Signature_Info.Location
        "ltl_disclaimer": True,                # Signature_Info.LTL_Disclaimer
        "extension":      "1234",              # Signature_Info.Extension
        "direct_line":    "555-000-0001",      # Signature_Info.Direct_Line
        "cell":           "555-000-0002",      # Signature_Info.Cell
        "about":          "Some bio text",     # Signature_Info.About
    }
"""
from __future__ import annotations

import sys
import time
from authenticator import admin_directory_v1_api

SCHEMA_NAME = "Signature_Info"
DOMAIN = "company.com"

# Map roster keys -> Signature_Info schema field names
SCHEMA_FIELDS = {
    "template":       "Template",
    "title":          "Title",
    "location":       "Location",
    "ltl_disclaimer": "LTL_Disclaimer",
    "extension":      "Extension",
    "direct_line":    "Direct_Line",
    "cell":           "Cell",
    "about":          "About",
}

# Edit this list to drive updates. See module docstring for entry shape.
# Example entries — replace with your actual users
ROSTER = [
    # {"email": "john.doe@company.com", "template": "office_template", "title": "Account Manager"},
    # {"email": "jane.smith@company.com", "template": "regional_template", "title": "Operations Specialist"},
]


def run_updates(roster: list[dict], dry_run: bool = True) -> None:
    """Apply (or preview) Signature_Info and profile-title changes from *roster*.

    Args:
        roster: List of update entries; only 'email' is required per entry.
        dry_run: When True, print diffs without writing to the API.
    """
    service = admin_directory_v1_api()
    errors, changes = [], []

    for person in roster:
        email = person.get("email")
        if not email:
            errors.append(f"[BAD ENTRY] missing 'email': {person}")
            continue

        try:
            result = service.users().list(
                domain=DOMAIN,
                maxResults=1,
                orderBy="email",
                query=f"email={email}",
                projection="full",
            ).execute()
            users = result.get("users", [])
            if not users:
                errors.append(f"[NOT FOUND] {email}")
                continue
        except Exception as e:
            errors.append(f"[FETCH ERROR] {email}: {e}")
            continue

        user = users[0]
        sig_data = user.get("customSchemas", {}).get(SCHEMA_NAME, {})
        orgs = user.get("organizations", [{}])
        current_title_profile = orgs[0].get("title", "") if orgs else ""

        diffs = []
        schema_updates = {}
        profile_updates = {}

        for roster_key, schema_key in SCHEMA_FIELDS.items():
            if roster_key not in person:
                continue
            new = person[roster_key]
            default = False if isinstance(new, bool) else ""
            current = sig_data.get(schema_key, default)
            if current != new:
                diffs.append(f"  {schema_key}: {current!r} -> {new!r}")
                schema_updates[schema_key] = new

        if "title" in person and current_title_profile != person["title"]:
            diffs.append(f"  Profile Title: {current_title_profile!r} -> {person['title']!r}")
            profile_updates["title"] = person["title"]

        if not diffs:
            print(f"[NO CHANGE] {email}")
            continue

        print(f"\n[UPDATE] {email}")
        for d in diffs:
            print(d)
        changes.append(email)

        if not dry_run:
            try:
                body = {}
                if schema_updates:
                    body["customSchemas"] = {SCHEMA_NAME: schema_updates}
                if profile_updates:
                    body["organizations"] = [{"title": profile_updates["title"], "primary": True}]
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
    print(f"  Roster size:   {len(roster)}")
    print(f"  Will update:   {len(changes)}")
    print(f"  No changes:    {len(roster) - len(changes) - len(errors)}")
    print(f"  Errors:        {len(errors)}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  {e}")
    if dry_run and changes:
        print("\nDRY RUN — re-run with --apply to commit changes.")


if __name__ == "__main__":
    dry = "--apply" not in sys.argv
    run_updates(ROSTER, dry_run=dry)
