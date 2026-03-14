import httpx
import msal
import logging
from config import GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, GRAPH_TENANT_ID, FROM_EMAIL

logger = logging.getLogger(__name__)


def _get_token() -> str:
    app = msal.ConfidentialClientApplication(
        GRAPH_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{GRAPH_TENANT_ID}",
        client_credential=GRAPH_CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in result:
        raise RuntimeError(f"Failed to acquire token: {result.get('error_description')}")
    return result["access_token"]


def send_email(to: str, subject: str, html_body: str) -> None:
    token = _get_token()
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": to}}],
        }
    }
    with httpx.Client() as client:
        resp = client.post(
            f"https://graph.microsoft.com/v1.0/users/{FROM_EMAIL}/sendMail",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
    logger.info("Email sent to %s: %s", to, subject)
