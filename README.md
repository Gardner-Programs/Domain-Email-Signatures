# Domain Email Signatures

A suite of scripts for managing Google Workspace email signatures at scale across an entire domain. Handles bulk application, template management, auditing, and field-level updates using the Gmail API and Google Admin SDK.

## Scripts

| Script | Purpose |
|---|---|
| `domain_signature_change.py` | Core script: fetches all domain users via Admin SDK, assigns and applies HTML signature templates based on org unit or department |
| `scripts/email_templates.py` | Defines all HTML signature templates with dynamic field injection |
| `scripts/google_api.py` | Shared Google API authentication and service builders |
| `scripts/all_user_download.py` | Downloads all user records from the Google Admin SDK |
| `scripts/get_all_signatures.py` | Reads and reports current signature for every user |
| `scripts/update_sig_info.py` | Bulk-updates signature info (name, title, phone) for a list of users |
| `scripts/update_sig_field.py` | Updates a single field across a targeted list of users |
| `scripts/update_single.py` | Updates the signature for one specific user |
| `scripts/sig_info_report.py` | Generates a report of signature data across the domain |
| `scripts/audit_template.py` | Audits which users have a specific template applied and flags mismatches |
| `scripts/verify_template.py` | Verifies a list of users have the correct template and field values |
| `scripts/preview_template.py` | Renders a template preview for a given user without pushing it |
| `scripts/check_team_template.py` | Checks that all members of a group have a consistent template |
| `scripts/push_phone_updates.py` | Pushes phone number updates to a targeted list of users |
| `scripts/lookup_orgunits.py` | Looks up the org unit path for users in a given region |

## Setup

### Prerequisites
- Google Cloud project with Gmail API and Admin SDK enabled
- Service account with domain-wide delegation
- Required OAuth scopes:
  - `https://www.googleapis.com/auth/admin.directory.user`
  - `https://www.googleapis.com/auth/gmail.settings.basic`
  - `https://www.googleapis.com/auth/gmail.settings.sharing`

### Configuration
Replace the placeholder paths in the scripts with your actual credentials:
```python
service_account_json_file_path = '/path/to/your/service-account-key.json'
admin_email = 'admin@yourdomain.com'
DOMAIN = 'yourdomain.com'
```

## How It Works

1. **Auth** — A service account with domain-wide delegation impersonates the admin user to call the Admin SDK, then impersonates each individual user to call the Gmail API on their behalf.
2. **Pagination** — The Admin SDK returns up to 500 users per page; the scripts loop through all pages using `nextPageToken`.
3. **Template selection** — Users are assigned templates based on their org unit, department, or a manual override list.
4. **Application** — Each user's signature is set via `users.settings.sendAs.patch` targeting their primary send-as address.
