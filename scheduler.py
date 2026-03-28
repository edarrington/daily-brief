from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import datetime
import logging
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from services.brief_builder import build_brief
from services.azure_costs import fetch_costs
from services.mailer import send_email
from config import TO_EMAIL

logger = logging.getLogger(__name__)
PT = pytz.timezone("America/Los_Angeles")

_jinja = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))


def send_morning_brief():
    logger.info("Sending morning brief...")
    subject, html = build_brief("Morning")
    send_email(TO_EMAIL, subject, html)


def send_evening_brief():
    logger.info("Sending evening brief...")
    subject, html = build_brief("Evening")
    send_email(TO_EMAIL, subject, html)


def send_azure_cost_brief():
    logger.info("Sending Azure cost report...")
    try:
        rows = fetch_costs()
    except Exception:
        logger.exception("Failed to fetch Azure costs")
        return

    total = sum(r["cost"] for r in rows)
    currency = rows[0]["currency"] if rows else "USD"
    today = datetime.date.today()
    date_str = today.strftime("%A, %B %d, %Y")
    month_str = today.strftime("%B %Y")

    template = _jinja.get_template("azure_cost_email.html")
    html = template.render(
        date=date_str,
        month=month_str,
        total=total,
        currency=currency,
        rows=rows,
    )
    subject = f"Azure Cost Report — {month_str} (${total:.2f} so far)"
    send_email(TO_EMAIL, subject, html)


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=PT)
    scheduler.add_job(send_morning_brief, CronTrigger(hour=7, minute=0, timezone=PT))
    scheduler.add_job(send_evening_brief, CronTrigger(hour=18, minute=0, timezone=PT))
    scheduler.add_job(send_azure_cost_brief, CronTrigger(day_of_week='mon', hour=6, minute=0, timezone=PT))
    return scheduler
