import asyncio
import html
import logging
import os
import re

from .base import BaseScraper

log = logging.getLogger(__name__)

QUERIES = [
    "online hackathon registration open 2026 -is:retweet",
    "virtual hackathon apply prize 2026 -is:retweet",
]


class TwitterScraper(BaseScraper):
    name = "twitter"

    def scrape(self) -> list[dict]:
        return asyncio.run(self._scrape())

    async def _scrape(self) -> list[dict]:
        try:
            from twscrape import API, gather
        except ImportError:
            return []

        auth_token = os.getenv("TWITTER_AUTH_TOKEN", "")
        ct0        = os.getenv("TWITTER_CT0", "")
        username   = os.getenv("TWITTER_USERNAME", "")
        password   = os.getenv("TWITTER_PASSWORD", "")
        email      = os.getenv("TWITTER_EMAIL", "")

        if not auth_token or not ct0:
            return []

        api     = API()
        cookies = f"auth_token={auth_token}; ct0={ct0}"
        # Re-register the account each run so refreshed cookies in .env
        # replace the ones cached in accounts.db (expired cookies would
        # otherwise be reused forever).
        try:
            await api.pool.delete_accounts(username)
        except Exception:
            pass
        try:
            await api.pool.add_account(
                username=username, password=password,
                email=email, email_password="",
                cookies=cookies,
            )
        except Exception as exc:
            log.warning("twitter: could not register account: %s", exc)
            return []

        hackathons = []
        seen: set[str] = set()

        for query in QUERIES:
            try:
                from twscrape import gather
                tweets = await gather(api.search(query, limit=30))
            except Exception:
                continue

            for tweet in tweets:
                # Prefer expanded external links from tweet.links
                external = [
                    lnk.url for lnk in (tweet.links or [])
                    if lnk.url
                    and "twitter.com" not in lnk.url
                    and "x.com" not in lnk.url
                ]

                # Fallback: follow t.co redirect in raw text
                if not external:
                    tco = re.search(r"https://t\.co/\S+", tweet.rawContent)
                    if tco:
                        resolved = self._resolve(tco.group(0).rstrip(".,)"))
                        if "twitter.com" not in resolved and "x.com" not in resolved and "t.co" not in resolved:
                            external = [resolved]

                # A tweet without a link to an actual hackathon page is noise, skip it
                if not external:
                    continue
                url = external[0]

                if url in seen:
                    continue
                seen.add(url)

                # Clean up title: strip bare t.co links from display text
                text  = html.unescape(tweet.rawContent)
                title = re.sub(r"https://t\.co/\S+", "", text).strip()
                title = re.sub(r"\s+", " ", title)
                if not title:
                    title = url[:100]

                hackathons.append(self.make_hackathon(
                    title=title[:100],
                    url=url,
                    description=text,
                ))

        return hackathons

    def _resolve(self, tco_url: str) -> str:
        try:
            r = self.session.head(tco_url, allow_redirects=True, timeout=5)
            return r.url
        except Exception:
            return tco_url
