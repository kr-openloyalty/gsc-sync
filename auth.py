#!/usr/bin/env python3
"""OAuth flow for Google Search Console API. Run once to generate token.json.

Usage:
  python3 auth.py              → prints the authorization URL
  python3 auth.py <redirect>   → completes token exchange with the redirect URL
"""

import json
import os
import sys
import warnings
from urllib.parse import urlparse, parse_qs

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
STATE_FILE = ".auth_state.json"
REDIRECT_URI = "http://localhost:8080"


def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    session = AuthorizedSession(creds)
    session.verify = False
    return session


def main():
    if len(sys.argv) < 2:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRET_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )
        auth_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
        )

        with open(STATE_FILE, "w") as f:
            json.dump({"code_verifier": flow.code_verifier, "state": state}, f)

        print("Open this URL in your browser:\n")
        print(auth_url)
        print("\nAfter approving, copy the full redirect URL from your browser")
        print("(starts with http://localhost:8080/?code=...) and run:")
        print(f"\n  python3 auth.py '<redirect_url>'\n")
        return

    # --- Step 2: exchange code for token ---
    redirected_url = sys.argv[1]
    parsed = urlparse(redirected_url)
    code = parse_qs(parsed.query).get("code", [None])[0]
    if not code:
        print("ERROR: Could not find 'code' in the URL.")
        sys.exit(1)

    if not os.path.exists(STATE_FILE):
        print(f"ERROR: {STATE_FILE} not found. Run 'python3 auth.py' first.")
        sys.exit(1)

    with open(STATE_FILE) as f:
        saved = json.load(f)

    import os
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=saved["state"],
    )
    flow.code_verifier = saved["code_verifier"]
    flow.fetch_token(code=code)
    creds = flow.credentials

    os.remove(STATE_FILE)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())
    print(f"Credentials saved to {TOKEN_FILE}")

    # Quick test: list verified properties
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()
    resp = session.get("https://www.googleapis.com/webmasters/v3/sites")
    resp.raise_for_status()
    print("\nVerified Search Console properties:")
    for site in resp.json().get("siteEntry", []):
        print(f"  {site['siteUrl']}  ({site['permissionLevel']})")


if __name__ == "__main__":
    main()
