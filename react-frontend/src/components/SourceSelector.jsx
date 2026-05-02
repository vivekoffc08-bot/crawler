import { useState, useEffect } from 'react';
import { getSources } from '../api/jobs';

/**
 * Source selector with site logos and colored checkboxes.
 * Fetches available sources from the API.
 */

// Fallback source data (used if API is unavailable)
const FALLBACK_SOURCES = [
  { id: 'linkedin', name: 'LinkedIn', region: 'global', color: '#0A66C2' },
  { id: 'indeed', name: 'Indeed', region: 'global', color: '#2164F3' },
  { id: 'naukri', name: 'Naukri', region: 'india', color: '#4A90D9' },
  { id: 'glassdoor', name: 'Glassdoor', region: 'global', color: '#0CAA41' },
  { id: 'wellfound', name: 'Wellfound', region: 'global', color: '#000000' },
  { id: 'internshala', name: 'Internshala', region: 'india', color: '#00A5EC' },
  { id: 'shine', name: 'Shine', region: 'india', color: '#E85D24' },
  { id: 'monster', name: 'Monster India', region: 'india', color: '#6E45A5' },
];

export default function SourceSelector({ selected = [], onChange }) {
  const [sources, setSources] = useState(FALLBACK_SOURCES);
  const [selectAll, setSelectAll] = useState(true);

  useEffect(() => {
    getSources()
      .then((data) => {
        if (data?.sources?.length) {
          setSources(data.sources);
        }
      })
      .catch(() => {
        // Use fallback silently
      });
  }, []);

  const handleToggle = (sourceId) => {
    if (selectAll) {
      // Switch from "all" to specific selection
      setSelectAll(false);
      const allExcept = sources.map((s) => s.id).filter((id) => id !== sourceId);
      onChange(allExcept);
    } else {
      const isSelected = selected.includes(sourceId);
      const newSelected = isSelected
        ? selected.filter((id) => id !== sourceId)
        : [...selected, sourceId];

      // If all are selected, switch back to "all" mode
      if (newSelected.length === sources.length) {
        setSelectAll(true);
        onChange(['all']);
      } else {
        onChange(newSelected);
      }
    }
  };

  const handleSelectAll = () => {
    setSelectAll(true);
    onChange(['all']);
  };

  const isSelected = (sourceId) => {
    return selectAll || selected.includes(sourceId);
  };

  // Group sources by region
  const globalSources = sources.filter((s) => s.region === 'global');
  const indiaSources = sources.filter((s) => s.region === 'india');

  return (
    <div className="space-y-3">
      {/* Select All toggle */}
      <button
        type="button"
        onClick={handleSelectAll}
        className={`w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
          selectAll
            ? 'bg-electric-500/15 border border-electric-500/40 text-electric-400'
            : 'bg-dark-700/50 border border-dark-400/30 text-dark-200 hover:border-dark-300'
        }`}
        id="source-select-all"
      >
        <span className={`w-3 h-3 rounded-sm border-2 flex items-center justify-center transition-all ${
          selectAll ? 'border-electric-500 bg-electric-500' : 'border-dark-300'
        }`}>
          {selectAll && (
            <svg width="8" height="8" viewBox="0 0 12 12" fill="none">
              <path d="M2 6L5 9L10 3" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </span>
        Search All Sources
      </button>

      {/* Global Sources */}
      <div>
        <p className="text-[10px] font-mono text-dark-200 uppercase tracking-widest mb-2">Global</p>
        <div className="grid grid-cols-2 gap-1.5">
          {globalSources.map((source) => (
            <SourceItem
              key={source.id}
              source={source}
              checked={isSelected(source.id)}
              onToggle={() => handleToggle(source.id)}
            />
          ))}
        </div>
      </div>

      {/* India Sources */}
      <div>
        <p className="text-[10px] font-mono text-dark-200 uppercase tracking-widest mb-2">India</p>
        <div className="grid grid-cols-2 gap-1.5">
          {indiaSources.map((source) => (
            <SourceItem
              key={source.id}
              source={source}
              checked={isSelected(source.id)}
              onToggle={() => handleToggle(source.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function SourceItem({ source, checked, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`flex items-center gap-2 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
        checked
          ? 'bg-dark-600/60 border border-dark-300/50 text-slate-300'
          : 'bg-dark-700/30 border border-dark-500/20 text-dark-200 hover:bg-dark-600/30'
      }`}
      id={`source-${source.id}`}
    >
      <span
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{
          backgroundColor: checked ? source.color : '#45456a',
          boxShadow: checked ? `0 0 6px ${source.color}40` : 'none',
        }}
      />
      <span className="truncate">{source.name}</span>
    </button>
  );
}
