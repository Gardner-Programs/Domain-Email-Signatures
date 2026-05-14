# Domain Email Signatures

A suite of Python scripts for managing Google Workspace email signatures at scale across an entire domain. Handles bulk application, template management, auditing, and field-level updates using the Gmail API and Google Admin SDK.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/email_templates.py` | Defines all HTML signature templates with dynamic field injection |
| `scripts/authenticator.py` | Google service account auth and API service builders |
| `scripts/google_api.py` | Shared helpers: bulk signature push, error reporting, user fetching |
| `scripts/all_user_download.py` | Downloads all user records from the Admin SDK to CSV |
| `scripts/get_all_signatures.py` | Exports every active user's live Gmail signature HTML to a shared Drive folder |
| `scripts/update_sig_info.py` | Patches multiple Signature_Info fields for a roster of users (dry-run by default) |
| `scripts/update_sig_field.py` | Bulk-sets a single field to the same value across a targeted user list |
| `scripts/update_single.py` | Updates the live signature for one user; generates a preview image |
| `scripts/sig_info_report.py` | Exports the Signature_Info custom schema for all users to CSV |
| `scripts/audit_template.py` | Audits which users have a specific template applied and flags mismatches |
| `scripts/verify_template.py` | Verifies a roster of users have the correct template and field values |
| `scripts/preview_template.py` | Renders a JPG preview for a roster of users without pushing to Gmail |
| `scripts/check_team_template.py` | Checks that all members of a group have a consistent template |
| `scripts/push_phone_updates.py` | Pushes phone number updates to a targeted user list |
| `scripts/lookup_orgunits.py` | Lists the org unit path for every user in the domain |

## Setup

### Prerequisites

- Python 3.9+
- Google Cloud project with Gmail API and Admin SDK enabled
- Service account with domain-wide delegation and the following scopes:
  - `https://www.googleapis.com/auth/admin.directory.user`
  - `https://www.googleapis.com/auth/admin.directory.userschema`
  - `https://www.googleapis.com/auth/gmail.settings.basic`
  - `https://www.googleapis.com/auth/gmail.settings.sharing`
  - `https://www.googleapis.com/auth/drive` (for `get_all_signatures.py`)
- `wkhtmltopdf` installed and on PATH (for `update_single.py` preview images)

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Place your service account key JSON in a `Keys/` folder (or set `KEY_PATH` in `.env` to its absolute path). The `authenticator.py` module searches several common locations and also respects `KEY_PATH` as an override.

## How It Works

1. **Auth** — A service account with domain-wide delegation impersonates the admin user to call the Admin SDK, then impersonates each individual user to call the Gmail API on their behalf.
2. **Custom schema** — Signature fields (title, location, extension, direct line, template key) are stored in a `Signature_Info` custom schema on each user's Google Directory profile. This makes them queryable and auditable without touching Gmail directly.
3. **Pagination** — The Admin SDK returns up to 500 users per page; scripts loop through all pages via `nextPageToken`.
4. **Template selection** — `email_templates.py` maps a `Template` key (e.g. `branch_a`, `corp_hr`) to a fully rendered HTML string. The key is stored in each user's `Signature_Info` schema and read at push time.
5. **Application** — Each user's signature is set via `users.settings.sendAs.patch` targeting their primary send-as address.
6. **Dry-run safety** — `update_sig_info.py` and `update_sig_field.py` default to dry-run mode and print diffs before writing. Pass `--apply` to commit changes.
