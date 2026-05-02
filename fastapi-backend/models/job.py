"""
Pydantic models for job search queries, postings, and API responses.
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ExperienceLevel(str, Enum):
    fresher = "0-1"
    junior = "1-3"
    mid = "3-5"
    senior = "5-10"
    lead = "10+"


class JobType(str, Enum):
    full_time = "full-time"
    part_time = "part-time"
    contract = "contract"
    internship = "internship"
    remote = "remote"


class JobQuery(BaseModel):
    designation: str                         # e.g. "Software Engineer"
    location: str                            # e.g. "Mumbai" or "Remote"
    experience_min: int = 0                  # years
    experience_max: int = 10
    salary_min: Optional[int] = None         # in LPA for India, USD/yr for others
    salary_max: Optional[int] = None
    job_type: Optional[JobType] = None
    skills: Optional[List[str]] = []         # e.g. ["Python", "React"]
    remote_ok: bool = False
    sources: List[str] = ["all"]             # which sites to scrape
    max_results: int = 50


class JobPosting(BaseModel):
    id: str                                  # hash of title+company+location
    title: str
    company: str
    location: str
    salary_range: Optional[str] = None
    experience_required: Optional[str] = None
    job_type: Optional[str] = None
    skills_required: List[str] = []
    posted_date: Optional[datetime] = None
    apply_url: str                           # DIRECT link — this is the key output
    source: str                              # "linkedin", "naukri", etc.
    source_logo: Optional[str] = None        # URL to site favicon/logo
    description_snippet: Optional[str] = None
    confidence_score: int = 1                # 1-3, higher = appeared on more sites
    is_remote: bool = False


class SearchResponse(BaseModel):
    query: JobQuery
    total_found: int
    jobs: List[JobPosting]
    sources_scraped: List[str]
    scrape_time_seconds: float
    errors: List[str] = []
