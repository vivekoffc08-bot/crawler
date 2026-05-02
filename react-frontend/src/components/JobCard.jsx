import { formatDistanceToNow } from 'date-fns';
import { ExternalLink, MapPin, Building2, Clock, Briefcase, TrendingUp } from 'lucide-react';

/**
 * Job posting card component.
 * Shows title, company, location, salary, skills, source badge, and a direct "View Job" link.
 */

const SOURCE_COLORS = {
  linkedin: { bg: 'rgba(10,102,194,0.12)', text: '#60a5fa', border: 'rgba(10,102,194,0.25)' },
  indeed: { bg: 'rgba(33,100,243,0.12)', text: '#60a5fa', border: 'rgba(33,100,243,0.25)' },
  naukri: { bg: 'rgba(74,144,217,0.12)', text: '#7cb8f7', border: 'rgba(74,144,217,0.25)' },
  glassdoor: { bg: 'rgba(12,170,65,0.12)', text: '#34d399', border: 'rgba(12,170,65,0.25)' },
  wellfound: { bg: 'rgba(200,200,200,0.08)', text: '#cbd5e1', border: 'rgba(200,200,200,0.2)' },
  internshala: { bg: 'rgba(0,165,236,0.12)', text: '#38bdf8', border: 'rgba(0,165,236,0.25)' },
  shine: { bg: 'rgba(232,93,36,0.12)', text: '#fb923c', border: 'rgba(232,93,36,0.25)' },
  monster: { bg: 'rgba(110,69,165,0.12)', text: '#a78bfa', border: 'rgba(110,69,165,0.25)' },
};

export default function JobCard({ job, index = 0 }) {
  const colors = SOURCE_COLORS[job.source] || SOURCE_COLORS.linkedin;

  // Format posted date
  let postedText = '';
  if (job.posted_date) {
    try {
      postedText = formatDistanceToNow(new Date(job.posted_date), { addSuffix: true });
    } catch {
      postedText = '';
    }
  }

  // Limit displayed skills
  const displaySkills = (job.skills_required || []).slice(0, 5);
  const extraSkills = (job.skills_required || []).length - 5;

  return (
    <div
      className="glass-card group p-5 flex flex-col gap-3 relative overflow-hidden hover:translate-y-[-2px] transition-all duration-300"
      style={{ animationDelay: `${index * 0.05}s` }}
      id={`job-card-${job.id}`}
    >
      {/* Top row: source badge + confidence + remote */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {/* Source badge */}
          <span
            className="source-badge"
            style={{
              backgroundColor: colors.bg,
              color: colors.text,
              border: `1px solid ${colors.border}`,
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: colors.text }}
            />
            {job.source}
          </span>

          {/* Remote badge */}
          {job.is_remote && (
            <span className="source-badge bg-accent-green/10 text-accent-green border border-accent-green/20">
              🌐 Remote
            </span>
          )}
        </div>

        {/* Confidence indicator */}
        {job.confidence_score > 1 && (
          <div className="flex items-center gap-1.5" title={`Found on ${job.confidence_score} sites`}>
            <TrendingUp size={12} className="text-accent-green" />
            <div className="confidence-dots">
              {[1, 2, 3].map((i) => (
                <span
                  key={i}
                  className={`confidence-dot ${i <= job.confidence_score ? 'active' : ''}`}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Job Title */}
      <h3 className="text-base font-semibold text-white leading-snug group-hover:text-electric-400 transition-colors line-clamp-2">
        {job.title}
      </h3>

      {/* Company + Location */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-400">
        <span className="flex items-center gap-1.5">
          <Building2 size={13} className="text-dark-200" />
          {job.company}
        </span>
        <span className="flex items-center gap-1.5">
          <MapPin size={13} className="text-dark-200" />
          {job.location}
        </span>
      </div>

      {/* Salary + Experience row */}
      <div className="flex flex-wrap items-center gap-3">
        {job.salary_range && (
          <span className="flex items-center gap-1.5 text-xs font-medium text-accent-green bg-accent-green/8 border border-accent-green/15 px-2.5 py-1 rounded-md">
            💰 {job.salary_range}
          </span>
        )}
        {job.experience_required && (
          <span className="flex items-center gap-1.5 text-xs text-slate-400 bg-dark-600/50 px-2.5 py-1 rounded-md">
            <Briefcase size={11} />
            {job.experience_required}
          </span>
        )}
        {job.job_type && (
          <span className="text-xs text-dark-100 bg-dark-600/40 px-2 py-1 rounded-md capitalize">
            {job.job_type}
          </span>
        )}
      </div>

      {/* Skills */}
      {displaySkills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {displaySkills.map((skill) => (
            <span key={skill} className="tag text-[11px]">
              {skill}
            </span>
          ))}
          {extraSkills > 0 && (
            <span className="text-[11px] px-2 py-0.5 text-dark-200 font-mono">
              +{extraSkills} more
            </span>
          )}
        </div>
      )}

      {/* Description snippet */}
      {job.description_snippet && (
        <p className="text-xs text-dark-100 leading-relaxed line-clamp-2">
          {job.description_snippet}
        </p>
      )}

      {/* Bottom row: posted date + View Job button */}
      <div className="flex items-center justify-between mt-auto pt-3 border-t border-dark-400/20">
        {postedText ? (
          <span className="flex items-center gap-1.5 text-xs text-dark-200">
            <Clock size={12} />
            {postedText}
          </span>
        ) : (
          <span />
        )}

        <a
          href={job.apply_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold
            bg-electric-500/10 text-electric-400 border border-electric-500/20
            hover:bg-electric-500/20 hover:border-electric-500/40 hover:shadow-[0_0_16px_rgba(59,130,246,0.15)]
            transition-all duration-200 group/btn"
          id={`view-job-${job.id}`}
        >
          View Job
          <ExternalLink size={12} className="group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
        </a>
      </div>

      {/* Hover glow line at top */}
      <div
        className="absolute top-0 left-0 right-0 h-px opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          background: `linear-gradient(90deg, transparent, ${colors.text}, transparent)`,
        }}
      />
    </div>
  );
}
