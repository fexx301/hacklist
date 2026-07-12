import os

from .devpost    import DevpostScraper
from .mlh        import MLHScraper
from .devfolio   import DevfolioScraper
from .unstop     import UnstopScraper
from .hackerearth import HackerEarthScraper
from .twitter    import TwitterScraper


def get_all_scrapers():
    scrapers = [
        DevpostScraper(),
        MLHScraper(),
        DevfolioScraper(),
        UnstopScraper(),
        HackerEarthScraper(),
    ]
    if os.getenv("TWITTER_USERNAME"):
        scrapers.append(TwitterScraper())
    return scrapers
