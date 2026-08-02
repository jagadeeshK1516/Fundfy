"use client";

export function LoadingSpinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12",
  };

  return (
    <div className="flex items-center justify-center p-4">
      <div
        className={`${sizeClasses[size]} rounded-full border-2 border-slate-700 border-t-brand-pink animate-spin`}
      />
    </div>
  );
}

export function LoadingShimmer({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 rounded animate-shimmer"
          style={{ width: `${80 - i * 15}%` }}
        />
      ))}
    </div>
  );
}
