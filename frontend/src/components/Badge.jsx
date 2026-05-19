import { AlertTriangle, CheckCircle, XCircle, Info } from 'lucide-react';

const variants = {
  low: { bg: 'bg-status-low/10 text-status-low', icon: XCircle },
  warning: { bg: 'bg-status-warning/15 text-yellow-700 dark:text-yellow-300', icon: AlertTriangle },
  success: { bg: 'bg-status-success/10 text-status-success', icon: CheckCircle },
  primary: { bg: 'bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-300', icon: Info },
  secondary: { bg: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300', icon: null },
};

export default function Badge({ children, variant = 'secondary', dot, className = '' }) {
  const v = variants[variant] || variants.secondary;
  const Icon = v.icon;

  return (
    <span className={`badge ${v.bg} ${className}`}>
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {Icon && <Icon size={12} />}
      {children}
    </span>
  );
}

export function StockBadge({ available, threshold }) {
  const isLow = threshold && available <= threshold;
  if (isLow) {
    return <Badge variant="low" dot>Low: {available}</Badge>;
  }
  return <Badge variant="success" dot>In Stock: {available}</Badge>;
}

export function MarginBadge({ profit }) {
  if (profit == null) return null;
  if (profit < 5) return <Badge variant="warning"><AlertTriangle size={12} /> Low Margin</Badge>;
  return <Badge variant="success">Healthy Margin</Badge>;
}

export function PriceSourceBadge({ source }) {
  if (source === 'manual') return <Badge variant="primary">Manual</Badge>;
  return <Badge variant="secondary">Calculated</Badge>;
}
