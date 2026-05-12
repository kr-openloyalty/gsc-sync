#!/usr/bin/env python3
"""OAuth flow for Google Search Console API. Run once to generate token.json.

Usage:
  python3 auth.py              → prints the authorization URL
  python3 auth.py <redirect>   → completes token exchange with the redirect URL
"""

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

    if len(sys.argv) < 2:
        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
        print("Open this URL in your browser:\n")
        print(auth_url)
        print("\nAfter approving, copy the full redirect URL from your browser")
        print("(starts with http://localhost:8080/?code=...) and run:")
        print(f"\n  python3 auth.py '<redirect_url>'\n")
        return

    redirected_url = sys.argv[1]
    parsed = urlparse(redirected_url)
    code = parse_qs(parsed.query).get("code", [None])[0]
    if not code:
        print("ERROR: Could not find 'code' in the URL.")
        sys.exit(1)

    flow.fetch_token(code=code)
    creds = flow.credentials

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"Credentials saved to {TOKEN_FILE}")

    service = build("searchconsole", "v1", credentials=creds)
    sites = service.sites().list().execute()
    print("\nVerified Search Console properties:")
    for site in sites.get("siteEntry", []):
        print(f"  {site['siteUrl']}  ({site['permissionLevel']})")


if __name__ == "__main__":
    main()
