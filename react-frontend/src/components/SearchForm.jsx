import { useState } from 'react';
import { Search, Crosshair, Zap } from 'lucide-react';
import SkillTagInput from './SkillTagInput';
import DualRangeSlider from './DualRangeSlider';
import SourceSelector from './SourceSelector';

/**
 * Main search form component.
 * Multi-field form with designation, location, experience, salary,
 * job type, skills, source selection, and max results.
 */

const DESIGNATION_SUGGESTIONS = [
  'Software Engineer', 'Frontend Developer', 'Backend Developer', 'Full Stack Developer',
  'Data Scientist', 'Data Analyst', 'Product Manager', 'DevOps Engineer',
  'Machine Learning Engineer', 'UI/UX Designer', 'Mobile Developer', 'Cloud Architect',
  'QA Engineer', 'Business Analyst', 'Cybersecurity Analyst', 'System Administrator',
];

const LOCATION_SUGGESTIONS = [
  'Bangalore', 'Mumbai', 'Delhi NCR', 'Hyderabad', 'Pune', 'Chennai',
  'Kolkata', 'Noida', 'Gurgaon', 'Remote',
  'New York', 'San Francisco', 'London', 'Singapore', 'Dubai',
];

const JOB_TYPE_OPTIONS = [
  { value: 'full-time', label: 'Full-time', icon: '💼' },
  { value: 'part-time', label: 'Part-time', icon: '⏰' },
  { value: 'contract', label: 'Contract', icon: '📝' },
  { value: 'internship', label: 'Internship', icon: '🎓' },
  { value: 'remote', label: 'Remote', icon: '🌐' },
];

const MAX_RESULTS_OPTIONS = [10, 25, 50, 100];

export default function SearchForm({ onSearch, isLoading = false }) {
  const [form, setForm] = useState({
    designation: '',
    location: '',
    experience_min: 0,
    experience_max: 10,
    salary_min: 0,
    salary_max: 50,
    job_type: null,
    skills: [],
    remote_ok: false,
    sources: ['all'],
    max_results: 50,
  });

  const [salaryMode, setSalaryMode] = useState('lpa'); // 'lpa' or 'usd'
  const [showDesignationSuggestions, setShowDesignationSuggestions] = useState(false);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);

  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.designation.trim()) return;

    const query = {
      designation: form.designation.trim(),
      location: form.location.trim() || 'Remote',
      experience_min: form.experience_min,
      experience_max: form.experience_max,
      salary_min: salaryMode === 'lpa' ? form.salary_min : Math.round(form.salary_min * 83),
      salary_max: salaryMode === 'lpa' ? form.salary_max : Math.round(form.salary_max * 83),
      job_type: form.job_type,
      skills: form.skills,
      remote_ok: form.remote_ok || form.job_type === 'remote',
      sources: form.sources,
      max_results: form.max_results,
    };

    onSearch(query);
  };

  const filteredDesignations = DESIGNATION_SUGGESTIONS.filter((s) =>
    s.toLowerCase().includes(form.designation.toLowerCase())
  );

  const filteredLocations = LOCATION_SUGGESTIONS.filter((s) =>
    s.toLowerCase().includes(form.location.toLowerCase())
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Row 1: Designation + Location */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Designation */}
        <div className="relative">
          <label className="block text-xs font-mono text-dark-100 uppercase tracking-widest mb-1.5">
            <Crosshair size={11} className="inline mr-1.5 text-electric-400" />
            Designation / Title
          </label>
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-200" />
            <input
              type="text"
              value={form.designation}
              onChange={(e) => {
                updateField('designation', e.target.value);
                setShowDesignationSuggestions(e.target.value.length > 0);
              }}
              onFocus={() => setShowDesignationSuggestions(true)}
              onBlur={() => setTimeout(() => setShowDesignationSuggestions(false), 200)}
              placeholder="e.g. Software Engineer"
              className="input-field pl-10 h-11"
              required
              id="search-designation"
            />
          </div>
          {/* Autocomplete dropdown */}
          {showDesignationSuggestions && filteredDesignations.length > 0 && (
            <div className="absolute z-30 w-full mt-1 bg-dark-700 border border-dark-400/50 rounded-lg shadow-2xl shadow-black/50 max-h-48 overflow-y-auto">
              {filteredDesignations.slice(0, 8).map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onMouseDown={() => {
                    updateField('designation', suggestion);
                    setShowDesignationSuggestions(false);
                  }}
                  className="w-full text-left px-4 py-2.5 text-sm text-slate-300 hover:bg-dark-600 hover:text-white transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Location */}
        <div className="relative">
          <label className="block text-xs font-mono text-dark-100 uppercase tracking-widest mb-1.5">
            <span className="inline mr-1.5">📍</span>
            Location
          </label>
          <input
            type="text"
            value={form.location}
            onChange={(e) => {
              updateField('location', e.target.value);
              setShowLocationSuggestions(e.target.value.length > 0);
            }}
            onFocus={() => setShowLocationSuggestions(true)}
            onBlur={() => setTimeout(() => setShowLocationSuggestions(false), 200)}
            placeholder="e.g. Bangalore, Mumbai, Remote"
            className="input-field h-11"
            id="search-location"
          />
          {showLocationSuggestions && filteredLocations.length > 0 && (
            <div className="absolute z-30 w-full mt-1 bg-dark-700 border border-dark-400/50 rounded-lg shadow-2xl shadow-black/50 max-h-48 overflow-y-auto">
              {filteredLocations.slice(0, 8).map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onMouseDown={() => {
                    updateField('location', suggestion);
                    setShowLocationSuggestions(false);
                  }}
                  className="w-full text-left px-4 py-2.5 text-sm text-slate-300 hover:bg-dark-600 hover:text-white transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Row 2: Experience + Salary sliders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <DualRangeSlider
          label="Experience"
          min={0}
          max={15}
          step={1}
          minValue={form.experience_min}
          maxValue={form.experience_max}
          onChange={({ min, max }) => {
            updateField('experience_min', min);
            updateField('experience_max', max);
          }}
          formatLabel={(v) => `${v}y`}
        />

        <div>
          <div className="flex items-center justify-between mb-1">
            <div /> {/* Spacer — DualRangeSlider renders its own label */}
            <div className="flex rounded-md overflow-hidden border border-dark-400/30">
              <button
                type="button"
                onClick={() => setSalaryMode('lpa')}
                className={`text-[10px] font-mono px-2 py-0.5 transition-all ${
                  salaryMode === 'lpa' ? 'bg-electric-500/20 text-electric-400' : 'text-dark-200 hover:text-slate-300'
                }`}
              >
                ₹ LPA
              </button>
              <button
                type="button"
                onClick={() => setSalaryMode('usd')}
                className={`text-[10px] font-mono px-2 py-0.5 transition-all ${
                  salaryMode === 'usd' ? 'bg-electric-500/20 text-electric-400' : 'text-dark-200 hover:text-slate-300'
                }`}
              >
                $ USD
              </button>
            </div>
          </div>
          <DualRangeSlider
            label="Salary Range"
            min={0}
            max={salaryMode === 'lpa' ? 50 : 200}
            step={salaryMode === 'lpa' ? 1 : 10}
            minValue={form.salary_min}
            maxValue={form.salary_max > (salaryMode === 'lpa' ? 50 : 200) ? (salaryMode === 'lpa' ? 50 : 200) : form.salary_max}
            onChange={({ min, max }) => {
              updateField('salary_min', min);
              updateField('salary_max', max);
            }}
            formatLabel={(v) => salaryMode === 'lpa' ? `${v}` : `${v}k`}
            unit={salaryMode === 'lpa' ? 'LPA' : 'USD/yr'}
          />
        </div>
      </div>

      {/* Row 3: Job Type pills */}
      <div>
        <label className="block text-xs font-mono text-dark-100 uppercase tracking-widest mb-2">
          Job Type
        </label>
        <div className="flex flex-wrap gap-2">
          {JOB_TYPE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                if (form.job_type === option.value) {
                  updateField('job_type', null);
                  if (option.value === 'remote') updateField('remote_ok', false);
                } else {
                  updateField('job_type', option.value);
                  if (option.value === 'remote') updateField('remote_ok', true);
                }
              }}
              className={`pill-toggle ${form.job_type === option.value ? 'active' : ''}`}
              id={`jobtype-${option.value}`}
            >
              <span className="mr-1">{option.icon}</span>
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Row 4: Skills */}
      <div>
        <label className="block text-xs font-mono text-dark-100 uppercase tracking-widest mb-1.5">
          🛠️ Skills
        </label>
        <SkillTagInput
          skills={form.skills}
          onChange={(skills) => updateField('skills', skills)}
        />
      </div>

      {/* Row 5: Sources */}
      <div>
        <label className="block text-xs font-mono text-dark-100 uppercase tracking-widest mb-2">
          📡 Sources
        </label>
        <SourceSelector
          selected={form.sources}
          onChange={(sources) => updateField('sources', sources)}
        />
      </div>

      {/* Row 6: Max Results */}
      <div>
        <label className="block text-xs font-mono text-dark-100 uppercase tracking-widest mb-2">
          Max Results
        </label>
        <div className="flex gap-2">
          {MAX_RESULTS_OPTIONS.map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => updateField('max_results', value)}
              className={`pill-toggle font-mono text-xs ${form.max_results === value ? 'active' : ''}`}
              id={`max-results-${value}`}
            >
              {value}
            </button>
          ))}
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !form.designation.trim()}
        className="glow-btn w-full text-base py-4 flex items-center justify-center gap-3 font-bold tracking-wide"
        id="hunt-jobs-btn"
      >
        {isLoading ? (
          <>
            <div className="loader-pulse">
              <span /><span /><span />
            </div>
            Scanning...
          </>
        ) : (
          <>
            <Zap size={20} className="fill-current" />
            HUNT JOBS
          </>
        )}
      </button>
    </form>
  );
}
