export default function Card({ children, className = '', hover = false, glass = false, padded = true }) {
  const cls = hover ? 'card-hover' : glass ? 'card-glass' : 'card';
  return (
    <div className={`${cls} ${padded ? '' : 'p-0'} ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-base font-semibold text-gray-900 dark:text-dark-text">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

export function CardSection({ children, className = '' }) {
  return <div className={`space-y-4 ${className}`}>{children}</div>;
}

export function Divider({ className = '' }) {
  return <div className={`divider ${className}`} />;
}
