"""
Wellfound (formerly AngelList) scraper — for startup jobs.
Uses Playwright as it's a React-rendered SPA.
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


class WellfoundScraper(BaseScraper):
    name = "wellfound"
    base_url = "https://wellfound.com/jobs"
    requires_playwright = True

    SOURCE_LOGO = "https://wellfound.com/favicon.ico"

    def build_search_url(self, page_num: int = 0) -> str:
        """Build Wellfound job search URL."""
        params = []
        if self.query.designation:
            params.append(f"role={quote_plus(self.query.designation)}")
        if self.query.location:
            params.append(f"location={quote_plus(self.query.location)}")
        if self.query.remote_ok:
            params.append("remote=true")
        if page_num > 0:
            params.append(f"page={page_num + 1}")

        query_string = "&".join(params)
        return f"{self.base_url}?{query_string}" if params else self.base_url

    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Fetch Wellfound page using Playwright (React SPA)."""
        url = self.build_search_url(page_num)
        logger.info(f"[{self.name}] Fetching: {url}")

        try:
            await self._page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for job listings to render
            try:
                await self._page.wait_for_selector(
                    "[class*='jobListing'], [class*='styles_component'], [data-test='JobSearchResults']",
                    timeout=12000,
                )
            except Exception:
                logger.warning(f"[{self.name}] Job listing selector timeout")

            # Scroll to load more
            for _ in range(3):
                await self._page.evaluate("window.scrollBy(0, 600)")
                await self._page.wait_for_timeout(1000)

            return await self._page.content()

        except Exception as e:
            logger.error(f"[{self.name}] Fetch error: {e}")
            return None

    async def parse_jobs(self, html: str) -> List[JobPosting]:
        """Parse Wellfound search results."""
        jobs = []
        soup = BeautifulSoup(html, "lxml")

        # Wellfound uses various class patterns
        cards = soup.find_all("div", class_=re.compile(r"styles_component|JobListing|job-listing"))
        if not cards:
            # Try a broader search
            cards = soup.find_all("div", class_=re.compile(r"styles_result|StartupResult"))
        if not cards:
            # Try to find job links
            job_links = soup.find_all("a", href=re.compile(r"/jobs/"))
            cards = [link.parent for link in job_links if link.parent]

        logger.debug(f"[{self.name}] Found {len(cards)} raw cards")

        for card in cards:
            try:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] Card parse error: {e}")

        return jobs

    def _parse_card(self, card) -> Optional[JobPosting]:
        """Parse a single Wellfound job card."""
        # Title — usually in a heading or styled span
        title_el = card.find("h2") or card.find("h3") or \
                   card.find("a", class_=re.compile(r"title|jobTitle"))
        title = title_el.get_text(strip=True) if title_el else None

        if not title:
            # Try finding from a link
            links = card.find_all("a")
            for link in links:
                text = link.get_text(strip=True)
                if text and len(text) > 5 and not text.startswith("http"):
                    href = link.get("href", "")
                    if "/jobs/" in href or "/role/" in href:
                        title = text
                        break

        if not title:
            return None

        # Company
        company_el = card.find("h3") if card.find("h2") else None
        if not company_el:
            company_el = card.find("span", class_=re.compile(r"company|startup-name"))
        company = company_el.get_text(strip=True) if company_el else "Startup"

        # URL
        job_url = None
        links = card.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "/jobs/" in href or "/role/" in href:
                if href.startswith("/"):
                    job_url = f"https://wellfound.com{href}"
                else:
                    job_url = href
                break

        if not job_url:
            return None

        # Location
        loc_el = card.find("span", class_=re.compile(r"location"))
        location = loc_el.get_text(strip=True) if loc_el else self.query.location

        # Salary
        sal_el = card.find("span", class_=re.compile(r"salary|compensation"))
        salary = sal_el.get_text(strip=True) if sal_el else None

        # Remote
        is_remote = bool(
            card.find(string=re.compile(r"remote", re.I)) or
            "remote" in location.lower()
        )

        job_id = generate_job_id(title, company, location)

        return JobPosting(
            id=job_id,
            title=title,
            company=company,
            location=location,
            salary_range=salary,
            apply_url=job_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            is_remote=is_remote,
            confidence_score=1,
        )
