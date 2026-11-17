#!/usr/bin/env python3
"""Watch Microsoft 365 service health and print active incidents.

Detection should not depend on users opening tickets. This script reads
Microsoft Graph service health issues (GET /admin/serviceAnnouncement/issues)
and prints unresolved incidents, newest first, so you can feed them into a
SIEM, Tines, or a pager.

Live mode needs an Entra ID app registration with the application permission
ServiceHealth.Read.All, and these environment variables:
    M365_TENANT_ID, M365_CLIENT_ID, M365_CLIENT_SECRET
Install: pip install msal requests

Offline demo mode needs nothing:
    python3 tools/m365_health_watch.py --sample tools/sample_issues.json

Exit codes: 0 = no active incidents, 1 = at least one active incident,
2 = configuration or API error.
"""

import argparse
import json
import os
import sys

GRAPH_URL = "https://graph.microsoft.com/v1.0/admin/serviceAnnouncement/issues"


def fetch_live():
    """Return the list of issues from Microsoft Graph, following paging."""
    try:
        import msal
        import requests
    except ImportError:
        sys.exit("error: live mode needs 'pip install msal requests'")

    try:
        tenant = os.environ["M365_TENANT_ID"]
        client_id = os.environ["M365_CLIENT_ID"]
        secret = os.environ["M365_CLIENT_SECRET"]
    except KeyError as missing:
        print(f"error: missing environment variable {missing}", file=sys.stderr)
        sys.exit(2)

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=secret,
    )
    token = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" not in token:
        print(f"error: token request failed: {token.get('error_description')}",
              file=sys.stderr)
        sys.exit(2)

    headers = {"Authorization": f"Bearer {token['access_token']}"}
    params = {"$filter": "isResolved eq false"}
    issues, url = [], GRAPH_URL
    while url:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"error: Graph returned {resp.status_code}: {resp.text[:200]}",
                  file=sys.stderr)
            sys.exit(2)
        body = resp.json()
        issues.extend(body.get("value", []))
        url, params = body.get("@odata.nextLink"), None
    return issues


def load_sample(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("value", [])


def active_incidents(issues):
    """Unresolved issues classified as incidents, newest first."""
    found = [
        i for i in issues
        if not i.get("isResolved") and i.get("classification") == "incident"
    ]
    return sorted(found, key=lambda i: i.get("startDateTime", ""), reverse=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", help="read issues from a local JSON file instead of Graph")
    parser.add_argument("--json", action="store_true", help="print JSON lines for SIEM ingestion")
    args = parser.parse_args(argv)

    issues = load_sample(args.sample) if args.sample else fetch_live()
    incidents = active_incidents(issues)

    for i in incidents:
        if args.json:
            print(json.dumps({k: i.get(k) for k in (
                "id", "service", "title", "status", "startDateTime", "impactDescription")}))
        else:
            print(f"[{i.get('startDateTime', '?')}] {i.get('id')} "
                  f"{i.get('service')}: {i.get('title')} ({i.get('status')})")

    if not incidents and not args.json:
        print("No active incidents.")
    return 1 if incidents else 0


if __name__ == "__main__":
    sys.exit(main())
