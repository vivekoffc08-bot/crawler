"""
Abstract base scraper class.
All site-specific scrapers inherit from this and implement fetch_page + parse_jobs.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import List, Optional

from models.job import JobPosting, JobQuery
from utils.rotate_ua import get_random_ua, get_random_headers
from utils.proxy import rate_limiter

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all job scrapers.
    
    Subclasses must implement:
        - fetch_page(page_num) -> raw HTML string
        - parse_jobs(html) -> list of JobPosting
    
    The base class provides:
        - scrape() loop with pagination
        - Rate limiting between requests
        - User-agent rotation
        - Error handling with graceful degradation
    """

    name: str = ""
    base_url: str = ""
    requires_playwright: bool = False  # Whether this site needs JS rendering

    def __init__(self, query: JobQuery):
        self.query = query
        self.jobs: List[JobPosting] = []
        self.headers = get_random_headers()
        self._browser = None
        self._context = None
        self._page = None

    @abstractmethod
    async def fetch_page(self, page_num: int) -> Optional[str]:
        """Return raw HTML of results page, or None on failure."""
        pass

    @abstractmethod
    async def parse_jobs(self, html: str) -> List[JobPosting]:
        """Parse HTML and return list of JobPosting objects."""
        pass

    def build_search_url(self, page_num: int = 0) -> str:
        """Build the search URL for the given page. Override in subclass."""
        return self.base_url

    async def setup_playwright(self):
        """Initialize Playwright browser for JS-heavy sites."""
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                ]
            )
            self._context = await self._browser.new_context(
                user_agent=get_random_ua(),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="Asia/Kolkata",
            )
            
            # Apply stealth settings
            try:
                from playwright_stealth import stealth_async
                self._page = await self._context.new_page()
                await stealth_async(self._page)
            except ImportError:
                self._page = await self._context.new_page()
                logger.warning("playwright-stealth not installed, proceeding without stealth")
            
            # Block unnecessary resources to speed up loading
            await self._page.route(
                "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}",
                lambda route: route.abort()
            )
            
            return True
        except Exception as e:
            logger.error(f"[{self.name}] Failed to setup Playwright: {e}")
            return False

    async def teardown_playwright(self):
        """Clean up Playwright resources."""
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if hasattr(self, "_playwright") and self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.error(f"[{self.name}] Error during Playwright teardown: {e}")

    async def scrape(self, max_pages: int = 3) -> List[JobPosting]:
        """
        Main scraping loop. Fetches pages, parses jobs, handles errors.
        Returns collected job postings.
        """
        logger.info(f"[{self.name}] Starting scrape for '{self.query.designation}' in '{self.query.location}'")

        try:
            if self.requires_playwright:
                setup_ok = await self.setup_playwright()
                if not setup_ok:
                    logger.error(f"[{self.name}] Playwright setup failed, skipping")
                    return []

            for page_num in range(max_pages):
                try:
                    # Rate limit between pages
                    if page_num > 0:
                        delay = random.uniform(2.0, 5.0)
                        logger.debug(f"[{self.name}] Waiting {delay:.1f}s before page {page_num + 1}")
                        await asyncio.sleep(delay)

                    await rate_limiter.wait(self.name)

                    html = await self.fetch_page(page_num)
                    if not html:
                        logger.warning(f"[{self.name}] Empty response on page {page_num + 1}, stopping")
                        break

                    jobs = await self.parse_jobs(html)
                    logger.info(f"[{self.name}] Page {page_num + 1}: found {len(jobs)} jobs")

                    if len(jobs) == 0:
                        logger.info(f"[{self.name}] No more jobs found, stopping pagination")
                        break

                    self.jobs.extend(jobs)
                    rate_limiter.record_success(self.name)

                except Exception as e:
                    logger.error(f"[{self.name}] Error on page {page_num + 1}: {e}")
                    rate_limiter.record_failure(self.name, 500)
                    break  # Don't continue pagination on error

        finally:
            if self.requires_playwright:
                await self.teardown_playwright()

        logger.info(f"[{self.name}] Scrape complete: {len(self.jobs)} total jobs")
        return self.jobs
