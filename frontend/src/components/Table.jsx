import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import { useState } from 'react';

export function Table({ headers, children, className = '' }) {
  return (
    <div className={`table-container ${className}`}>
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100 dark:border-dark-border bg-gray-50/50 dark:bg-dark-surface/50">
            {headers.map((h, i) => (
              <th key={i} className="table-header" style={h.width ? { width: h.width } : undefined}>
                {h.sortable ? (
                  <SortButton label={h.label} sortKey={h.key} onSort={h.onSort} currentSort={h.currentSort} />
                ) : (
                  h.label
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50 dark:divide-dark-border/50">
          {children}
        </tbody>
      </table>
    </div>
  );
}

function SortButton({ label, sortKey, onSort, currentSort }) {
  const active = currentSort?.key === sortKey;
  return (
    <button
      className="inline-flex items-center gap-1 hover:text-gray-900 dark:hover:text-dark-text transition-colors"
      onClick={() => onSort?.(sortKey)}
    >
      {label}
      {active ? (
        currentSort.dir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
      ) : (
        <ChevronsUpDown size={14} className="opacity-30" />
      )}
    </button>
  );
}

export function TableRow({ children, className = '', onClick }) {
  return (
    <tr
      className={`table-row ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

export function TableCell({ children, className = '' }) {
  return <td className={`table-cell ${className}`}>{children}</td>;
}

export function TableSkeleton({ rows = 5, cols = 4 }) {
  return (
    <div className="table-container">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100 dark:border-dark-border">
            {Array.from({ length: cols }).map((_, i) => (
              <th key={i} className="table-header"><div className="skeleton h-3 w-20" /></th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, r) => (
            <tr key={r} className="border-b border-gray-50 dark:border-dark-border/50">
              {Array.from({ length: cols }).map((_, c) => (
                <td key={c} className="table-cell"><div className="skeleton h-4 w-full" style={{ maxWidth: `${60 + Math.random() * 40}%` }} /></td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Pagination({ current, total, onChange }) {
  if (total <= 1) return null;
  const pages = [];
  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= current - 1 && i <= current + 1)) {
      pages.push(i);
    } else if (pages[pages.length - 1] !== '...') {
      pages.push('...');
    }
  }

  return (
    <div className="flex items-center justify-between pt-4">
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Page {current} of {total}
      </p>
      <div className="flex items-center gap-1">
        {pages.map((p, i) =>
          p === '...' ? (
            <span key={`e${i}`} className="px-2 text-gray-400">...</span>
          ) : (
            <button
              key={p}
              onClick={() => onChange(p)}
              className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                p === current
                  ? 'bg-primary-500 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-surface'
              }`}
            >
              {p}
            </button>
          )
        )}
      </div>
    </div>
  );
}
