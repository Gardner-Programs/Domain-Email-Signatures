"""Quick verification: checks office template roster users' profile + custom schema fields."""
from authenticator import admin_directory_v1_api

service = admin_directory_v1_api()

# Example entries — replace with your actual users
ROSTER = [
    {"email": "john.doe@company.com",   "template": "office_template",       "title": "Account Manager",      "direct": "555-000-0001"},
    {"email": "jane.smith@company.com", "template": "carrier_sales_template", "title": "Carrier Sales Rep",    "direct": "555-000-0002"},
]

issues = []
for p in ROSTER:
    email = p["email"]
    try:
        result = service.users().list(
            domain="company.com", maxResults=1, orderBy="email",
            query=f"email={email}", projection="full"
        ).execute()
        users = result.get("users", [])
        if not users:
            issues.append(f"[NOT FOUND] {email}")
            continue
        user = users[0]
        sig = user.get("customSchemas", {}).get("Signature_Info", {})
        orgs = user.get("organizations", [{}])
        profile_title = orgs[0].get("title", "") if orgs else ""

        diffs = []
        if sig.get("Template", "") != p["template"]:
            diffs.append(f"  Template: '{sig.get('Template','')}' (expected '{p['template']}')")
        if sig.get("Title", "") != p["title"]:
            diffs.append(f"  Schema Title: '{sig.get('Title','')}' (expected '{p['title']}')")
        if profile_title != p["title"]:
            diffs.append(f"  Profile Title: '{profile_title}' (expected '{p['title']}')")
        if not sig.get("LTL_Disclaimer", False):
            diffs.append("  LTL_Disclaimer: False (expected True)")
        if p["direct"] and sig.get("Direct_Line", "") != p["direct"]:
            diffs.append(f"  Direct_Line: '{sig.get('Direct_Line','')}' (expected '{p['direct']}')")

        if diffs:
            issues.append(f"[MISMATCH] {email}")
            for d in diffs:
                issues.append(d)
        else:
            print(f"[OK] {email}")
    except Exception as e:
        issues.append(f"[ERROR] {email}: {e}")

if issues:
    print()
    for i in issues:
        print(i)
else:
    print("\nAll users verified - no issues found.")
