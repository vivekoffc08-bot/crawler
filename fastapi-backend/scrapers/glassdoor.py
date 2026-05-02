"""
Glassdoor Jobs scraper.
Uses Playwright with human-like scroll behavior to bypass bot detection.
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


class GlassdoorScraper(BaseScraper):
    name = "glassdoor"
    base_url = "https://www.glassdoor.com/Job/jobs.htm"
    requires_playwright = True

    SOURCE_LOGO = "https://www.glassdoor.com/favicon.ico"

    def build_search_url(self, page_num: int = 0) -> str:
        """Build Glassdoor job search URL."""
        params = {
            "sc.keyword": self.query.designation,
            "locT": "C",
            "locKeyword": self.query.location,
        }
        if page_num > 0:
            params["p"] = str(page_num + 1)
        if self.query.salary_min:
            params["minSalary"] = str(self.query.salary_min)
        if self.query.remote_ok:
            params["remoteWorkType"] = "1"

        query_string = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
        return f"{self.base_url}?{query_string}"

    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Fetch Glassdoor page with human-like scrolling behavior."""
        url = self.build_search_url(page_num)
        logger.info(f"[{self.name}] Fetching: {url}")

        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for job listings
            try:
                await self._page.wait_for_selector(
                    "[data-test='jobListing'], .react-job-listing, .JobsList_jobListItem",
                    timeout=10000,
                )
            except Exception:
                logger.warning(f"[{self.name}] Job listing selector timeout")

            # Human-like scroll behavior
            import random
            for i in range(4):
                scroll_amount = random.randint(300, 700)
                await self._page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                await self._page.wait_for_timeout(random.randint(500, 1500))

            return await self._page.content()

        except Exception as e:
            logger.error(f"[{self.name}] Fetch error: {e}")
            return None

    async def parse_jobs(self, html: str) -> List[JobPosting]:
        """Parse Glassdoor search results."""
        jobs = []
        soup = BeautifulSoup(html, "lxml")

        # Try multiple card selectors (Glassdoor changes layout frequently)
        cards = soup.find_all("li", class_=re.compile(r"react-job-listing|JobsList_jobListItem"))
        if not cards:
            cards = soup.find_all("li", attrs={"data-test": "jobListing"})
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"JobCard|jobCard"))

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
        """Parse a single Glassdoor job card."""
        # Title
        title_el = card.find("a", class_=re.compile(r"jobTitle|job-title|JobCard_jobTitle")) or \
                   card.find("a", attrs={"data-test": "job-title"})
        if not title_el:
            title_el = card.find("h2") or card.find("a")
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None

        # Job URL
        job_url = None
        if title_el and title_el.get("href"):
            href = title_el["href"]
            if href.startswith("/"):
                job_url = f"https://www.glassdoor.com{href}"
            else:
                job_url = href
        
        # Try to extract job ID for URL construction
        if not job_url:
            job_id_attr = card.get("data-id") or card.get("data-job-id")
            if job_id_attr:
                job_url = f"https://www.glassdoor.com/job-listing/{job_id_attr}"
        
        if not job_url:
            return None

        # Company
        company_el = card.find("span", class_=re.compile(r"EmployerProfile|employer-name")) or \
                     card.find("div", class_=re.compile(r"employer|JobCard_companyName"))
        company = company_el.get_text(strip=True) if company_el else "Unknown Company"
        # Remove rating from company name (e.g., "Google4.5★")
        company = re.sub(r"[\d.]+[★☆]?$", "", company).strip()

        # Location
        loc_el = card.find("span", class_=re.compile(r"loc|location|JobCard_location")) or \
                 card.find("div", class_=re.compile(r"location"))
        location = loc_el.get_text(strip=True) if loc_el else self.query.location

        # Salary
        sal_el = card.find("span", class_=re.compile(r"salary|compensation|JobCard_salaryEstimate"))
        salary = sal_el.get_text(strip=True) if sal_el else None

        # Posted date
        age_el = card.find("div", class_=re.compile(r"listing-age|JobCard_listingAge"))
        posted_date = None
        if age_el:
            posted_date = self._parse_age(age_el.get_text(strip=True))

        is_remote = "remote" in location.lower() if location else False

        gd_job_id = generate_job_id(title, company, location)

        return JobPosting(
            id=gd_job_id,
            title=title,
            company=company,
            location=location,
            salary_range=salary,
            posted_date=posted_date,
            apply_url=job_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            is_remote=is_remote,
            confidence_score=1,
        )

    def _parse_age(self, text: str) -> Optional[datetime]:
        """Parse Glassdoor listing age like '2d', '1w', '30d+'."""
        now = datetime.now()
        text = text.strip().lower()

        match = re.search(r"(\d+)d", text)
        if match:
            return now - timedelta(days=int(match.group(1)))

        match = re.search(r"(\d+)h", text)
        if match:
            return now - timedelta(hours=int(match.group(1)))

        match = re.search(r"(\d+)w", text)
        if match:
            return now - timedelta(weeks=int(match.group(1)))

        return None
