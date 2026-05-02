"""
LinkedIn Jobs scraper.
Uses Playwright for JS rendering. Extracts job cards from LinkedIn's public job search.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from models.job import JobPosting, JobQuery
from scrapers.base import BaseScraper
from utils.dedup import generate_job_id

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    name = "linkedin"
    base_url = "https://www.linkedin.com/jobs/search/"
    requires_playwright = True

    # Source logo (LinkedIn favicon)
    SOURCE_LOGO = "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png"

    def build_search_url(self, page_num: int = 0) -> str:
        """Build LinkedIn job search URL with query parameters."""
        params = {
            "keywords": self.query.designation,
            "location": self.query.location,
            "sortBy": "DD",  # Sort by date
            "position": 1,
            "pageNum": page_num,
            "start": page_num * 25,
        }
        if self.query.remote_ok:
            params["f_WT"] = "2"  # Remote filter

        query_string = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
        return f"{self.base_url}?{query_string}"

    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Fetch LinkedIn search results page using Playwright."""
        url = self.build_search_url(page_num)
        logger.info(f"[{self.name}] Fetching: {url}")

        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for job cards to load
            try:
                await self._page.wait_for_selector(
                    ".jobs-search__results-list li, .base-card",
                    timeout=10000
                )
            except Exception:
                logger.warning(f"[{self.name}] Job cards selector timeout, trying alternative")

            # Scroll down to trigger lazy loading
            for _ in range(3):
                await self._page.evaluate("window.scrollBy(0, 800)")
                await self._page.wait_for_timeout(1000)

            html = await self._page.content()
            return html

        except Exception as e:
            logger.error(f"[{self.name}] Fetch error: {e}")
            return None

    async def parse_jobs(self, html: str) -> List[JobPosting]:
        """Parse LinkedIn search results HTML into JobPosting objects."""
        jobs = []
        soup = BeautifulSoup(html, "lxml")

        # LinkedIn uses base-card class for public job listings
        cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))
        if not cards:
            # Try alternative selector for authenticated/different layout
            cards = soup.find_all("li", class_=re.compile(r"jobs-search-results__list-item"))

        logger.debug(f"[{self.name}] Found {len(cards)} raw cards")

        for card in cards:
            try:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] Failed to parse card: {e}")
                continue

        return jobs

    def _parse_card(self, card) -> Optional[JobPosting]:
        """Parse a single LinkedIn job card into a JobPosting."""
        # Title
        title_el = card.find("h3", class_=re.compile(r"base-search-card__title")) or \
                   card.find("a", class_=re.compile(r"job-card-list__title"))
        if not title_el:
            title_el = card.find("h3") or card.find("span", class_=re.compile(r"title"))
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None

        # Company
        company_el = card.find("h4", class_=re.compile(r"base-search-card__subtitle")) or \
                     card.find("a", class_=re.compile(r"hidden-nested-link"))
        company = company_el.get_text(strip=True) if company_el else "Unknown Company"

        # Location
        location_el = card.find("span", class_=re.compile(r"job-search-card__location"))
        location = location_el.get_text(strip=True) if location_el else self.query.location

        # Job URL
        link_el = card.find("a", href=re.compile(r"/jobs/view/|/jobs/"))
        if link_el and link_el.get("href"):
            job_url = link_el["href"]
            if not job_url.startswith("http"):
                job_url = f"https://www.linkedin.com{job_url}"
            # Clean tracking params
            job_url = job_url.split("?")[0]
        else:
            return None  # Skip if no URL

        # Posted date
        time_el = card.find("time")
        posted_date = None
        if time_el and time_el.get("datetime"):
            try:
                posted_date = datetime.fromisoformat(time_el["datetime"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        if not posted_date:
            date_text_el = card.find("span", class_=re.compile(r"listed-date|date"))
            if date_text_el:
                posted_date = self._parse_relative_date(date_text_el.get_text(strip=True))

        # Check for remote
        is_remote = "remote" in location.lower() if location else self.query.remote_ok

        # Generate deterministic ID
        job_id = generate_job_id(title, company, location)

        return JobPosting(
            id=job_id,
            title=title,
            company=company,
            location=location,
            posted_date=posted_date,
            apply_url=job_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            is_remote=is_remote,
            confidence_score=1,
        )

    def _parse_relative_date(self, text: str) -> Optional[datetime]:
        """Parse relative date strings like '2 days ago', '1 week ago'."""
        text = text.lower().strip()
        now = datetime.now()

        patterns = [
            (r"(\d+)\s*minute", lambda m: now - timedelta(minutes=int(m))),
            (r"(\d+)\s*hour", lambda m: now - timedelta(hours=int(m))),
            (r"(\d+)\s*day", lambda m: now - timedelta(days=int(m))),
            (r"(\d+)\s*week", lambda m: now - timedelta(weeks=int(m))),
            (r"(\d+)\s*month", lambda m: now - timedelta(days=int(m) * 30)),
            (r"just\s*now", lambda _: now),
            (r"today", lambda _: now),
            (r"yesterday", lambda _: now - timedelta(days=1)),
        ]

        for pattern, calc in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    val = int(match.group(1)) if match.lastindex else 0
                    return calc(val)
                except (ValueError, IndexError):
                    return calc(0)

        return None
