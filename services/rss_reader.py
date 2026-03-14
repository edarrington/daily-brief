import re
import feedparser
import logging
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class FeedItem:
    title: str
    link: str
    summary: str
    source: str


FEEDS = {
    "ai": [
        ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"),
        ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    ],
    "cybersecurity": [
        ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
        ("Bleeping Computer", "https://www.bleepingcomputer.com/feed/"),
        ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ],
    "world": [
        ("BBC World News", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Reuters", "https://feeds.reuters.com/reuters/worldNews"),
        ("NYT World", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
    ],
}


def fetch_category(category: str, max_per_feed: int = 2) -> List[FeedItem]:
    items = []
    for source_name, url in FEEDS[category]:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_feed]:
                summary = getattr(entry, "summary", "") or ""
                summary = re.sub(r"<[^>]+>", "", summary)[:300].strip()
                items.append(
                    FeedItem(
                        title=entry.get("title", "No title"),
                        link=entry.get("link", "#"),
                        summary=summary,
                        source=source_name,
                    )
                )
        except Exception as e:
            logger.warning("Failed to fetch feed %s: %s", url, e)
    return items[:5]
