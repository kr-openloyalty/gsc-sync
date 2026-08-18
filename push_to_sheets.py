"""Push canonicalization report CSV to a new Google Sheet."""
import csv
import json
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

TOKEN_FILE = "/home/user/gsc-sync/sheets_token.json"
SECRET_FILE = "/home/user/gsc-sync/client_secret.json"
CSV_FILE = "/tmp/canonicalization_full_report.csv"


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_FILE, SCOPES)
            auth_url, _ = flow.authorization_url(prompt="consent")
            print("\n\nVisit this URL to authorize Sheets access:")
            print(auth_url)
            print()
            code = input("Paste the authorization code here: ").strip()
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def main():
    creds = get_credentials()

    sheets = build("sheets", "v4", credentials=creds)

    # Create new spreadsheet
    spreadsheet = sheets.spreadsheets().create(body={
        "properties": {"title": "openloyalty.io — Canonicalization Audit 2026-08-18"},
        "sheets": [{"properties": {"title": "Full Audit"}}],
    }).execute()

    sid = spreadsheet["spreadsheetId"]
    print(f"Created: https://docs.google.com/spreadsheets/d/{sid}/edit")

    # Read CSV and build rows
    rows = []
    with open(CSV_FILE, newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    print(f"Uploading {len(rows)} rows...")

    # Batch update in chunks of 500
    chunk_size = 500
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        sheets.spreadsheets().values().append(
            spreadsheetId=sid,
            range="Full Audit!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": chunk},
        ).execute()
        print(f"  Uploaded rows {i+1}–{min(i+chunk_size, len(rows))}")

    # Bold header row
    sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={
        "requests": [{
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold",
            }
        }, {
            "updateSheetProperties": {
                "properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 1}},
                "fields": "gridProperties.frozenRowCount",
            }
        }]
    }).execute()

    print(f"\nDone! https://docs.google.com/spreadsheets/d/{sid}/edit")


if __name__ == "__main__":
    main()
