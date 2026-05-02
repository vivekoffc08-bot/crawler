import { useState, useMemo, useCallback } from 'react';

/**
 * Custom hook for client-side filtering and sorting of already-fetched job results.
 */
export function useFilters(jobs = []) {
  const [filters, setFilters] = useState({
    sources: [],        // Filter by source (e.g., ["linkedin", "naukri"])
    jobTypes: [],       // Filter by job type
    isRemote: null,     // true, false, or null (any)
    salaryMin: null,    // Minimum salary filter
    experienceMax: null,// Max experience filter
    searchText: '',     // Text search within results
  });

  const [sortBy, setSortBy] = useState('latest'); // 'latest', 'relevant', 'salary'

  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const toggleArrayFilter = useCallback((key, value) => {
    setFilters((prev) => {
      const arr = prev[key] || [];
      const exists = arr.includes(value);
      return {
        ...prev,
        [key]: exists ? arr.filter((v) => v !== value) : [...arr, value],
      };
    });
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      sources: [],
      jobTypes: [],
      isRemote: null,
      salaryMin: null,
      experienceMax: null,
      searchText: '',
    });
    setSortBy('latest');
  }, []);

  // Apply filters
  const filteredJobs = useMemo(() => {
    let result = [...jobs];

    // Source filter
    if (filters.sources.length > 0) {
      result = result.filter((job) => filters.sources.includes(job.source));
    }

    // Job type filter
    if (filters.jobTypes.length > 0) {
      result = result.filter((job) =>
        job.job_type && filters.jobTypes.includes(job.job_type)
      );
    }

    // Remote filter
    if (filters.isRemote !== null) {
      result = result.filter((job) => job.is_remote === filters.isRemote);
    }

    // Text search (title, company, location, skills)
    if (filters.searchText.trim()) {
      const q = filters.searchText.toLowerCase();
      result = result.filter((job) =>
        job.title.toLowerCase().includes(q) ||
        job.company.toLowerCase().includes(q) ||
        job.location.toLowerCase().includes(q) ||
        (job.skills_required || []).some((s) => s.toLowerCase().includes(q))
      );
    }

    // Sort
    switch (sortBy) {
      case 'latest':
        result.sort((a, b) => {
          const dateA = a.posted_date ? new Date(a.posted_date) : new Date(0);
          const dateB = b.posted_date ? new Date(b.posted_date) : new Date(0);
          return dateB - dateA;
        });
        break;
      case 'relevant':
        result.sort((a, b) => b.confidence_score - a.confidence_score);
        break;
      case 'salary':
        result.sort((a, b) => {
          const salA = parseSalary(a.salary_range);
          const salB = parseSalary(b.salary_range);
          return salB - salA;
        });
        break;
      default:
        break;
    }

    return result;
  }, [jobs, filters, sortBy]);

  // Count jobs per source (for filter sidebar badges)
  const sourceCounts = useMemo(() => {
    const counts = {};
    jobs.forEach((job) => {
      counts[job.source] = (counts[job.source] || 0) + 1;
    });
    return counts;
  }, [jobs]);

  // Count jobs per type
  const typeCounts = useMemo(() => {
    const counts = {};
    jobs.forEach((job) => {
      if (job.job_type) {
        counts[job.job_type] = (counts[job.job_type] || 0) + 1;
      }
    });
    return counts;
  }, [jobs]);

  return {
    filters,
    sortBy,
    filteredJobs,
    sourceCounts,
    typeCounts,
    updateFilter,
    toggleArrayFilter,
    setSortBy,
    resetFilters,
  };
}

/**
 * Extract a numeric salary value from salary range strings for sorting.
 * Handles formats like "₹10 - ₹15 LPA", "$80,000 - $120,000", "INR 500000"
 */
function parseSalary(salaryStr) {
  if (!salaryStr) return 0;
  // Extract all numbers
  const numbers = salaryStr.match(/[\d,]+/g);
  if (!numbers || numbers.length === 0) return 0;
  // Take the highest number
  const values = numbers.map((n) => parseInt(n.replace(/,/g, ''), 10));
  return Math.max(...values);
}
