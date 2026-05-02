"""
Shine.com scraper — India-specific job board.
Uses httpx + BeautifulSoup (standard HTML rendering).
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from models.job import JobPosting, JobQuery
from scrapers.base import BaseScraper
from utils.dedup import generate_job_id
from utils.rotate_ua import get_random_headers

logger = logging.getLogger(__name__)


class ShineScraper(BaseScraper):
    name = "shine"
    base_url = "https://www.shine.com"
    requires_playwright = False

    SOURCE_LOGO = "https://www.shine.com/favicon.ico"

    def build_search_url(self, page_num: int = 0) -> str:
        """Build Shine.com job search URL (slug-style)."""
        title_slug = self.query.designation.lower().replace(" ", "-")
        location_slug = self.query.location.lower().replace(" ", "-")

        url = f"{self.base_url}/job-search/{title_slug}-jobs-in-{location_slug}"

        if page_num > 0:
            url += f"-{page_num + 1}"

        return url

    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Fetch Shine.com page using httpx."""
        url = self.build_search_url(page_num)
        logger.info(f"[{self.name}] Fetching: {url}")

        try:
            async with httpx.AsyncClient(
                headers=get_random_headers(),
                follow_redirects=True,
                timeout=20.0,
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"[{self.name}] HTTP {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"[{self.name}] Fetch error: {e}")
            return None

    async def parse_jobs(self, html: str) -> List[JobPosting]:
        """Parse Shine.com search results."""
        jobs = []
        soup = BeautifulSoup(html, "lxml")

        # Shine job cards
        cards = soup.find_all("div", class_=re.compile(r"jobCard|search_listing|job_listing_row"))
        if not cards:
            cards = soup.find_all("div", id=re.compile(r"srp_job_tuple"))
        if not cards:
            # Broader fallback
            cards = soup.find_all("div", class_=re.compile(r"search-results-job"))

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
        """Parse a single Shine.com job card."""
        # Title
        title_el = card.find("a", class_=re.compile(r"job_title|jobTitle|title")) or \
                   card.find("h2") or card.find("h3")
        if not title_el:
            title_el = card.find("a")
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None

        # URL
        job_url = None
        if title_el and title_el.name == "a" and title_el.get("href"):
            href = title_el["href"]
            if href.startswith("/"):
                job_url = f"https://www.shine.com{href}"
            elif href.startswith("http"):
                job_url = href

        if not job_url:
            link = card.find("a", href=re.compile(r"shine\.com"))
            if link:
                job_url = link["href"]

        if not job_url:
            return None

        # Company
        company_el = card.find("span", class_=re.compile(r"company|comp_name")) or \
                     card.find("div", class_=re.compile(r"comp_name|company"))
        company = company_el.get_text(strip=True) if company_el else "Unknown Company"

        # Location
        loc_el = card.find("span", class_=re.compile(r"loc|location")) or \
                 card.find("div", class_=re.compile(r"location"))
        location = loc_el.get_text(strip=True) if loc_el else self.query.location

        # Experience
        exp_el = card.find("span", class_=re.compile(r"exp|experience")) or \
                 card.find("div", class_=re.compile(r"experience"))
        experience = exp_el.get_text(strip=True) if exp_el else None

        # Salary
        sal_el = card.find("span", class_=re.compile(r"sal|salary")) or \
                 card.find("div", class_=re.compile(r"salary"))
        salary = sal_el.get_text(strip=True) if sal_el else None

        # Skills
        skill_els = card.find_all("span", class_=re.compile(r"skill|tag"))
        skills = [s.get_text(strip=True) for s in skill_els if s.get_text(strip=True)]

        # Posted date
        date_el = card.find("span", class_=re.compile(r"date|posted")) or \
                  card.find("div", class_=re.compile(r"date"))
        posted_date = None
        if date_el:
            posted_date = self._parse_date(date_el.get_text(strip=True))

        is_remote = "remote" in location.lower() or bool(card.find(string=re.compile(r"remote|wfh", re.I)))

        job_id = generate_job_id(title, company, location)

        return JobPosting(
            id=job_id,
            title=title,
            company=company,
            location=location,
            salary_range=salary,
            experience_required=experience,
            skills_required=skills[:10],
            posted_date=posted_date,
            apply_url=job_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            is_remote=is_remote,
            confidence_score=1,
        )

    def _parse_date(self, text: str) -> Optional[datetime]:
        """Parse Shine date strings."""
        text = text.lower().strip()
        now = datetime.now()

        if "today" in text or "just" in text:
            return now

        match = re.search(r"(\d+)\s*day", text)
        if match:
            return now - timedelta(days=int(match.group(1)))

        match = re.search(r"(\d+)\s*hour", text)
        if match:
            return now - timedelta(hours=int(match.group(1)))

        match = re.search(r"(\d+)\s*week", text)
        if match:
            return now - timedelta(weeks=int(match.group(1)))

        return None
