"""
Monster India scraper.
Uses httpx to hit Monster India's JSON API directly.
"""

import json
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


class MonsterScraper(BaseScraper):
    name = "monster"
    base_url = "https://www.monsterindia.com"
    requires_playwright = False

    SOURCE_LOGO = "https://www.monsterindia.com/favicon.ico"

    # Monster India's search API endpoint
    API_URL = "https://www.monsterindia.com/srp/results"

    def build_search_url(self, page_num: int = 0) -> str:
        """Build Monster India search URL."""
        params = {
            "query": self.query.designation,
            "locations": self.query.location,
            "page": str(page_num + 1),
        }
        if self.query.experience_min is not None:
            params["experienceRanges"] = f"{self.query.experience_min}~{self.query.experience_max}"
        if self.query.salary_min:
            params["salaryRanges"] = f"{self.query.salary_min}~{self.query.salary_max or 100}"

        query_string = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
        return f"{self.API_URL}?{query_string}"

    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Fetch Monster India results — try JSON API first, then HTML fallback."""
        url = self.build_search_url(page_num)
        logger.info(f"[{self.name}] Fetching: {url}")

        headers = get_random_headers()
        headers["Accept"] = "application/json, text/html"

        try:
            async with httpx.AsyncClient(
                headers=headers,
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
        """Parse Monster India results — try JSON first, then HTML."""
        jobs = []

        # Strategy 1: Try parsing as JSON (API response)
        try:
            data = json.loads(html)
            if isinstance(data, dict):
                job_list = data.get("searchResult", data.get("results", data.get("jobs", [])))
                if isinstance(job_list, dict):
                    job_list = job_list.get("results", [])
                if isinstance(job_list, list):
                    for item in job_list:
                        job = self._parse_json_job(item)
                        if job:
                            jobs.append(job)
                    if jobs:
                        logger.info(f"[{self.name}] Parsed {len(jobs)} jobs from JSON API")
                        return jobs
        except (json.JSONDecodeError, TypeError):
            pass

        # Strategy 2: HTML parsing fallback
        soup = BeautifulSoup(html, "lxml")

        cards = soup.find_all("div", class_=re.compile(r"card-apply-content|job-card|job-list-card"))
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"job-tittle|job-item"))

        logger.debug(f"[{self.name}] Found {len(cards)} HTML cards")

        for card in cards:
            try:
                job = self._parse_html_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] Card parse error: {e}")

        return jobs

    def _parse_json_job(self, item: dict) -> Optional[JobPosting]:
        """Parse a job from Monster India's JSON API response."""
        if not isinstance(item, dict):
            return None

        title = item.get("title", "") or item.get("jobTitle", "")
        if not title:
            return None

        company = item.get("companyName", "") or item.get("company", {}).get("name", "Unknown Company")
        if isinstance(company, dict):
            company = company.get("name", "Unknown Company")

        # Location
        locations = item.get("locations", item.get("location", []))
        if isinstance(locations, list):
            location = ", ".join(locations) if locations else self.query.location
        elif isinstance(locations, str):
            location = locations
        else:
            location = self.query.location

        # URL
        job_url = item.get("jobUrl", "") or item.get("url", "") or item.get("applyUrl", "")
        if not job_url:
            job_id_val = item.get("jobId", "")
            if job_id_val:
                job_url = f"https://www.monsterindia.com/job/{job_id_val}"
        if job_url and not job_url.startswith("http"):
            job_url = f"https://www.monsterindia.com{job_url}"
        if not job_url:
            return None

        # Salary
        salary_range = None
        sal_min = item.get("salaryMin", item.get("minSalary", ""))
        sal_max = item.get("salaryMax", item.get("maxSalary", ""))
        if sal_min or sal_max:
            salary_range = f"₹{sal_min} - ₹{sal_max} LPA" if sal_min and sal_max else f"₹{sal_min or sal_max} LPA"

        # Experience
        exp_min = item.get("experienceMin", item.get("minExperience", ""))
        exp_max = item.get("experienceMax", item.get("maxExperience", ""))
        experience = None
        if exp_min is not None or exp_max is not None:
            experience = f"{exp_min or 0}-{exp_max or ''} years"

        # Skills
        skills = item.get("skills", []) or item.get("keySkills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]

        # Posted date
        posted_date = None
        date_str = item.get("postedDate", "") or item.get("createdDate", "")
        if date_str:
            try:
                posted_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Description
        description = item.get("description", "") or item.get("jobDescription", "")
        snippet = description[:200] if description else None

        is_remote = bool(item.get("isRemote", False)) or "remote" in location.lower()

        job_id = generate_job_id(title, company, location)

        return JobPosting(
            id=job_id,
            title=title,
            company=company,
            location=location,
            salary_range=salary_range,
            experience_required=experience,
            skills_required=skills[:10] if isinstance(skills, list) else [],
            posted_date=posted_date,
            apply_url=job_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            description_snippet=snippet,
            is_remote=is_remote,
            confidence_score=1,
        )

    def _parse_html_card(self, card) -> Optional[JobPosting]:
        """Parse a Monster India HTML job card."""
        # Title
        title_el = card.find("h3") or card.find("a", class_=re.compile(r"title|name"))
        if not title_el:
            title_el = card.find("h2") or card.find("a")
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None

        # URL
        link = card.find("a", href=True)
        job_url = None
        if link:
            href = link.get("href", "")
            if href.startswith("/"):
                job_url = f"https://www.monsterindia.com{href}"
            elif href.startswith("http"):
                job_url = href

        if not job_url:
            return None

        # Company
        company_el = card.find("span", class_=re.compile(r"company|comp")) or \
                     card.find("div", class_=re.compile(r"company"))
        company = company_el.get_text(strip=True) if company_el else "Unknown Company"

        # Location
        loc_el = card.find("span", class_=re.compile(r"loc|location"))
        location = loc_el.get_text(strip=True) if loc_el else self.query.location

        # Experience
        exp_el = card.find("span", class_=re.compile(r"exp|experience"))
        experience = exp_el.get_text(strip=True) if exp_el else None

        # Salary
        sal_el = card.find("span", class_=re.compile(r"sal|salary"))
        salary = sal_el.get_text(strip=True) if sal_el else None

        job_id = generate_job_id(title, company, location)

        return JobPosting(
            id=job_id,
            title=title,
            company=company,
            location=location,
            salary_range=salary,
            experience_required=experience,
            apply_url=job_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            confidence_score=1,
        )
