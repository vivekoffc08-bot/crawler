"""
Apollo-style deduplication logic for job postings.
Deduplicates by hashing (normalized_title + company + location).
Jobs appearing on multiple sites get a boosted confidence score.
"""

import hashlib
import re
import string
from typing import List
from models.job import JobPosting


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison:
    - lowercase
    - remove punctuation
    - strip extra whitespace
    - remove common suffixes like 'pvt', 'ltd', 'inc', 'llc', 'private', 'limited'
    """
    if not text:
        return ""
    text = text.lower().strip()
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Remove common corporate suffixes
    suffixes = [
        "pvt", "ltd", "private", "limited", "inc", "llc", "llp",
        "corp", "corporation", "co", "company", "technologies",
        "tech", "solutions", "services", "india",
    ]
    words = text.split()
    words = [w for w in words if w not in suffixes]
    # Collapse whitespace
    text = " ".join(words)
    return text


def generate_job_id(title: str, company: str, location: str) -> str:
    """
    Generate a deterministic ID for a job posting based on
    normalized title + company + location.
    """
    norm_title = normalize_text(title)
    norm_company = normalize_text(company)
    norm_location = normalize_text(location)
    composite = f"{norm_title}|{norm_company}|{norm_location}"
    return hashlib.sha256(composite.encode("utf-8")).hexdigest()[:16]


def deduplicate_jobs(jobs: List[JobPosting]) -> List[JobPosting]:
    """
    Deduplicate job postings Apollo-style:
    1. Group by normalized (title + company + location) hash
    2. For duplicates, keep the one with the most data (longest description, etc.)
    3. Boost confidence_score based on how many sources reported the same job
    4. Sort by posted_date DESC, then confidence_score DESC
    """
    if not jobs:
        return []

    # Group jobs by their dedup key
    groups: dict[str, List[JobPosting]] = {}
    for job in jobs:
        key = generate_job_id(job.title, job.company, job.location)
        if key not in groups:
            groups[key] = []
        groups[key].append(job)

    # Merge each group into a single best-of job
    merged: List[JobPosting] = []
    for key, group in groups.items():
        # Confidence = number of unique sources
        unique_sources = set(j.source for j in group)
        confidence = min(len(unique_sources), 3)  # Cap at 3

        # Pick the "best" posting — prefer the one with the most data
        best = max(group, key=lambda j: _richness_score(j))

        # Merge skills from all sources
        all_skills = set()
        for j in group:
            all_skills.update(j.skills_required)

        # Merge salary info — pick the first non-null
        salary = best.salary_range
        if not salary:
            for j in group:
                if j.salary_range:
                    salary = j.salary_range
                    break

        # Merge experience info
        experience = best.experience_required
        if not experience:
            for j in group:
                if j.experience_required:
                    experience = j.experience_required
                    break

        # Pick the earliest posted_date
        dates = [j.posted_date for j in group if j.posted_date]
        earliest_date = min(dates) if dates else best.posted_date

        # Create the merged posting
        merged_job = JobPosting(
            id=key,
            title=best.title,
            company=best.company,
            location=best.location,
            salary_range=salary,
            experience_required=experience,
            job_type=best.job_type,
            skills_required=list(all_skills)[:15],  # Cap at 15 skills
            posted_date=earliest_date,
            apply_url=best.apply_url,
            source=best.source,
            source_logo=best.source_logo,
            description_snippet=best.description_snippet,
            confidence_score=confidence,
            is_remote=any(j.is_remote for j in group),
        )
        merged.append(merged_job)

    # Sort: posted_date DESC (newest first), then confidence_score DESC
    merged.sort(
        key=lambda j: (
            j.posted_date or __import__("datetime").datetime.min,
            j.confidence_score,
        ),
        reverse=True,
    )

    return merged


def _richness_score(job: JobPosting) -> int:
    """
    Score how "rich" a job posting is in terms of filled fields.
    Used to pick the best representative when deduplicating.
    """
    score = 0
    if job.salary_range:
        score += 3
    if job.experience_required:
        score += 2
    if job.description_snippet:
        score += len(job.description_snippet) // 50  # Longer = better
    if job.skills_required:
        score += len(job.skills_required)
    if job.posted_date:
        score += 2
    if job.job_type:
        score += 1
    if job.is_remote:
        score += 1
    return score
