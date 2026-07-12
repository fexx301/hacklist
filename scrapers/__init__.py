import os

from .devpost     import DevpostScraper
from .mlh         import MLHScraper
from .devfolio    import DevfolioScraper
from .unstop      import UnstopScraper
from .hackerearth import HackerEarthScraper
from .dorahacks   import DoraHacksScraper
from .kaggle      import KaggleScraper
from .twitter     import TwitterScraper


def get_all_scrapers():
    scrapers = [
        DevpostScraper(),
        MLHScraper(),
        DevfolioScraper(),
        UnstopScraper(),
        HackerEarthScraper(),
        DoraHacksScraper(),
    ]
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        scrapers.append(KaggleScraper())
    if os.getenv("TWITTER_USERNAME"):
        scrapers.append(TwitterScraper())
    return scrapers
