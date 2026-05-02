from .base import BaseScraper
from .linkedin import LinkedInScraper
from .indeed import IndeedScraper
from .naukri import NaukriScraper
from .glassdoor import GlassdoorScraper
from .wellfound import WellfoundScraper
from .internshala import InternshalaScraper
from .shine import ShineScraper
from .monster import MonsterScraper

SCRAPER_MAP = {
    "linkedin": LinkedInScraper,
    "indeed": IndeedScraper,
    "naukri": NaukriScraper,
    "glassdoor": GlassdoorScraper,
    "wellfound": WellfoundScraper,
    "internshala": InternshalaScraper,
    "shine": ShineScraper,
    "monster": MonsterScraper,
}

__all__ = [
    "BaseScraper",
    "LinkedInScraper",
    "IndeedScraper",
    "NaukriScraper",
    "GlassdoorScraper",
    "WellfoundScraper",
    "InternshalaScraper",
    "ShineScraper",
    "MonsterScraper",
    "SCRAPER_MAP",
]
