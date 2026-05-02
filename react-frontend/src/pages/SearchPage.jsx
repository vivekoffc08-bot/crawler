import { useNavigate } from 'react-router-dom';
import { Radar, Zap, Globe, Shield, Database, ArrowRight } from 'lucide-react';
import SearchForm from '../components/SearchForm';
import { useJobSearch } from '../hooks/useJobSearch';

/**
 * Search Page — the main landing page with the search form.
 * "Command Center" aesthetic with grid background and hero section.
 */
export default function SearchPage() {
  const navigate = useNavigate();
  const { search, loading } = useJobSearch();

  const handleSearch = async (query) => {
    // Store query in sessionStorage for the results page
    sessionStorage.setItem('jobhunt_query', JSON.stringify(query));
    // Navigate to results page (search is triggered there)
    navigate('/results');
  };

  return (
    <div className="min-h-[calc(100vh-56px)]">
      {/* Hero Section */}
      <section className="relative py-12 sm:py-16 lg:py-20 overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 pointer-events-none">
          {/* Radial glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-electric-500/5 rounded-full blur-[120px]" />
          <div className="absolute top-20 right-1/4 w-[300px] h-[300px] bg-accent-cyan/3 rounded-full blur-[100px]" />
          {/* Grid dots */}
          <div className="absolute top-10 left-10 w-2 h-2 rounded-full bg-electric-500/20 animate-pulse" />
          <div className="absolute top-32 right-20 w-1.5 h-1.5 rounded-full bg-accent-cyan/30 animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute bottom-20 left-1/4 w-1 h-1 rounded-full bg-accent-green/30 animate-pulse" style={{ animationDelay: '2s' }} />
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 relative">
          {/* Status bar */}
          <div className="flex items-center justify-center gap-3 mb-8">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-dark-400/30 bg-dark-800/50">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
              <span className="text-[10px] font-mono text-dark-100 uppercase tracking-widest">8 Sources Online</span>
            </div>
          </div>

          {/* Title */}
          <div className="text-center mb-10">
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 tracking-tight">
              <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Job Hunt
              </span>
              <span className="text-electric-500"> Command Center</span>
            </h1>
            <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Aggregate job postings from <span className="text-electric-400 font-medium">8+ job boards</span> in seconds.
              Direct links. No middleman. No sign-ups.
            </p>
          </div>

          {/* Feature badges */}
          <div className="flex flex-wrap items-center justify-center gap-3 mb-10">
            {[
              { icon: Globe, text: 'Multi-Source', desc: '8 boards' },
              { icon: Zap, text: 'Real-Time', desc: 'Live scan' },
              { icon: Database, text: 'Deduplication', desc: 'Smart merge' },
              { icon: Shield, text: 'Direct Links', desc: 'No redirect' },
            ].map(({ icon: Icon, text, desc }) => (
              <div
                key={text}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-dark-700/40 border border-dark-400/20"
              >
                <Icon size={14} className="text-electric-400" />
                <div>
                  <p className="text-xs font-medium text-slate-300">{text}</p>
                  <p className="text-[10px] text-dark-200 font-mono">{desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Search Form Card */}
          <div className="glass-card p-6 sm:p-8 relative">
            {/* Corner decorations */}
            <div className="absolute top-0 left-0 w-8 h-8 border-t border-l border-electric-500/30 rounded-tl-xl" />
            <div className="absolute top-0 right-0 w-8 h-8 border-t border-r border-electric-500/30 rounded-tr-xl" />
            <div className="absolute bottom-0 left-0 w-8 h-8 border-b border-l border-electric-500/30 rounded-bl-xl" />
            <div className="absolute bottom-0 right-0 w-8 h-8 border-b border-r border-electric-500/30 rounded-br-xl" />

            <SearchForm onSearch={handleSearch} isLoading={loading} />
          </div>

          {/* Source strip */}
          <div className="mt-8 text-center">
            <p className="text-[10px] font-mono text-dark-200 uppercase tracking-widest mb-3">
              Aggregating from
            </p>
            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-dark-100">
              {['LinkedIn', 'Indeed', 'Naukri', 'Glassdoor', 'Wellfound', 'Internshala', 'Shine', 'Monster'].map((name) => (
                <span key={name} className="flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-dark-300" />
                  {name}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-center text-xs font-mono text-dark-200 uppercase tracking-[0.2em] mb-10">
            How It Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                step: '01',
                title: 'Define Target',
                desc: 'Set your designation, location, experience, salary range, and preferred sources.',
                color: 'from-electric-500/10 to-electric-500/5',
                borderColor: 'border-electric-500/15',
              },
              {
                step: '02',
                title: 'Parallel Scan',
                desc: 'Our engine scrapes 8+ job boards simultaneously with real-time progress tracking.',
                color: 'from-accent-cyan/10 to-accent-cyan/5',
                borderColor: 'border-accent-cyan/15',
              },
              {
                step: '03',
                title: 'Direct Links',
                desc: 'Get deduplicated results with direct apply links — no middleman, no sign-ups required.',
                color: 'from-accent-green/10 to-accent-green/5',
                borderColor: 'border-accent-green/15',
              },
            ].map((item) => (
              <div
                key={item.step}
                className={`glass-card p-5 bg-gradient-to-b ${item.color} ${item.borderColor} group`}
              >
                <span className="text-2xl font-bold font-mono text-dark-300 group-hover:text-dark-200 transition-colors">
                  {item.step}
                </span>
                <h3 className="text-sm font-semibold text-white mt-2 mb-1">{item.title}</h3>
                <p className="text-xs text-dark-100 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
