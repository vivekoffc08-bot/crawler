"""
Naukri.com scraper — critical for India-based job search.
Uses Playwright for JS rendering + JSON-LD structured data extraction.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import quote

from bs4 import BeautifulSoup

from models.job import JobPosting, JobQuery
from scrapers.base import BaseScraper
from utils.dedup import generate_job_id

logger = logging.getLogger(__name__)


class NaukriScraper(BaseScraper):
    name = "naukri"
    base_url = "https://www.naukri.com"
    requires_playwright = True

    SOURCE_LOGO = "https://static.naukimg.com/s/4/100/i/naukri_Logo.png"

    # Naukri salary codes (LPA)
    SALARY_MAP = {
        0: "0",
        3: "3",
        5: "5",
        7: "7",
        10: "10",
        15: "15",
        20: "20",
        25: "25",
        30: "30",
        50: "50",
    }

    def _get_salary_code(self, salary_lpa: Optional[int]) -> str:
        """Map salary in LPA to Naukri's salary filter code."""
        if not salary_lpa:
            return ""
        # Find closest available salary code
        closest = min(self.SALARY_MAP.keys(), key=lambda x: abs(x - salary_lpa))
        return self.SALARY_MAP[closest]

    def build_search_url(self, page_num: int = 0) -> str:
        """Build Naukri search URL with slugified parameters."""
        # Naukri uses slug-style URLs
        title_slug = self.query.designation.lower().replace(" ", "-")
        location_slug = self.query.location.lower().replace(" ", "-")

        url = f"{self.base_url}/{title_slug}-jobs-in-{location_slug}"

        params = []
        if self.query.experience_min is not None or self.query.experience_max is not None:
            exp_min = self.query.experience_min or 0
            exp_max = self.query.experience_max or 30
            params.append(f"experience={exp_min}")

        if self.query.salary_min:
            salary_code = self._get_salary_code(self.query.salary_min)
            if salary_code:
                params.append(f"salary={salary_code}")

        if page_num > 0:
            params.append(f"pageNo={page_num + 1}")

        if self.query.remote_ok:
            params.append("wfhType=1")

        if params:
            url += "?" + "&".join(params)

        return url

    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Fetch Naukri search page with Playwright."""
        url = self.build_search_url(page_num)
        logger.info(f"[{self.name}] Fetching: {url}")

        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for job listings to appear
            try:
                await self._page.wait_for_selector(
                    ".srp-jobtuple-wrapper, .jobTupleHeader, .list, article.jobTuple",
                    timeout=10000,
                )
            except Exception:
                logger.warning(f"[{self.name}] Job selector timeout")

            # Scroll to trigger lazy loading
            for _ in range(2):
                await self._page.evaluate("window.scrollBy(0, 600)")
                await self._page.wait_for_timeout(800)

            return await self._page.content()

        except Exception as e:
            logger.error(f"[{self.name}] Fetch error: {e}")
            return None

    async def parse_jobs(self, html: str) -> List[JobPosting]:
        """
        Parse Naukri results.
        Strategy: First try JSON-LD structured data (faster, more reliable),
        then fall back to DOM scraping.
        """
        soup = BeautifulSoup(html, "lxml")
        jobs = []

        # Strategy 1: Extract from JSON-LD script tags
        json_ld_jobs = self._parse_json_ld(soup)
        if json_ld_jobs:
            logger.info(f"[{self.name}] Extracted {len(json_ld_jobs)} jobs from JSON-LD")
            return json_ld_jobs

        # Strategy 2: DOM scraping fallback
        cards = soup.find_all("article", class_=re.compile(r"jobTuple|srp-jobtuple"))
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"srp-jobtuple-wrapper|cust-job-tuple"))
        if not cards:
            # Try newer Naukri layout
            cards = soup.find_all("div", class_=re.compile(r"styles_jlc__main"))

        logger.debug(f"[{self.name}] Found {len(cards)} DOM cards")

        for card in cards:
            try:
                job = self._parse_dom_card(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                logger.debug(f"[{self.name}] Card parse error: {e}")
                continue

        return jobs

    def _parse_json_ld(self, soup) -> List[JobPosting]:
        """Extract job postings from JSON-LD structured data."""
        jobs = []
        scripts = soup.find_all("script", type="application/ld+json")

        for script in scripts:
            try:
                data = json.loads(script.string)

                # Handle single job posting
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    job = self._json_ld_to_posting(data)
                    if job:
                        jobs.append(job)

                # Handle ItemList of job postings
                elif isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        if isinstance(item, dict):
                            posting = item.get("item", item)
                            if posting.get("@type") == "JobPosting":
                                job = self._json_ld_to_posting(posting)
                                if job:
                                    jobs.append(job)

                # Handle array of postings
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "JobPosting":
                            job = self._json_ld_to_posting(item)
                            if job:
                                jobs.append(job)

            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"[{self.name}] JSON-LD parse error: {e}")
                continue

        return jobs

    def _json_ld_to_posting(self, data: dict) -> Optional[JobPosting]:
        """Convert a JSON-LD JobPosting schema to our JobPosting model."""
        title = data.get("title", "")
        if not title:
            return None

        # Company
        org = data.get("hiringOrganization", {})
        company = org.get("name", "Unknown Company") if isinstance(org, dict) else str(org)

        # Location
        loc_data = data.get("jobLocation", {})
        if isinstance(loc_data, dict):
            address = loc_data.get("address", {})
            if isinstance(address, dict):
                location = address.get("addressLocality", "") or address.get("name", "")
                region = address.get("addressRegion", "")
                if region and location:
                    location = f"{location}, {region}"
            else:
                location = str(address)
        elif isinstance(loc_data, list) and loc_data:
            first_loc = loc_data[0]
            address = first_loc.get("address", {}) if isinstance(first_loc, dict) else {}
            location = address.get("addressLocality", self.query.location) if isinstance(address, dict) else self.query.location
        else:
            location = self.query.location

        # Salary
        salary_data = data.get("baseSalary", {})
        salary_range = None
        if isinstance(salary_data, dict):
            value = salary_data.get("value", {})
            if isinstance(value, dict):
                min_val = value.get("minValue", "")
                max_val = value.get("maxValue", "")
                currency = salary_data.get("currency", "INR")
                if min_val and max_val:
                    salary_range = f"{currency} {min_val} - {max_val}"
                elif min_val:
                    salary_range = f"{currency} {min_val}+"

        # URL
        apply_url = data.get("url", "") or data.get("sameAs", "")
        if not apply_url:
            return None

        # Posted date
        posted_date = None
        date_str = data.get("datePosted", "")
        if date_str:
            try:
                posted_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Skills from description
        description = data.get("description", "")
        skills = self._extract_skills(description)

        # Experience
        exp_data = data.get("experienceRequirements", "")
        experience = str(exp_data) if exp_data else None

        # Employment type
        emp_type = data.get("employmentType", "")
        job_type = None
        if emp_type:
            type_map = {
                "FULL_TIME": "full-time",
                "PART_TIME": "part-time",
                "CONTRACT": "contract",
                "INTERN": "internship",
                "TEMPORARY": "contract",
            }
            if isinstance(emp_type, list):
                emp_type = emp_type[0] if emp_type else ""
            job_type = type_map.get(emp_type.upper(), emp_type.lower())

        is_remote = bool(
            data.get("jobLocationType") == "TELECOMMUTE" or
            "remote" in location.lower() or
            "work from home" in (description or "").lower()
        )

        job_id = generate_job_id(title, company, location)

        return JobPosting(
            id=job_id,
            title=title,
            company=company,
            location=location or self.query.location,
            salary_range=salary_range,
            experience_required=experience,
            job_type=job_type,
            skills_required=skills[:10],
            posted_date=posted_date,
            apply_url=apply_url,
            source=self.name,
            source_logo=self.SOURCE_LOGO,
            description_snippet=description[:200] if description else None,
            is_remote=is_remote,
            confidence_score=1,
        )

    def _parse_dom_card(self, card) -> Optional[JobPosting]:
        """Fallback DOM-based card parsing for Naukri."""
        # Title
        title_el = card.find("a", class_=re.compile(r"title|jobTitle")) or card.find("a", {"class": "title"})
        if not title_el:
            title_el = card.find("h2") or card.find("a")
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None

        # URL
        job_url = None
        if title_el and title_el.name == "a":
            job_url = title_el.get("href", "")
        if not job_url:
            link = card.find("a", href=re.compile(r"naukri\.com/job-listings"))
            job_url = link["href"] if link else None
        if not job_url:
            return None
        if not job_url.startswith("http"):
            job_url = f"https://www.naukri.com{job_url}"

        # Company
        company_el = card.find("a", class_=re.compile(r"comp-name|subTitle")) or \
                     card.find("span", class_=re.compile(r"comp-name"))
        company = company_el.get_text(strip=True) if company_el else "Unknown Company"

        # Location
        loc_el = card.find("span", class_=re.compile(r"loc|location|locWd498"))
        location = loc_el.get_text(strip=True) if loc_el else self.query.location

        # Experience
        exp_el = card.find("span", class_=re.compile(r"exp|expwdth"))
        experience = exp_el.get_text(strip=True) if exp_el else None

        # Salary
        sal_el = card.find("span", class_=re.compile(r"sal|salary"))
        salary = sal_el.get_text(strip=True) if sal_el else None
        if salary and salary.lower() == "not disclosed":
            salary = None

        # Skills
        skill_els = card.find_all("li", class_=re.compile(r"tag|skill")) or \
                    card.find_all("span", class_=re.compile(r"tag|skill"))
        skills = [s.get_text(strip=True) for s in skill_els if s.get_text(strip=True)]

        # Posted date
        date_el = card.find("span", class_=re.compile(r"date|freshness"))
        posted_date = None
        if date_el:
            posted_date = self._parse_naukri_date(date_el.get_text(strip=True))

        is_remote = "remote" in location.lower() or "work from home" in location.lower()

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

    def _parse_naukri_date(self, text: str) -> Optional[datetime]:
        """Parse Naukri date strings like 'Few Hours Ago', '3 Days Ago'."""
        text = text.lower().strip()
        now = datetime.now()

        if "just now" in text or "few hours" in text:
            return now
        if "today" in text:
            return now

        match = re.search(r"(\d+)\s*day", text)
        if match:
            return now - timedelta(days=int(match.group(1)))

        match = re.search(r"(\d+)\s*hour", text)
        if match:
            return now - timedelta(hours=int(match.group(1)))

        if "1 week" in text:
            return now - timedelta(weeks=1)

        match = re.search(r"(\d+)\s*week", text)
        if match:
            return now - timedelta(weeks=int(match.group(1)))

        return None

    def _extract_skills(self, text: str) -> List[str]:
        """Extract common tech skills from job description text."""
        if not text:
            return []

        common_skills = [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Angular",
            "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "AWS",
            "Azure", "GCP", "Docker", "Kubernetes", "Git", "CI/CD",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "Data Science", "Power BI", "Tableau", "Excel", "REST API",
            "GraphQL", "Microservices", "Linux", "C++", "C#", ".NET",
            "PHP", "Ruby", "Go", "Rust", "Swift", "Kotlin", "Flutter",
            "React Native", "HTML", "CSS", "Sass", "Tailwind",
            "Jenkins", "Terraform", "Ansible", "Spark", "Hadoop",
            "Kafka", "RabbitMQ", "Elasticsearch", "Nginx",
        ]

        found = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill.lower() in text_lower:
                found.append(skill)

        return found
