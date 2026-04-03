import httpx
import datetime
import logging
import os

logger = logging.getLogger(__name__)

SUBSCRIPTION_ID = "1b98522b-bc4a-4790-a8e0-66c1aa8a85f0"
MANAGED_IDENTITY_CLIENT_ID = "6703dd26-c811-494a-b249-3fbb34b7cc84"


def _get_token() -> str:
    identity_endpoint = os.environ.get("IDENTITY_ENDPOINT")
    identity_header = os.environ.get("IDENTITY_HEADER")

    if identity_endpoint and identity_header:
        # Azure Container Apps managed identity endpoint
        resp = httpx.get(
            identity_endpoint,
            params={
                "api-version": "2019-08-01",
                "resource": "https://management.azure.com/",
                "client_id": MANAGED_IDENTITY_CLIENT_ID,
            },
            headers={"X-IDENTITY-HEADER": identity_header},
            timeout=10,
        )
    else:
        # Standard IMDS fallback
        resp = httpx.get(
            "http://169.254.169.254/metadata/identity/oauth2/token",
            params={
                "api-version": "2018-02-01",
                "resource": "https://management.azure.com/",
                "client_id": MANAGED_IDENTITY_CLIENT_ID,
            },
            headers={"Metadata": "true"},
            timeout=10,
        )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_costs(last_month: bool = False) -> list[dict]:
    """Returns list of {resource_group, cost, currency} sorted by cost desc."""
    token = _get_token()
    today = datetime.date.today()
    if last_month:
        first_of_this_month = today.replace(day=1)
        end_date = first_of_this_month - datetime.timedelta(days=1)
        start_date = end_date.replace(day=1)
    else:
        start_date = today.replace(day=1)
        end_date = today
    start = start_date.isoformat() + "T00:00:00Z"
    end = end_date.isoformat() + "T23:59:59Z"

    payload = {
        "type": "Usage",
        "timeframe": "Custom",
        "timePeriod": {"from": start, "to": end},
        "dataset": {
            "granularity": "None",
            "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
            "grouping": [{"type": "Dimension", "name": "ResourceGroupName"}],
        },
    }

    resp = httpx.post(
        f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/providers/Microsoft.CostManagement/query",
        params={"api-version": "2023-11-01"},
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    rows = data.get("properties", {}).get("rows", [])
    results = [
        {"resource_group": row[1], "cost": row[0], "currency": row[2]}
        for row in rows
    ]
    results.sort(key=lambda x: x["cost"], reverse=True)
    return results
