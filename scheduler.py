from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging
from services.brief_builder import build_brief
from services.mailer import send_email
from config import TO_EMAIL

logger = logging.getLogger(__name__)
PT = pytz.timezone("America/Los_Angeles")


def send_morning_brief():
    logger.info("Sending morning brief...")
    subject, html = build_brief("Morning")
    send_email(TO_EMAIL, subject, html)


def send_evening_brief():
    logger.info("Sending evening brief...")
    subject, html = build_brief("Evening")
    send_email(TO_EMAIL, subject, html)


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=PT)
    scheduler.add_job(send_morning_brief, CronTrigger(hour=7, minute=0, timezone=PT))
    scheduler.add_job(send_evening_brief, CronTrigger(hour=18, minute=0, timezone=PT))
    return scheduler
