"""
Indeed Jobs scraper.
Uses httpx for initial request; falls back to Playwright if blocked.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from models.job import JobPosting, JobQuery
from scrapers.base import BaseScraper
from utils.dedup import generate_job_id
from utils.rotate_ua import get_random_headers

logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):
    name = "indeed"
    base_url = "https://www.indeed.com/jobs"
    requires_playwright = False  # Try httpx first

    SOURCE_LOGO = "https://upload.wikimedia.org/wikipedia/commons/f/fc/Indeed_logo.svg"

    def build_search_url(self, page_num: int = 0) -> str:
        """Build Indeed search URL."""
        params = {
            "q": self.query.designation,
            "l": self.query.location,
            "sort": "date",
            "start": page_num * 10,
        }
        if self.query.salary_min:
            params["salary"] = str(self.query.salary_min)
        if self.query.job_type:
            jt_map = {
                "full-time": "fulltime",
                "part-time": "parttime",
                "contract": "contract",
                "internship": "internship",
            }
            params["jt"] = jt_map.get(self.query.job_type, "")
        if self.query.remote_ok:
            params["remotejob"] = "032b3046-06a3-4876-8dfd-474eb5e7ed11"

        query_string = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items() if v)
        return f"{self.base_url}?{query_string}"

    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Fetch Indeed search results using httpx, fallback to Playwright."""
        url = self.build_search_url(page_num)
        logger.info(f"[{self.name}] Fetching: {url}")

        # Try httpx first (faster)
        try:
            async with httpx.AsyncClient(
                headers=get_random_headers(),
                follow_redirects=True,
                timeout=20.0,
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    html = response.text
                    # Check if we got real content or a block page
                    if "job_seen_beacon" in html or "jobsearch-ResultsList" in html or "resultContent" in html:
                        return html
                    else:
                        logger.warning(f"[{self.name}] httpx response missing job cards, trying Playwright")
                else:
                    logger.warning(f"[{self.name}] httpx returned {response.status_code}")
        except Exception as e:
            logger.warning(f"[{self.name}] httpx failed: {e}")

        # Fallback to Playwright
        try:
            if not self._browser:
                setup_ok = await self.setup_playwright()
                if not setup_ok:
                    return None

            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                await self._page.wait_for_selector(
                    ".job_seen_beacon, .resultContent, .jobsearch-ResultsList",
                    timeout=10000
                )
            except Exception:
                pass

            html = await self._page.content()
            return html

        except Exception as e:
            logger.error(f"[{self.name}] Playwright fallback failed: {e}")
            return None

    async def parse_jobs(self, html: str) -> List[JobPosting]:
        """Parse Indeed search results HTML."""
        jobs = []
        soup = BeautifulSoup(html, "lxml")

        # Indeed uses various card classes
        cards = soup.find_all("div", class_=re.compile(r"job_seen_beacon|cardOutline"))
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"resultContent|slider_item"))
        if not cards:
            # Try the list items approach
            cards = soup.find_all("li", class_=re.compile(r"css-.*"))
            cards = [c for c in cards if c.find("h2")]

        logger.debug(f"[{self.name}] Found {len(cards)} raw cards")

        for card in cards:
            try:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] Card parse error: {e}")
                continue

        return jobs

    def _parse_card(self, card) -> Optional[JobPosting]:
        """Parse a single Indeed job card."""
        # Title
        title_el = card.find("h2", class_=re.compile(r"jobTitle")) or card.find("h2")
        if title_el:
            # Remove hidden spans
            for hidden in title_el.find_all("span", class_="visually-hidden"):
                hidden.decompose()
            title = title_el.get_text(strip=True)
        else:
            return None

        if not title or len(title) < 3:
            return None

        # Job key for URL
        link_el = card.find("a", href=re.compile(r"jk=|/viewjob|/rc/clk"))
        job_key = None
        job_url = None
        if link_el:
            href = link_el.get("href", "")
            # Extract job key
            jk_match = re.search(r"jk=([a-f0-9]+)", href)
            if jk_match:
                job_key = jk_match.group(1)
                job_url = f"https://www.indeed.com/viewjob?jk={job_key}"
            elif href.startswith("/"):
                job_url = f"https://www.indeed.com{href}"
            else:
                job_url = href

        if not job_url:
            # Try data attribute
            jk_attr = card.get("data-jk") or card.get("id", "").replace("job_", "")
            if jk_attr:
                job_url = f"https://www.indeed.com/viewjob?jk={jk_attr}"
            else:
                return None

        # Company
        company_el = card.find("span", {"data-testid": "company-name"}) or \
                     card.find("span", class_=re.compile(r"companyName|company"))
        company = company_el.get_text(strip=True) if company_el else "Unknown Company"

        # Location
        location_el = card.find("div", {"data-testid": "text-location"}) or \
                      card.find("div", class_=re.compile(r"companyLocation"))
        location = location_el.get_text(strip=True) if location_el else self.query.location

        # Salary
        salary_el = card.find("div", class_=re.compile(r"salary-snippet|metadata.*salary"))
        salary = salary_el.get_text(strip=True) if salary_el else None

        # Snippet / Description
        snippet_el = card.find("div", class_=re.compile(r"job-snippet")) or \
                     card.find("table", class_=re.compile(r"jobCardShelfContainer"))
        snippet = snippet_el.get_text(strip=True)[:200] if snippet_el else None

        # Posted date
        date_el = card.find("span", class_=re.compile(r"date")) or \
                  card.find("span", {"data-testid": "myJobsStateDate"})
        posted_date = None
        if date_el:
            posted_date = self._parse_relative_date(date_el.get_text(strip=True))

        # Remote check
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
            posted_date=posted_date,
            apply_url=job_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            description_snippet=snippet,
            is_remote=is_remote,
            confidence_score=1,
        )

    def _parse_relative_date(self, text: str) -> Optional[datetime]:
        """Parse Indeed's relative date strings."""
        text = text.lower().strip()
        now = datetime.now()

        if "just posted" in text or "today" in text:
            return now
        
        match = re.search(r"(\d+)\+?\s*day", text)
        if match:
            return now - timedelta(days=int(match.group(1)))
        
        match = re.search(r"(\d+)\s*hour", text)
        if match:
            return now - timedelta(hours=int(match.group(1)))

        if "active" in text:
            match = re.search(r"(\d+)", text)
            if match:
                return now - timedelta(days=int(match.group(1)))

        return None
