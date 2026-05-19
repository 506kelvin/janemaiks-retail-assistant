import { useEffect, useState, useRef } from 'react';

function AnimatedCounter({ value, duration = 600 }) {
  const [display, setDisplay] = useState(0);
  const startRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    if (typeof value !== 'number') return;
    startRef.current = null;
    const startVal = display;

    const step = (timestamp) => {
      if (!startRef.current) startRef.current = timestamp;
      const progress = Math.min((timestamp - startRef.current) / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(startVal + (value - startVal) * easeOut));
      if (progress < 1) rafRef.current = requestAnimationFrame(step);
    };

    rafRef.current = requestAnimationFrame(step);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [value, duration]);

  if (typeof value !== 'number') return value;
  return display.toLocaleString();
}

const iconColors = {
  blue: 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400',
  green: 'bg-green-50 dark:bg-green-500/10 text-green-600 dark:text-green-400',
  amber: 'bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400',
  purple: 'bg-purple-50 dark:bg-purple-500/10 text-purple-600 dark:text-purple-400',
  red: 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400',
  primary: 'bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400',
};

export default function StatCard({ icon: Icon, label, value, color = 'blue', trend, trendUp, subtitle, onClick }) {
  const colorCls = iconColors[color] || iconColors.blue;

  return (
    <div
      className={`stat-card ${onClick ? 'cursor-pointer hover:shadow-card-hover' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter') onClick(); } : undefined}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="stat-label">{label}</p>
          <p className="stat-value">
            {typeof value === 'number' ? <AnimatedCounter value={value} /> : value}
          </p>
          {trend && (
            <p className={`stat-trend ${trendUp !== undefined ? (trendUp ? 'text-status-success' : 'text-status-low') : 'text-gray-400'}`}>
              {trendUp !== undefined && (trendUp ? '↑ ' : '↓ ')}
              {trend}
            </p>
          )}
        </div>
        <div className={`stat-icon ${colorCls} flex-shrink-0 ml-3`}>
          <Icon size={22} />
        </div>
      </div>
      {subtitle && <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">{subtitle}</p>}
    </div>
  );
}
