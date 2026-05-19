import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Package, MessageSquare, BarChart3, X } from 'lucide-react';
import { LogoFull } from './Logo';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/products', icon: Package, label: 'Products' },
  { to: '/chatbot', icon: MessageSquare, label: 'AI Assistant' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
];

function NavLink({ to, icon: Icon, label, onClick }) {
  const location = useLocation();
  const active = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));

  return (
    <Link
      to={to}
      onClick={onClick}
      className={`nav-link ${active ? 'nav-link-active' : ''}`}
      aria-current={active ? 'page' : undefined}
    >
      <Icon size={20} />
      <span>{label}</span>
      {active && (
        <span className="ml-auto w-1.5 h-5 rounded-full bg-primary-500 dark:bg-primary-400" />
      )}
    </Link>
  );
}

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 dark:bg-black/60 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed md:sticky top-0 left-0 z-50 md:z-0
          h-full w-64 md:h-screen
          bg-white dark:bg-dark-card
          border-r border-gray-100 dark:border-dark-border
          flex flex-col
          transition-transform duration-300 ease-in-out
          ${open ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 h-16 border-b border-gray-100 dark:border-dark-border flex-shrink-0">
          <Link to="/" className="flex items-center gap-2.5 group">
            <LogoFull />
          </Link>
          <button
            onClick={onClose}
            className="md:hidden btn-icon btn-ghost"
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink key={item.to} {...item} onClick={onClose} />
          ))}
        </nav>

        {/* Brand footer */}
        <div className="px-5 py-4 border-t border-gray-100 dark:border-dark-border flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-500/10 dark:to-blue-500/10 flex items-center justify-center">
              <span className="text-xs font-bold text-primary-500">JM</span>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">JaneMaiks Retail Assistant</p>
              <p className="text-xs text-gray-400 dark:text-gray-500">v2.0.0</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
