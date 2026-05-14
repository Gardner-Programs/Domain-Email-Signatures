from authenticator import admin_directory_v1_api, gmail_v1_api
from email_templates import set_html_template, CONFIGS
import imgkit
import os
import re  # Added for safe HTML injection

# --- Configuration: Debug Overlay ---
# This HTML snippet is injected only during 'start_all'
DEBUG_OVERLAY_HTML = """
<div style="
    position: absolute;
    top: 0;
    right: 0;
    background-color: #d90429;
    color: #ffffff;
    padding: 6px 12px;
    font-family: sans-serif;
    font-size: 14px;
    font-weight: bold;
    z-index: 999999;
    opacity: 0.9;
    border-bottom-right-radius: 5px;
    pointer-events: none;">
    {name}
</div>
"""

# --- Helper: Update Gmail Signature ---
def set_signature(email, html):
    """Updates the live Gmail signature for the user."""
    try:
        DATA = {"signature": html}
        gmail_service = gmail_v1_api(email)
        send_signature = gmail_service.users().settings().sendAs().patch(
            userId="me",
            sendAsEmail=email,
            body=DATA
        ).execute()
        print(f"Successfully updated signature for {email}")
        return send_signature.get("signature", None)
    except Exception as e:
        print(f"Error updating signature: {e}")
        return None

# --- Helper: Generate Image Preview ---
def generate_preview_image(email, html, template_name):
    """Generates a JPG preview of the signature in the Downloads folder."""

    # robust path finding (works for any user)
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

    # Create filenames with the template name appended
    html_filename = f"{email}_{template_name}.html"
    img_filename = f"{email}_{template_name}.jpg"

    html_path = os.path.join(downloads_path, html_filename)
    img_path = os.path.join(downloads_path, img_filename)

    try:
        # Write HTML file
        with open(html_path, "w", encoding="utf-8") as file:
            file.write(html)

        # Convert to Image
        options = {"width": 600, "disable-smart-width": ""}
        imgkit.from_file(html_path, img_path, options=options)
        os.system(img_path)  # Optional: Open image automatically
        print(f"Generated preview: {img_filename}")

    except Exception as e:
        print(f"Error generating image for {template_name}: {e}")

# --- Helper: Extract User Data ---
def get_user_data(user):
    """Unpacks user data safely, similar to google_api.py"""
    fullname = user["name"]["fullName"]
    email = user["primaryEmail"]
    sig_data = user.get("customSchemas", {}).get("Signature_Info", {})
    print(sig_data)

    return {
        "fullname": fullname,
        "title": sig_data.get("Title", ""),
        "location": sig_data.get("Location", ""),
        "email": email,
        "ext": sig_data.get("Extension", ""),
        "direct": sig_data.get("Direct_Line", ""),
        "cell": sig_data.get("Cell", ""),
        "about": sig_data.get("About", ""),
        "ltl": sig_data.get("LTL_Disclaimer", False),
        "current_template": sig_data.get("Template", "regional_template")
    }

# --- MAIN FUNCTION 1: Update Single User ---
def start(userEmail):
    """
    Updates the LIVE signature for the specific user based on their
    current directory settings.
    """
    print(f"Fetching data for {userEmail}...")
    service = admin_directory_v1_api()
    result = service.users().list(
        domain="company.com",
        maxResults=1,
        orderBy="email",
        query=f"email={userEmail}",
        projection="full"
    ).execute()

    users = result.get("users", [])
    if not users:
        print("User not found.")
        return

    user = users[0]
    data = get_user_data(user)

    # Generate HTML using the user's assigned template
    html = set_html_template(
        template=data["current_template"],
        fullname=data["fullname"],
        title=data["title"],
        location=data["location"],
        email=data["email"],
        ext=data["ext"],
        cell=data["cell"],
        direct=data["direct"],
        about=data["about"]
    )

    # 1. Update Live Signature
    set_signature(data["email"], html)

    # 2. Generate a proof image (Optional, but good for verification)
    generate_preview_image(data["email"], html, data["current_template"])


# --- MAIN FUNCTION 2: Test All Templates ---
def start_all(userEmail):
    """
    Does NOT update live signatures.
    Generates a preview image for EVERY template using the user's info.
    INJECTS TEMPLATE NAME into the top of the image.
    """
    print(f"Fetching data for {userEmail} to test all templates...")
    service = admin_directory_v1_api()
    result = service.users().list(
        domain="company.com",
        maxResults=1,
        orderBy="email",
        query=f"email={userEmail}",
        projection="full"
    ).execute()

    users = result.get("users", [])
    if not users:
        print("User not found.")
        return

    user = users[0]
    data = get_user_data(user)

    # List of all templates found in email_templates.py
    all_templates = list(CONFIGS.keys())

    print(f"Generating images for {len(all_templates)} templates...")

    for temp_name in all_templates:
        # Generate HTML for this specific template using the user's data

        html = set_html_template(
            template=temp_name,
            fullname=data["fullname"],
            title=data["title"],
            location=data["location"],
            email=data["email"],
            ext=data["ext"],
            cell=data["cell"],
            direct=data["direct"],
            ltl=data["ltl"],
            about=data["about"]
        )

        # --- INJECT DEBUG OVERLAY ---
        # This adds the template name to the visual output without breaking layout
        overlay = DEBUG_OVERLAY_HTML.format(name=temp_name)

        # Check if <body> exists to inject properly, otherwise prepend
        if "<body" in html:
            # Regex to find <body ...> or <body> and insert overlay immediately after
            html = re.sub(r'(<body[^>]*>)', r'\1' + overlay, html, count=1, flags=re.IGNORECASE)
        else:
            # Fallback for templates without body tags
            html = overlay + html
        # ----------------------------

        # Only generate image, do NOT update live signature
        generate_preview_image(data["email"], html, temp_name)

    print("Batch generation complete. Check your Downloads folder.")


start_all("admin@company.com")
