"""
Office Template Preview Generator
Generates JPG preview images for all office template roster users using their live directory data.
Output: output/office_template_review/
"""
from __future__ import annotations

import os

import imgkit
from authenticator import admin_directory_v1_api
from email_templates import set_html_template

DOMAIN = "company.com"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "office_template_review")

# Example entries — replace with your actual users
ROSTER = [
    {"email": "john.doe@company.com",   "template": "office_template"},
    {"email": "jane.smith@company.com", "template": "carrier_sales_template"},
]


def fetch_user(service, email: str) -> dict | None:
    """Return the full user record for *email*, or None if not found."""
    result = service.users().list(
        domain=DOMAIN, maxResults=1, orderBy="email",
        query=f"email={email}", projection="full"
    ).execute()
    users = result.get("users", [])
    return users[0] if users else None


def generate() -> None:
    """Generate JPG signature previews for every entry in ROSTER."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    service = admin_directory_v1_api()
    success, errors = 0, []

    for person in ROSTER:
        email = person["email"]
        user = fetch_user(service, email)
        if not user:
            errors.append(f"[NOT FOUND] {email}")
            continue

        fullname = user.get("name", {}).get("fullName", "Unknown")
        sig_data = user.get("customSchemas", {}).get("Signature_Info", {})

        html = set_html_template(
            template=person["template"],
            fullname=fullname,
            title=sig_data.get("Title", ""),
            location=sig_data.get("Location", ""),
            email=email,
            ext=sig_data.get("Extension", ""),
            direct=sig_data.get("Direct_Line", ""),
            cell=sig_data.get("Cell", ""),
            ltl=sig_data.get("LTL_Disclaimer", False),
            about=sig_data.get("About", "")
        )

        safe_name = fullname.replace(" ", "_")
        tmp_html = os.path.join(OUTPUT_DIR, f"{safe_name}.html")
        img_path = os.path.join(OUTPUT_DIR, f"{safe_name}.jpg")

        with open(tmp_html, "w", encoding="utf-8") as f:
            f.write(html)

        try:
            options = {"width": 600, "disable-smart-width": ""}
            imgkit.from_file(tmp_html, img_path, options=options)
            print(f"[OK] {fullname}")
            success += 1
        except Exception as e:
            errors.append(f"[IMG ERROR] {fullname}: {e}")
        finally:
            if os.path.exists(tmp_html):
                os.remove(tmp_html)

    print(f"\n{'='*50}")
    print(f"Generated: {success}/{len(ROSTER)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(f"  {e}")
    print(f"Output: {os.path.abspath(OUTPUT_DIR)}")


if __name__ == "__main__":
    generate()
