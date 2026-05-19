import { Package } from 'lucide-react';

export default function EmptyState({ icon: Icon = Package, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="p-4 rounded-2xl bg-gray-50 dark:bg-dark-surface border border-gray-100 dark:border-dark-border mb-4 relative">
        <Icon size={48} className="text-gray-300 dark:text-gray-600" />
        <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-accent-500 border-2 border-white dark:border-dark-card" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-text mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-500 dark:text-gray-400 text-center max-w-sm mb-4">{description}</p>}
      {action}
    </div>
  );
}
