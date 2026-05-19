import { Store } from 'lucide-react';

export function LogoFull({ className = '', size = 'default' }) {
  const sizes = {
    small: { icon: 16, text: 'text-sm', sub: 'text-xs' },
    default: { icon: 20, text: 'text-base', sub: 'text-xs' },
    large: { icon: 28, text: 'text-2xl', sub: 'text-sm' },
  };
  const s = sizes[size] || sizes.default;

  return (
    <div className={`flex items-center gap-2.5 group ${className}`}>
      <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 text-white font-bold shadow-md shadow-primary-500/20 group-hover:shadow-primary-500/30 transition-all duration-300">
        <span className="text-sm font-extrabold tracking-tight">JM</span>
        <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-accent-500 border-2 border-white dark:border-dark-card" />
      </div>
      <div className="leading-tight">
        <div className={`font-bold ${s.text} text-gray-900 dark:text-dark-text tracking-tight`}>
          Jane<span className="text-primary-500">Maiks</span>
        </div>
        <div className={`${s.sub} text-gray-400 dark:text-gray-500 font-medium tracking-wide`}>
          Retail Assistant
        </div>
      </div>
    </div>
  );
}

export function LogoCompact({ className = '' }) {
  return (
    <div className={`flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 text-white font-bold shadow-md ${className}`}>
      <span className="text-sm font-extrabold tracking-tight">JM</span>
    </div>
  );
}

export function LogoAnimated({ className = '' }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 text-white font-bold shadow-lg shadow-primary-500/30 animate-pulse-slow">
        <Store size={22} className="animate-bounce-slow" />
        <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-accent-500 border-2 border-white dark:border-dark-card" />
      </div>
      <div className="leading-tight">
        <div className="text-xl font-extrabold text-gray-900 dark:text-dark-text tracking-tight">
          Jane<span className="text-primary-500">Maiks</span>
        </div>
        <div className="text-xs text-gray-400 dark:text-gray-500 font-medium tracking-wide">
          Loading...
        </div>
      </div>
    </div>
  );
}
