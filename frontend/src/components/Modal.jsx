import { X } from 'lucide-react';
import { useEffect, useRef } from 'react';

export default function Modal({ open, onClose, title, children, size = 'md' }) {
  const overlayRef = useRef(null);
  const contentRef = useRef(null);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
      contentRef.current?.focus();
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    if (open) window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 dark:bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === overlayRef.current) onClose?.(); }}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        ref={contentRef}
        tabIndex={-1}
        className={`bg-white dark:bg-dark-card rounded-2xl shadow-elevated w-full ${sizes[size] || sizes.md}
                    max-h-[90vh] overflow-y-auto animate-slide-up border border-gray-100 dark:border-dark-border`}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-dark-border">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-dark-text">{title}</h2>
          <button onClick={onClose} className="btn-icon btn-ghost" aria-label="Close">
            <X size={20} />
          </button>
        </div>
        <div className="px-6 py-4">
          {children}
        </div>
      </div>
    </div>
  );
}
