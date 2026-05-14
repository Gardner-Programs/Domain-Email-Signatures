import os
from authenticator import admin_directory_v1_api
import pandas
# --- Constants ---
DOMAIN = "company.com"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_all_active_users():
    """Fetches ALL active users into a list."""
    service = admin_directory_v1_api()
    all_users = []
    page_token = None

    print("Fetching full user directory...")

    # Query: Not suspended
    query = "isSuspended=false"

    while True:
        try:
            result = service.users().list(
                domain=DOMAIN,
                maxResults=500,
                orderBy="email",
                projection="full",
                query=query,
                pageToken=page_token
            ).execute()
        except Exception as e:
            print(f"Critical API Error fetching users: {e}")
            break

        users = result.get("users", [])

        for user in users:
            # Filter out non-user accounts locally
            if user.get("orgUnitPath") != "/Non-User Accounts":
                all_users.append(user)

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    print(f"Directory fetch complete. Found {len(all_users)} eligible users.")
    return all_users

pandas.DataFrame(get_all_active_users()).to_csv(os.path.join(OUTPUT_DIR, "all_active_users.csv"), index=False)
