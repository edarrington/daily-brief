import httpx
import datetime
import logging

logger = logging.getLogger(__name__)

SUBSCRIPTION_ID = "1b98522b-bc4a-4790-a8e0-66c1aa8a85f0"
MANAGED_IDENTITY_CLIENT_ID = "6703dd26-c811-494a-b249-3fbb34b7cc84"


def _get_token() -> str:
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


def fetch_costs() -> list[dict]:
    """Returns list of {resource_group, cost, currency} sorted by cost desc."""
    token = _get_token()
    today = datetime.date.today()
    start = today.replace(day=1).isoformat() + "T00:00:00Z"
    end = today.isoformat() + "T23:59:59Z"

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
