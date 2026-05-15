"""
Email signature HTML template builder.

CONFIGS maps template keys to per-template overrides applied on top of the
global defaults.  Call set_html_template() with a user's directory data to
get the final minified HTML string ready to push to the Gmail API.
"""
from __future__ import annotations

import html

# --- 1. ASSETS & TEXT BLOCKS ---
_ASSET_BASE = "https://company.com/wp-content/uploads/email-assets"
URLS = {
    "logo_circle":    f"{_ASSET_BASE}/logo_circle.jpg",
    "logo_transport": f"{_ASSET_BASE}/logo_transport.jpg",
    "icon_fb":        f"{_ASSET_BASE}/icon_fb.jpg",
    "icon_ig":        f"{_ASSET_BASE}/icon_ig.jpg",
    "icon_in":        f"{_ASSET_BASE}/icon_in.jpg",
    "icon_tw":        f"{_ASSET_BASE}/icon_tw.jpg",
    "icon_top100":    f"{_ASSET_BASE}/icon_top100.jpg",
    "header_hq":      f"{_ASSET_BASE}/header_hq.jpg",
}

LINKS = {
    "recruiting": '<p style="margin:0;font-size:9pt;line-height:1.25;">Want to work with us? Please email us <a href="mailto:recruiting@company.com" style="color:#1155cc;text-decoration:underline;">HERE</a></p>',
    "payment": '<p style="margin:0;font-size:9pt;line-height:1.25;">To check the status of a payment, please visit <a href="https://company.com/payment-status-lookup/" style="color:#1155cc;text-decoration:underline;">HERE</a></p>',
    "freight": '<p style="margin:0;font-size:9pt;line-height:1.5;">To see all of our available freight, please visit <a href="https://tpx.transportpro.net/availablefreight?cid=YOUR_COMPANY_ID" style="color:#1155cc;text-decoration:underline;">HERE</a></p>',
    "macropoint": '<p style="margin:0;font-size:9pt;line-height:1.25;">Integrate your ELD with MacroPoint to reduce the frequency of check calls. <a href="https://macropoint-lite.com/Connect.aspx?MPID=YOUR_MACROPOINT_ID" style="color:#1155cc;text-decoration:underline;">Click Here!</a></p>',
    "dispatch_addr": '<p style="margin:0;font-size:9pt;font-family:Arial;line-height:1.25;">dispatch@company.com</p><p style="margin:0;font-size:9pt;font-family:Arial;line-height:1.25;"><b>Address:</b> 123 Main St - Branch A, IN 46818</p>',
    "after_hours": '<p style="margin:0;font-size:9pt;line-height:1.25;">afterhours@company.com</p>',
    "chi_track": '<p style="margin:0;font-size:9pt;line-height:1.25;">afterhours@company.com</p><p style="margin:0;font-size:9pt;line-height:1.25;">If you need to track a shipment, follow this <a href="https://tpx.transportpro.net/track?l=YOUR_COMPANY_ID-" style="color:#1155cc;text-decoration:underline;">link</a> and enter our PRO number.</p>',
    "esc_phx": '<p style="margin:0;font-size:9pt;line-height:1.25;"><b>In the event you cannot reach me, please contact our escalation team at escalation@company.com</b></p>'
}

HOTLINES = {
    "default": "<b>24-7 Track &amp; Trace Hotline:</b> 555-000-0001 ext. 2001",
    "expedite": "<b>Expedite Operations Hotline:</b> 555-000-0002<br><b>24-7 Expedite Track &amp; Trace Hotline:</b> 555-000-0003",
    "phx": "<b>24-7 Track &amp; Trace Hotline:</b> 555-000-0004",
    "fraud": "<b>Fraud Verification Hotline:</b> 555-000-0001 ext. 5001<br><b>24-7 Track &amp; Trace Hotline:</b> 555-000-0001 ext. 2001",
    "chi_ds": "<b>24-7 Driver Services Hotline:</b> 555-000-0005 ext. 1301<br>driverservices@company.com",
    "chi_trace": "<b>24-7 Track &amp; Trace Hotline:</b> 555-000-0006",
    "trans_trace": "<b>24-7 Track &amp; Trace Hotline:</b> 555-000-0007 ext. 2001"
}

LTL_LEGAL = """<p style="color: #808080; font-weight: 500; text-decoration: none; vertical-align: baseline; font-size: 9pt; font-family: Arial; font-style: normal; margin-top:10px;">*Unless cargo liability is declared when booking LTL, liability for lost or damaged freight is limited to $0.50 per pound in any event, not to exceed $50,000 per occurrence. Additional insurance is available, by quote, with a declared value. All additional insurance comes with a minimum $500 deductible (or greater based on cargo value) per occurrence.<br><br>**Spot market LTL freight quotes are valid for 5 business days unless otherwise indicated. Please contact us for client specific / program pricing.</p>"""

HQ_HEADER = f"""<table border="0" cellpadding="0" cellspacing="0" style="border-collapse: collapse; font-family: Arial, Helvetica, sans-serif;"><tr><td style="padding-right: 8px; vertical-align: middle;"><a href="https://company.com/"><img src="{URLS['header_hq']}" alt="Company Logo" height="60" style="display: block; border: 0; outline: none; text-decoration: none;"></a></td><td style="color: #0b5394; font-size: 18px; font-weight: bold; font-style: italic; vertical-align: middle; line-height: 120%;">Powered by People. Proven in Performance.</td></tr></table>"""

CONFIGS = {
    # --- GLOBAL DEFAULT ---
    "default":              {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},

    # --- CORPORATE (location-agnostic) ---
    "corp_billing":         {"custom_body": LINKS["payment"], "override_phone": True, "hotline": HOTLINES["default"]},
    "corp_credit":          {"show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},
    "corp_claims":          {"phone_num": "555-000-0001 ext. 1701", "hotline": HOTLINES["default"]},
    "corp_hr":              {"custom_body": LINKS["recruiting"], "hotline": HOTLINES["default"]},
    "corp_fraud":           {"phone_num": "555-000-0005", "hotline": HOTLINES["fraud"], "custom_body": LINKS["macropoint"]},
    "corp_transportation":  {"use_transport_logo": True, "company_name": "Company Transportation, Inc.", "hotline": HOTLINES["trans_trace"], "phone_num": "555-000-0007"},
    "transport_dispatch":   {"use_transport_logo": True, "company_name": "Company Transportation Inc. - MC 299953 | SCAC CLNC", "custom_body": LINKS["dispatch_addr"], "hotline": HOTLINES["default"], "phone_num": "555-000-0007"},

    # --- BRANCH A (regional) ---
    "regional_template":                  {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},
    "regional_template_carrier_sales":    {"custom_body": LINKS["freight"], "hotline": HOTLINES["default"]},
    "regional_template_track_trace":      {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},
    "regional_template_expedite":         {"hotline": HOTLINES["expedite"]},

    # --- BRANCH B / BRANCH I ---
    "branch_b":                       {"phone_num": "555-000-0005", "hotline": HOTLINES["default"]},
    "branch_b_carrier_sales":         {"phone_num": "555-000-0005", "hotline": HOTLINES["chi_ds"], "custom_body": LINKS["freight"]},
    "branch_b_track_trace":           {"phone_num": "555-000-0005", "custom_body": LINKS["chi_track"], "hotline": HOTLINES["default"]},
    "branch_b_driver_services":       {"phone_num": "555-000-0005", "hotline": HOTLINES["chi_trace"], "custom_body": LINKS["macropoint"]},

    # --- BRANCH C ---
    "branch_c":                       {"phone_label": "Branch C Office", "phone_num": "555-000-0008", "show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "append_ext": False, "hotline": HOTLINES["default"]},
    "branch_c_ii":                    {"phone_label": "Branch C Office", "phone_num": "555-000-0009", "show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "append_ext": False, "hotline": HOTLINES["default"]},

    # --- BRANCH D ---
    "branch_d":                       {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},

    # --- BRANCH H ---
    "branch_h":                       {"phone_num": "555-000-0010", "hotline": "", "append_ext": False},

    # --- OFFICE TEMPLATE (/All Sites/Branch G-II) ---
    "office_template":               {"phone_label": "Team Line", "phone_num": "555-000-0004", "hotline": HOTLINES["phx"], "append_ext": False, "force_ltl": True, "direct_label": "Cell Phone"},
    "carrier_sales_template":        {"phone_label": "Team Line", "phone_num": "555-000-0004", "hotline": HOTLINES["phx"], "append_ext": False, "force_ltl": True, "direct_label": "Cell Phone", "custom_body": LINKS["esc_phx"]},
    "office_template_track_trace":   {"phone_label": "Team Line", "phone_num": "555-000-0004", "hotline": HOTLINES["phx"], "append_ext": False, "force_ltl": True, "direct_label": "Cell Phone"},

    # --- BRANCH F ---
    "branch_f":                      {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},
    "branch_f_carrier_sales":        {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "custom_body": LINKS["freight"], "hotline": HOTLINES["default"]},

    # --- BRANCH J ---
    "branch_j":                      {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},
    "branch_j_carrier_sales":        {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "custom_body": LINKS["freight"], "hotline": HOTLINES["default"]},
    "branch_j_track_trace":          {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},

    # --- BRANCH E ---
    "branch_e":                      {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},
    "branch_e_carrier_sales":        {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "custom_body": LINKS["freight"], "hotline": HOTLINES["default"]},
    "branch_e_track_trace":          {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},

    # --- INTERNATIONAL ---
    "international":                 {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},
    "international_carrier_sales":   {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "custom_body": LINKS["freight"], "hotline": HOTLINES["default"]},
    "international_track_trace":     {"show_reply_all": False, "show_logo_block": False, "custom_header": HQ_HEADER, "hotline": HOTLINES["default"]},
}


def set_html_template(
    template: str = "",
    fullname: str = "",
    title: str = "",
    location: str = "",
    email: str = "",
    ext: str = "",
    cell: str = "",
    direct: str = "",
    ltl: bool = False,
    about: str = "",
) -> str:
    """Build and return a minified HTML email signature string.

    Looks up *template* in CONFIGS, applies per-template overrides, then
    assembles the phone block, logo block, hotline, legal disclaimer, and
    custom header/body into a single ``<div>`` ready to push to the Gmail API.

    Args:
        template: Key from CONFIGS (e.g. ``"regional_template"``).  Defaults
                  to the ``"default"`` config when the key is not found.
        fullname: Employee's full display name (HTML-escaped before use).
        title: Job title (HTML-escaped before use).
        location: Office location string shown in the signature body.
        email: Employee's primary email address.
        ext: PBX extension number appended to the main phone line when allowed.
        cell: Cell phone number shown as a separate line when provided.
        direct: Direct-dial number shown as a separate line when provided.
        ltl: When True, append the LTL liability legal disclaimer.
        about: URL for the employee's "About me" profile link.

    Returns:
        Minified HTML string (newlines and excess whitespace removed).
    """

    # --- 3. PROCESSING LOGIC ---

    # Sanitize Inputs
    fullname = html.escape(fullname)
    title = html.escape(title)
    company_name = "Company Logistics, Inc."

    # Get Configuration (Default to "default" mapping above)
    config = CONFIGS.get(template, CONFIGS["default"]).copy()

    # Apply Config Overrides
    if "company_name" in config:
        company_name = config["company_name"]

    # --- 4. BUILD PHONE BLOCK ---
    p_style = '<p style="margin:0;font-size:9pt;font-family:Arial;line-height:1.25;">'
    phone_html = ""

    # Special Case: Billing
    if template == "corp_billing":
        phone_html = f"""{p_style}<b>Carrier Settlements:</b> 555-000-0001 option #4</p>{p_style}<b>Email:</b> <a href="mailto:paystatus@company.com" style="color:#1155cc;text-decoration:underline;font-size:9pt;">paystatus@company.com</a></p>"""
        if direct:
            phone_html += f'{p_style}<b>Direct Line:</b> {direct}</p>'
        if cell:
            phone_html += f'{p_style}<b>Cell Phone:</b> {cell}</p>'

    # Special Case: Templates that use Cell as the primary line
    elif config.get("force_cell_as_main"):
        label = config.get("phone_label", "Cell Phone")
        phone_html = f'{p_style}<b>{label}:</b> {cell}</p>'

    # Standard Case
    else:
        label = config.get("phone_label", "Phone")
        base_num = config.get("phone_num", "555-000-0001")

        # Append ext to base number only if allowed and not already present
        if config.get("append_ext", True) and ext and "ext." not in base_num:
            base_num += f" ext. {ext}"

        phone_html = f'{p_style}<b>{label}:</b> {base_num}</p>'
        direct_label = config.get("direct_label", "Direct Line")
        if direct:
            phone_html += f'{p_style}<b>{direct_label}:</b> {direct}</p>'
        if cell:
            phone_html += f'{p_style}<b>Cell Phone:</b> {cell}</p>'

    # --- 5. BUILD REMAINING BLOCKS ---

    # Hotline
    hotline_html = ""
    if config.get("hotline"):
        hotline_html = f"""<p style="margin:0; font-size:9pt; line-height:1.25; padding-top:5pt; padding-bottom:5pt; color:black;"><span style="font-size:9pt;">{config['hotline']}</span></p>"""

    # About Me Link
    about_html = f'{p_style}<a href="{about}" style="color:#1155cc;text-decoration:underline;font-size:9pt;">About me</a></p>' if about else ""

    # Reply All Warning
    reply_all_html = ""
    if config.get("show_reply_all", True):
        reply_all_html = '<p style="padding-bottom:2pt;font-weight:700;font-size:9pt;font-family:Arial;">Kindly REPLY ALL in every email correspondence to maintain visibility.</p>'

    # Logo Selection
    current_logo = URLS["logo_transport"] if config.get("use_transport_logo") else URLS["logo_circle"]

    # Logo Block (Social Media Table)
    logo_block = ""
    if config.get("show_logo_block", True):
        logo_block = f"""
        <table border="0" cellpadding="0" cellspacing="0" style="margin-top:5px;">
            <tr>
                <td valign="bottom" style="padding-right:8px;">
                    <a href="https://company.com/" title="Company Logo">
                        <img src="{current_logo}" width="300" height="78" alt="Company Logistics" style="display:block; border:0;">
                    </a>
                </td>
                <td valign="bottom">
                    <table border="0" cellpadding="0" cellspacing="0">
                        <tr>
                            <td align="center" style="padding-bottom:2px;">
                                <div style="line-height:0; font-size:0;">
                                    <a href="https://www.facebook.com/company" style="display:inline-block; margin-right:2px; text-decoration:none;"><img src="{URLS['icon_fb']}" width="24" height="25" alt="FB" style="display:block; border:0;"></a>
                                    <a href="https://www.instagram.com/company/" style="display:inline-block; margin-right:2px; text-decoration:none;"><img src="{URLS['icon_ig']}" width="24" height="25" alt="IG" style="display:block; border:0;"></a>
                                    <a href="https://www.linkedin.com/company/company/" style="display:inline-block; margin-right:2px; text-decoration:none;"><img src="{URLS['icon_in']}" width="24" height="25" alt="IN" style="display:block; border:0;"></a>
                                    <a href="https://twitter.com/company" style="display:inline-block; text-decoration:none;"><img src="{URLS['icon_tw']}" width="24" height="25" alt="TW" style="display:block; border:0;"></a>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td align="center">
                                <a href="https://company.com/"><img src="{URLS['icon_top100']}" width="100" height="44" alt="Top 100" style="display:block; border:0;"></a>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>"""

    # LTL Legal Block
    ltl_block = LTL_LEGAL if (ltl or config.get("force_ltl", False)) else ""

    # Custom Header & Body
    custom_header = config.get("custom_header", "")
    custom_body = config.get("custom_body", "")

    # --- 6. FINAL HTML ASSEMBLY ---

    final_html = f"""
    <div style="font-family:Arial, Helvetica, sans-serif; background-color:#FFFFFF; max-width:500px; padding:5pt;">
        {custom_header}
        {reply_all_html}

        <h3 style="font-size:2pt;font-family:Arial; margin-bottom:5px;">
            <span style="font-size:10pt; color:#0267a2; font-weight:700;">{fullname} </span>
            <span style="font-size:10pt; color:black; font-weight:700;"> | </span>
            <span style="color:#0267a2; font-weight:700; font-size:10pt;"> {title} </span>
        </h3>

        <p style="margin:0; font-size:10pt; font-weight:700; line-height:1.25; padding-bottom:3pt; color:black;"> {company_name} </p>
        <p style="margin:0; font-size:9pt; line-height:1.25; color:black;"><b>Location:</b> {location}</p>
        <p style="margin:0; font-size:9pt; line-height:1.25; color:black;">{email} &nbsp;</p>

        {phone_html}
        {about_html}
        {hotline_html}
        {custom_body}
        {logo_block}
        {ltl_block}
    </div>
    """

    # Return minified HTML string (removing newlines and tabs)
    return final_html.replace("\n", "").replace("\t", "").replace("    ", "")
