import { Check, Loader2, AlertCircle, Clock } from 'lucide-react';

/**
 * Loading state with per-source progress indicators.
 * Shows "Scraping LinkedIn... ✓", "Scraping Naukri... ⏳" etc.
 */

const SOURCE_META = {
  linkedin: { name: 'LinkedIn', color: '#0A66C2' },
  indeed: { name: 'Indeed', color: '#2164F3' },
  naukri: { name: 'Naukri', color: '#4A90D9' },
  glassdoor: { name: 'Glassdoor', color: '#0CAA41' },
  wellfound: { name: 'Wellfound', color: '#E8E8E8' },
  internshala: { name: 'Internshala', color: '#00A5EC' },
  shine: { name: 'Shine', color: '#E85D24' },
  monster: { name: 'Monster India', color: '#6E45A5' },
};

export default function LoadingState({ progress = {}, isLoading = true }) {
  const sources = Object.keys(progress);

  if (sources.length === 0 && isLoading) {
    // Initial state — no progress yet
    return (
      <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
        <div className="relative mb-6">
          {/* Spinning radar */}
          <div className="w-24 h-24 rounded-full border-2 border-dark-400/30 relative">
            <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-electric-500 animate-spin" />
            <div className="absolute inset-2 rounded-full border border-dark-400/20" />
            <div className="absolute inset-4 rounded-full border border-dark-400/10" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-electric-500 animate-pulse" />
            </div>
          </div>
          {/* Scan line */}
          <div className="absolute top-1/2 left-1/2 w-12 h-0.5 bg-gradient-to-r from-electric-500/80 to-transparent origin-left animate-spin" style={{ animationDuration: '2s' }} />
        </div>
        <p className="text-sm font-mono text-electric-400 mb-2">INITIALIZING SCAN</p>
        <p className="text-xs text-dark-200">Connecting to job sources...</p>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto py-12 animate-fade-in">
      <div className="text-center mb-8">
        <div className="loader-pulse justify-center mb-4">
          <span /><span /><span />
        </div>
        <p className="text-sm font-mono text-electric-400">SCANNING JOB BOARDS</p>
        <p className="text-xs text-dark-200 mt-1">Aggregating results in real-time...</p>
      </div>

      <div className="space-y-2">
        {sources.map((sourceId) => {
          const prog = progress[sourceId];
          const meta = SOURCE_META[sourceId] || { name: sourceId, color: '#3b82f6' };

          return (
            <div
              key={sourceId}
              className={`glass-card p-3 flex items-center gap-3 transition-all duration-300 ${
                prog.status === 'done' ? 'border-accent-green/20' :
                prog.status === 'error' ? 'border-accent-rose/20' :
                'border-dark-400/30'
              }`}
            >
              {/* Status icon */}
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{
                backgroundColor: `${meta.color}15`,
              }}>
                {prog.status === 'done' && (
                  <Check size={16} className="text-accent-green" />
                )}
                {prog.status === 'scraping' && (
                  <Loader2 size={16} className="text-electric-400 animate-spin" />
                )}
                {prog.status === 'pending' && (
                  <Clock size={14} className="text-dark-200" />
                )}
                {prog.status === 'error' && (
                  <AlertCircle size={16} className="text-accent-rose" />
                )}
              </div>

              {/* Source name + message */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-300">
                  {meta.name}
                </p>
                <p className={`text-xs truncate ${
                  prog.status === 'done' ? 'text-accent-green/70' :
                  prog.status === 'error' ? 'text-accent-rose/70' :
                  'text-dark-200'
                }`}>
                  {prog.message || 'Waiting...'}
                </p>
              </div>

              {/* Job count badge */}
              {prog.status === 'done' && prog.count > 0 && (
                <span className="text-xs font-mono font-bold text-accent-green bg-accent-green/10 px-2 py-0.5 rounded">
                  +{prog.count}
                </span>
              )}

              {/* Scan bar animation */}
              {prog.status === 'scraping' && (
                <div className="w-16 h-1 bg-dark-600 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full animate-scan"
                    style={{ backgroundColor: meta.color, width: '40%' }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
