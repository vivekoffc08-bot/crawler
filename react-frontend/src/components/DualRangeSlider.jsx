import { useState, useCallback } from 'react';

/**
 * Dual range slider component for selecting min-max ranges.
 * Used for experience and salary filters.
 */
export default function DualRangeSlider({
  min = 0,
  max = 100,
  step = 1,
  minValue,
  maxValue,
  onChange,
  formatLabel = (v) => v,
  label = '',
  unit = '',
}) {
  const [localMin, setLocalMin] = useState(minValue ?? min);
  const [localMax, setLocalMax] = useState(maxValue ?? max);

  const handleMinChange = useCallback((e) => {
    const value = Math.min(Number(e.target.value), localMax - step);
    setLocalMin(value);
    onChange?.({ min: value, max: localMax });
  }, [localMax, step, onChange]);

  const handleMaxChange = useCallback((e) => {
    const value = Math.max(Number(e.target.value), localMin + step);
    setLocalMax(value);
    onChange?.({ min: localMin, max: value });
  }, [localMin, step, onChange]);

  // Calculate track fill percentage
  const minPercent = ((localMin - min) / (max - min)) * 100;
  const maxPercent = ((localMax - min) / (max - min)) * 100;

  return (
    <div className="space-y-3">
      {label && (
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</span>
          <span className="text-sm font-mono font-semibold text-electric-400">
            {formatLabel(localMin)} — {formatLabel(localMax)} {unit}
          </span>
        </div>
      )}

      <div className="relative h-6 flex items-center">
        {/* Track background */}
        <div className="absolute w-full h-1 bg-dark-600 rounded-full" />

        {/* Active track */}
        <div
          className="absolute h-1 bg-gradient-to-r from-electric-600 to-electric-400 rounded-full"
          style={{
            left: `${minPercent}%`,
            width: `${maxPercent - minPercent}%`,
          }}
        />

        {/* Min slider */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localMin}
          onChange={handleMinChange}
          className="absolute w-full appearance-none bg-transparent pointer-events-none z-10
            [&::-webkit-slider-thumb]:pointer-events-auto
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-electric-500
            [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-dark-900
            [&::-webkit-slider-thumb]:shadow-[0_0_8px_rgba(59,130,246,0.5)]
            [&::-webkit-slider-thumb]:cursor-pointer
            [&::-webkit-slider-thumb]:transition-shadow
            [&::-webkit-slider-thumb]:hover:shadow-[0_0_16px_rgba(59,130,246,0.7)]"
          id={`range-min-${label}`}
        />

        {/* Max slider */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localMax}
          onChange={handleMaxChange}
          className="absolute w-full appearance-none bg-transparent pointer-events-none z-20
            [&::-webkit-slider-thumb]:pointer-events-auto
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-accent-cyan
            [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-dark-900
            [&::-webkit-slider-thumb]:shadow-[0_0_8px_rgba(6,182,212,0.5)]
            [&::-webkit-slider-thumb]:cursor-pointer
            [&::-webkit-slider-thumb]:transition-shadow
            [&::-webkit-slider-thumb]:hover:shadow-[0_0_16px_rgba(6,182,212,0.7)]"
          id={`range-max-${label}`}
        />
      </div>

      {/* Min/Max labels */}
      <div className="flex justify-between text-[10px] font-mono text-dark-200">
        <span>{formatLabel(min)}</span>
        <span>{formatLabel(max)}</span>
      </div>
    </div>
  );
}
