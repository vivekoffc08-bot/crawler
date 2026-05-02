"""
Internshala scraper — India-specific, for freshers and internship roles.
Uses httpx + BeautifulSoup (simpler HTML, no JS required).
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


class InternshalaScraper(BaseScraper):
    name = "internshala"
    base_url = "https://internshala.com"
    requires_playwright = False

    SOURCE_LOGO = "https://internshala.com/favicon.ico"

    def build_search_url(self, page_num: int = 0) -> str:
        """Build Internshala job search URL (slug-style)."""
        title_slug = self.query.designation.lower().replace(" ", "-")
        location_slug = self.query.location.lower().replace(" ", "-")

        url = f"{self.base_url}/jobs/{title_slug}-jobs-in-{location_slug}"

        if page_num > 0:
            url += f"/page-{page_num + 1}"

        return url

    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Fetch Internshala page using httpx."""
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
        """Parse Internshala job listings."""
        jobs = []
        soup = BeautifulSoup(html, "lxml")

        # Internshala job cards
        cards = soup.find_all("div", class_=re.compile(r"individual_internship|internship_meta"))
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"container-fluid individual"))
        if not cards:
            # Try the job-specific listing class
            cards = soup.find_all("div", id=re.compile(r"internship_list_container"))
            if cards:
                cards = cards[0].find_all("div", class_=re.compile(r"individual"))

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
        """Parse a single Internshala job card."""
        # Title
        title_el = card.find("h3", class_=re.compile(r"heading_4_5|job-internship-name")) or \
                   card.find("a", class_=re.compile(r"view_detail_button"))
        if not title_el:
            title_el = card.find("h3") or card.find("h4")
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None

        # URL
        link = card.find("a", href=True, class_=re.compile(r"view_detail_button|heading"))
        if not link:
            link = card.find("a", href=re.compile(r"/job/detail|/internship/detail"))
        if not link:
            # Find any relevant link
            links = card.find_all("a", href=True)
            for l in links:
                if "/job/" in l.get("href", "") or "/internship/" in l.get("href", ""):
                    link = l
                    break

        job_url = None
        if link:
            href = link.get("href", "")
            if href.startswith("/"):
                job_url = f"https://internshala.com{href}"
            elif href.startswith("http"):
                job_url = href

        if not job_url:
            return None

        # Company
        company_el = card.find("p", class_=re.compile(r"company_name|heading_6")) or \
                     card.find("h4", class_=re.compile(r"company_name"))
        if not company_el:
            company_el = card.find("a", class_=re.compile(r"link_display_like_text"))
        company = company_el.get_text(strip=True) if company_el else "Unknown Company"

        # Location
        loc_el = card.find("span", class_=re.compile(r"location_link")) or \
                 card.find("a", id=re.compile(r"location_names")) or \
                 card.find("div", class_=re.compile(r"individual_internship_details"))
        location = self.query.location
        if loc_el:
            loc_text = loc_el.get_text(strip=True)
            if loc_text:
                location = loc_text

        # Stipend / Salary
        stipend_el = card.find("span", class_=re.compile(r"stipend")) or \
                     card.find("div", class_=re.compile(r"stipend"))
        salary = stipend_el.get_text(strip=True) if stipend_el else None

        # Duration / Experience
        duration_el = card.find("div", class_=re.compile(r"item_body"))
        experience = None
        if duration_el:
            experience = duration_el.get_text(strip=True)

        # Posted date
        status_el = card.find("div", class_=re.compile(r"status-success|status"))
        posted_date = None
        if status_el:
            date_text = status_el.get_text(strip=True)
            posted_date = self._parse_date(date_text)

        # Job type
        job_type = "internship" if "internship" in (title + " " + self.base_url).lower() else "full-time"

        is_remote = bool(card.find(string=re.compile(r"work from home|remote", re.I)))

        job_id = generate_job_id(title, company, location)

        return JobPosting(
            id=job_id,
            title=title,
            company=company,
            location=location,
            salary_range=salary,
            experience_required=experience,
            job_type=job_type,
            posted_date=posted_date,
            apply_url=job_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            is_remote=is_remote,
            confidence_score=1,
        )

    def _parse_date(self, text: str) -> Optional[datetime]:
        """Parse Internshala date strings."""
        text = text.lower().strip()
        now = datetime.now()

        if "just now" in text or "today" in text:
            return now

        match = re.search(r"(\d+)\s*day", text)
        if match:
            return now - timedelta(days=int(match.group(1)))

        match = re.search(r"(\d+)\s*week", text)
        if match:
            return now - timedelta(weeks=int(match.group(1)))

        match = re.search(r"(\d+)\s*month", text)
        if match:
            return now - timedelta(days=int(match.group(1)) * 30)

        return None
