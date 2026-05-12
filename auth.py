#!/usr/bin/env python3
"""OAuth flow for Google Search Console API. Run once to generate token.json."""

import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"


def main():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)

    # Run local server flow; opens browser or prints URL for manual auth
    creds = flow.run_local_server(port=8080, open_browser=False)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"\nCredentials saved to {TOKEN_FILE}")

    # Quick test: list verified sites
    service = build("searchconsole", "v1", credentials=creds)
    sites = service.sites().list().execute()
    print("\nVerified Search Console properties:")
    for site in sites.get("siteEntry", []):
        print(f"  {site['siteUrl']}  ({site['permissionLevel']})")


if __name__ == "__main__":
    main()
