import { useState, useRef } from 'react';
import { X } from 'lucide-react';

/**
 * Tag input component for entering skills.
 * Type a skill and press Enter to add it as a tag.
 */
export default function SkillTagInput({ skills = [], onChange, placeholder = 'Type a skill and press Enter...' }) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef(null);

  const addSkill = (skill) => {
    const trimmed = skill.trim();
    if (trimmed && !skills.includes(trimmed)) {
      onChange([...skills, trimmed]);
    }
    setInputValue('');
  };

  const removeSkill = (skillToRemove) => {
    onChange(skills.filter((s) => s !== skillToRemove));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addSkill(inputValue);
    } else if (e.key === 'Backspace' && !inputValue && skills.length > 0) {
      removeSkill(skills[skills.length - 1]);
    }
  };

  // Common skill suggestions
  const suggestions = [
    'Python', 'JavaScript', 'React', 'Node.js', 'Java', 'TypeScript',
    'SQL', 'AWS', 'Docker', 'Machine Learning', 'Data Science',
    'Angular', 'Vue.js', 'Go', 'Kubernetes', 'C++',
  ].filter((s) => !skills.includes(s));

  const showSuggestions = inputValue.length === 0 && skills.length === 0;

  return (
    <div>
      <div
        className="flex flex-wrap gap-2 p-2 min-h-[44px] bg-dark-800 border border-dark-400/50 rounded-lg cursor-text focus-within:border-electric-500 focus-within:shadow-[0_0_0_3px_rgba(59,130,246,0.1)] transition-all"
        onClick={() => inputRef.current?.focus()}
      >
        {skills.map((skill) => (
          <span
            key={skill}
            className="tag group cursor-pointer"
            onClick={(e) => {
              e.stopPropagation();
              removeSkill(skill);
            }}
          >
            {skill}
            <X size={12} className="opacity-50 group-hover:opacity-100 transition-opacity" />
          </span>
        ))}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={skills.length === 0 ? placeholder : ''}
          className="flex-1 min-w-[120px] bg-transparent border-none outline-none text-sm text-slate-200 placeholder:text-dark-200"
          id="skill-tag-input"
        />
      </div>

      {/* Quick-add suggestion pills */}
      {showSuggestions && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {suggestions.slice(0, 8).map((skill) => (
            <button
              key={skill}
              type="button"
              onClick={() => addSkill(skill)}
              className="text-[11px] px-2.5 py-1 rounded-md bg-dark-600/50 text-dark-100 hover:bg-dark-500 hover:text-slate-300 border border-dark-400/30 transition-all"
            >
              + {skill}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
