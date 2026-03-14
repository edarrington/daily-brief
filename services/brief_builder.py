import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from services.rss_reader import fetch_category

_env = Environment(loader=FileSystemLoader(Path(__file__).parent.parent / "templates"))


def build_brief(period: str) -> tuple[str, str]:
    """Returns (subject, html_body). period = 'Morning' | 'Evening'"""
    ai_items = fetch_category("ai")
    cyber_items = fetch_category("cybersecurity")
    world_items = fetch_category("world")

    today = datetime.date.today().strftime("%A, %B %d, %Y")
    template = _env.get_template("brief_email.html")
    html = template.render(
        period=period,
        date=today,
        ai_items=ai_items,
        cyber_items=cyber_items,
        world_items=world_items,
    )
    subject = f"{period} Brief — {today}"
    return subject, html
