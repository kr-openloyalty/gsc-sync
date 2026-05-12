#!/usr/bin/env python3
"""OAuth flow for Google Search Console API. Run once to generate token.json."""

import json
import sys
from urllib.parse import urlparse, parse_qs
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
REDIRECT_URI = "http://localhost:8080/"


def main():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")

    print("=" * 60)
    print("1. Open this URL in your browser:")
    print()
    print(auth_url)
    print()
    print("2. Sign in and grant access.")
    print("3. You'll be redirected to localhost:8080 (which will fail to load).")
    print("4. Copy the FULL URL from your browser's address bar and paste it below.")
    print("=" * 60)

    redirected_url = input("\nPaste the full redirect URL here: ").strip()

    parsed = urlparse(redirected_url)
    code = parse_qs(parsed.query).get("code", [None])[0]
    if not code:
        print("ERROR: Could not find 'code' in the URL. Please try again.")
        sys.exit(1)

    flow.fetch_token(code=code)
    creds = flow.credentials

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
