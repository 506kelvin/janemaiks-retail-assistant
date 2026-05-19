import { Search, X } from 'lucide-react';
import { useRef } from 'react';

export default function SearchBar({ value, onChange, placeholder = 'Search...', className = '' }) {
  const inputRef = useRef(null);

  return (
    <div className={`relative ${className}`}>
      <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
      <input
        ref={inputRef}
        type="text"
        className="input-field pl-10 pr-10"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={placeholder}
      />
      {value && (
        <button
          onClick={() => { onChange(''); inputRef.current?.focus(); }}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          aria-label="Clear search"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}
