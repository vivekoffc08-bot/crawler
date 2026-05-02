import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, SlidersHorizontal, RotateCcw, AlertTriangle, Search } from 'lucide-react';
import JobCard from '../components/JobCard';
import FilterSidebar from '../components/FilterSidebar';
import LoadingState from '../components/LoadingState';
import { useJobSearch } from '../hooks/useJobSearch';
import { useFilters } from '../hooks/useFilters';

/**
 * Results Page — shows job search results with filtering and sorting.
 * Triggers the actual search on mount using the query stored in sessionStorage.
 */
export default function ResultsPage() {
  const navigate = useNavigate();
  const { data, loading, error, progress, search, cancel } = useJobSearch();
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const jobs = data?.jobs || [];
  const {
    filters,
    sortBy,
    filteredJobs,
    sourceCounts,
    typeCounts,
    updateFilter,
    toggleArrayFilter,
    setSortBy,
    resetFilters,
  } = useFilters(jobs);

  // Trigger search on mount
  useEffect(() => {
    const stored = sessionStorage.getItem('jobhunt_query');
    if (stored && !hasSearched) {
      try {
        const query = JSON.parse(stored);
        setHasSearched(true);
        search(query);
      } catch {
        navigate('/');
      }
    } else if (!stored) {
      navigate('/');
    }
  }, []);

  const handleRetry = useCallback(() => {
    const stored = sessionStorage.getItem('jobhunt_query');
    if (stored) {
      const query = JSON.parse(stored);
      search(query);
    }
  }, [search]);

  const handleNewSearch = () => {
    cancel();
    navigate('/');
  };

  // Get query info for display
  const query = data?.query || (() => {
    try {
      return JSON.parse(sessionStorage.getItem('jobhunt_query') || '{}');
    } catch {
      return {};
    }
  })();

  return (
    <div className="min-h-[calc(100vh-56px)]">
      {/* Results Header */}
      <div className="sticky top-14 z-30 bg-dark-900/90 backdrop-blur-xl border-b border-dark-400/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex items-center justify-between gap-4">
            {/* Left: Back + query info */}
            <div className="flex items-center gap-3 min-w-0">
              <button
                onClick={handleNewSearch}
                className="flex items-center gap-1.5 text-xs text-dark-100 hover:text-white transition-colors flex-shrink-0"
                id="back-to-search"
              >
                <ArrowLeft size={14} />
                <span className="hidden sm:inline">New Search</span>
              </button>

              <div className="h-5 w-px bg-dark-400/50 flex-shrink-0" />

              <div className="min-w-0">
                <p className="text-sm font-semibold text-white truncate">
                  {query.designation || 'Jobs'}
                  {query.location && <span className="text-dark-100 font-normal"> in {query.location}</span>}
                </p>
                {data && !loading && (
                  <p className="text-[11px] font-mono text-dark-200">
                    Found <span className="text-electric-400">{data.total_found}</span> jobs across{' '}
                    <span className="text-electric-400">{data.sources_scraped?.length || 0}</span> sources in{' '}
                    <span className="text-accent-green">{data.scrape_time_seconds}s</span>
                  </p>
                )}
              </div>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {data && !loading && (
                <button
                  onClick={handleRetry}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-dark-100 hover:text-white border border-dark-400/30 hover:border-dark-300 transition-all"
                  id="retry-search"
                >
                  <RotateCcw size={12} />
                  <span className="hidden sm:inline">Rescan</span>
                </button>
              )}
              <button
                onClick={() => setMobileFiltersOpen(true)}
                className="lg:hidden flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-dark-100 hover:text-white border border-dark-400/30 hover:border-dark-300 transition-all"
                id="open-mobile-filters"
              >
                <SlidersHorizontal size={12} />
                Filters
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Loading State */}
        {loading && (
          <LoadingState progress={progress} isLoading={loading} />
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="max-w-lg mx-auto py-16 text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl bg-accent-rose/10 border border-accent-rose/20 flex items-center justify-center mx-auto mb-4">
              <AlertTriangle size={28} className="text-accent-rose" />
            </div>
            <h2 className="text-lg font-semibold text-white mb-2">Search Failed</h2>
            <p className="text-sm text-dark-100 mb-6">{error}</p>
            <div className="flex items-center justify-center gap-3">
              <button onClick={handleRetry} className="glow-btn text-sm py-2.5 px-6">
                <RotateCcw size={14} className="mr-1.5 inline" />
                Retry
              </button>
              <button
                onClick={handleNewSearch}
                className="px-6 py-2.5 rounded-lg text-sm text-dark-100 border border-dark-400/30 hover:border-dark-300 hover:text-white transition-all"
              >
                New Search
              </button>
            </div>
          </div>
        )}

        {/* Results */}
        {data && !loading && (
          <div className="flex gap-6 animate-fade-in">
            {/* Job Cards Grid */}
            <div className="flex-1 min-w-0">
              {/* Errors from individual scrapers */}
              {data.errors && data.errors.length > 0 && (
                <div className="mb-4 p-3 rounded-lg bg-accent-amber/5 border border-accent-amber/15">
                  <p className="text-xs font-semibold text-accent-amber mb-1">
                    ⚠️ Some sources had issues:
                  </p>
                  {data.errors.map((err, i) => (
                    <p key={i} className="text-[11px] text-dark-100 font-mono">{err}</p>
                  ))}
                </div>
              )}

              {filteredJobs.length > 0 ? (
                <>
                  {/* Sort/count bar (above grid) */}
                  <div className="flex items-center justify-between mb-4">
                    <p className="text-xs text-dark-200 font-mono">
                      {filteredJobs.length} result{filteredJobs.length !== 1 ? 's' : ''}
                      {filteredJobs.length !== jobs.length && (
                        <span className="text-dark-300"> (filtered from {jobs.length})</span>
                      )}
                    </p>

                    {/* Desktop sort (inline) */}
                    <div className="hidden lg:flex items-center gap-1.5">
                      <span className="text-[10px] font-mono text-dark-300 mr-1">SORT:</span>
                      {[
                        { value: 'latest', label: 'Latest' },
                        { value: 'relevant', label: 'Relevant' },
                        { value: 'salary', label: 'Salary ↓' },
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setSortBy(option.value)}
                          className={`pill-toggle text-[10px] py-0.5 px-2 ${sortBy === option.value ? 'active' : ''}`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Cards Grid */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 stagger-in">
                    {filteredJobs.map((job, index) => (
                      <JobCard key={job.id + '-' + index} job={job} index={index} />
                    ))}
                  </div>
                </>
              ) : (
                /* Empty state */
                <div className="text-center py-20">
                  <div className="w-16 h-16 rounded-2xl bg-dark-600/50 flex items-center justify-center mx-auto mb-4">
                    <Search size={28} className="text-dark-200" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {jobs.length > 0 ? 'No matching results' : 'No jobs found'}
                  </h3>
                  <p className="text-sm text-dark-100 mb-4">
                    {jobs.length > 0
                      ? 'Try adjusting your filters to see more results.'
                      : 'Try broadening your search criteria or selecting more sources.'
                    }
                  </p>
                  {jobs.length > 0 && (
                    <button
                      onClick={resetFilters}
                      className="text-sm text-electric-400 hover:text-electric-300 font-medium transition-colors"
                    >
                      Clear all filters
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Filter Sidebar (desktop) */}
            <div className="hidden lg:block w-64 flex-shrink-0">
              <FilterSidebar
                filters={filters}
                sourceCounts={sourceCounts}
                typeCounts={typeCounts}
                onUpdateFilter={updateFilter}
                onToggleArrayFilter={toggleArrayFilter}
                onResetFilters={resetFilters}
                sortBy={sortBy}
                onSortChange={setSortBy}
                totalJobs={jobs.length}
                filteredCount={filteredJobs.length}
              />
            </div>

            {/* Filter Sidebar (mobile) */}
            <FilterSidebar
              filters={filters}
              sourceCounts={sourceCounts}
              typeCounts={typeCounts}
              onUpdateFilter={updateFilter}
              onToggleArrayFilter={toggleArrayFilter}
              onResetFilters={resetFilters}
              sortBy={sortBy}
              onSortChange={setSortBy}
              totalJobs={jobs.length}
              filteredCount={filteredJobs.length}
              isMobileOpen={mobileFiltersOpen}
              onMobileClose={() => setMobileFiltersOpen(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
