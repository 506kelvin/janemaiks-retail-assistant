import { LogoAnimated } from './Logo';

export function CardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="skeleton h-4 w-24 mb-2" />
          <div className="skeleton h-8 w-32" />
        </div>
        <div className="skeleton h-12 w-12 rounded-xl" />
      </div>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <LogoAnimated />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="skeleton h-5 w-32 mb-4" />
            {Array.from({ length: 3 }).map((_, j) => (
              <div key={j} className="flex items-center justify-between py-2">
                <div className="skeleton h-4 w-24" />
                <div className="skeleton h-4 w-16" />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function TimelineSkeleton({ items = 3 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex gap-3 animate-pulse">
          <div className="skeleton h-4 w-4 rounded-full mt-1" />
          <div className="flex-1 space-y-1">
            <div className="skeleton h-3 w-20" />
            <div className="skeleton h-4 w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
