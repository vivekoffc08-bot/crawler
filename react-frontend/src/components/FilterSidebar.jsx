import { Search, X, SlidersHorizontal, Wifi } from 'lucide-react';

/**
 * Filter sidebar for the results page.
 * Provides client-side filtering of already-fetched results.
 */

const SOURCE_META = {
  linkedin: { name: 'LinkedIn', color: '#0A66C2' },
  indeed: { name: 'Indeed', color: '#2164F3' },
  naukri: { name: 'Naukri', color: '#4A90D9' },
  glassdoor: { name: 'Glassdoor', color: '#0CAA41' },
  wellfound: { name: 'Wellfound', color: '#CBD5E1' },
  internshala: { name: 'Internshala', color: '#00A5EC' },
  shine: { name: 'Shine', color: '#E85D24' },
  monster: { name: 'Monster India', color: '#6E45A5' },
};

const JOB_TYPES = [
  { value: 'full-time', label: 'Full-time' },
  { value: 'part-time', label: 'Part-time' },
  { value: 'contract', label: 'Contract' },
  { value: 'internship', label: 'Internship' },
  { value: 'remote', label: 'Remote' },
];

export default function FilterSidebar({
  filters,
  sourceCounts = {},
  typeCounts = {},
  onUpdateFilter,
  onToggleArrayFilter,
  onResetFilters,
  sortBy,
  onSortChange,
  totalJobs = 0,
  filteredCount = 0,
  isMobileOpen = false,
  onMobileClose,
}) {
  const hasActiveFilters =
    filters.sources.length > 0 ||
    filters.jobTypes.length > 0 ||
    filters.isRemote !== null ||
    filters.searchText;

  return (
    <>
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`
          fixed lg:sticky top-14 right-0 z-50 lg:z-0
          w-72 lg:w-64 h-[calc(100vh-56px)] lg:h-auto lg:max-h-[calc(100vh-80px)]
          bg-dark-800/95 lg:bg-transparent backdrop-blur-xl lg:backdrop-blur-none
          border-l lg:border-l-0 border-dark-400/30
          overflow-y-auto
          transition-transform duration-300
          ${isMobileOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
          p-4 space-y-5
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SlidersHorizontal size={14} className="text-electric-400" />
            <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-widest">Filters</h3>
          </div>
          <div className="flex items-center gap-2">
            {hasActiveFilters && (
              <button
                onClick={onResetFilters}
                className="text-[10px] text-accent-rose hover:text-accent-rose/80 font-medium transition-colors"
                id="reset-filters-btn"
              >
                Reset
              </button>
            )}
            <button
              onClick={onMobileClose}
              className="lg:hidden p-1 text-dark-200 hover:text-white"
              id="close-filters-btn"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Result count */}
        <div className="text-xs text-dark-200 font-mono">
          Showing {filteredCount} of {totalJobs} results
        </div>

        {/* Search within results */}
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-200" />
          <input
            type="text"
            placeholder="Filter results..."
            value={filters.searchText}
            onChange={(e) => onUpdateFilter('searchText', e.target.value)}
            className="input-field pl-9 text-xs h-9"
            id="filter-search-input"
          />
        </div>

        {/* Sort By */}
        <div>
          <h4 className="text-[10px] font-mono text-dark-200 uppercase tracking-widest mb-2">Sort By</h4>
          <div className="flex flex-wrap gap-1.5">
            {[
              { value: 'latest', label: 'Latest' },
              { value: 'relevant', label: 'Relevant' },
              { value: 'salary', label: 'Salary ↓' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => onSortChange(option.value)}
                className={`pill-toggle text-[11px] py-1 px-3 ${sortBy === option.value ? 'active' : ''}`}
                id={`sort-${option.value}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Source Filter */}
        {Object.keys(sourceCounts).length > 0 && (
          <div>
            <h4 className="text-[10px] font-mono text-dark-200 uppercase tracking-widest mb-2">Sources</h4>
            <div className="space-y-1">
              {Object.entries(sourceCounts).map(([source, count]) => {
                const meta = SOURCE_META[source] || { name: source, color: '#3b82f6' };
                const isActive = filters.sources.includes(source);
                return (
                  <button
                    key={source}
                    onClick={() => onToggleArrayFilter('sources', source)}
                    className={`w-full flex items-center justify-between py-1.5 px-2.5 rounded-md text-xs transition-all ${
                      isActive
                        ? 'bg-dark-600/60 text-slate-300'
                        : 'text-dark-100 hover:bg-dark-600/30 hover:text-slate-300'
                    }`}
                    id={`filter-source-${source}`}
                  >
                    <span className="flex items-center gap-2">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: isActive ? meta.color : '#45456a' }}
                      />
                      {meta.name}
                    </span>
                    <span className="font-mono text-dark-200">{count}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Job Type Filter */}
        {Object.keys(typeCounts).length > 0 && (
          <div>
            <h4 className="text-[10px] font-mono text-dark-200 uppercase tracking-widest mb-2">Job Type</h4>
            <div className="flex flex-wrap gap-1.5">
              {JOB_TYPES.filter((jt) => typeCounts[jt.value]).map((jt) => (
                <button
                  key={jt.value}
                  onClick={() => onToggleArrayFilter('jobTypes', jt.value)}
                  className={`pill-toggle text-[11px] py-1 px-2.5 ${
                    filters.jobTypes.includes(jt.value) ? 'active' : ''
                  }`}
                  id={`filter-type-${jt.value}`}
                >
                  {jt.label}
                  <span className="ml-1 text-dark-200 font-mono">{typeCounts[jt.value]}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Remote Filter */}
        <div>
          <h4 className="text-[10px] font-mono text-dark-200 uppercase tracking-widest mb-2">Remote</h4>
          <div className="flex gap-1.5">
            <button
              onClick={() => onUpdateFilter('isRemote', filters.isRemote === null ? true : null)}
              className={`pill-toggle text-[11px] py-1 px-3 ${filters.isRemote === true ? 'active' : ''}`}
              id="filter-remote-yes"
            >
              <Wifi size={11} className="mr-1" />
              Remote Only
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
