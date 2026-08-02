"use client";

import type { Task } from "@/lib/types";

const statusConfig = {
  pending: { bg: "bg-yellow-500/10", border: "border-yellow-500/30", text: "text-yellow-400", dot: "bg-yellow-400" },
  running: { bg: "bg-blue-500/10", border: "border-blue-500/30", text: "text-blue-400", dot: "bg-blue-400 animate-pulse-subtle" },
  completed: { bg: "bg-green-500/10", border: "border-green-500/30", text: "text-green-400", dot: "bg-green-400" },
  failed: { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", dot: "bg-red-400" },
};

export function TaskCard({ task }: { task: Task }) {
  const config = statusConfig[task.status] || statusConfig.pending;

  return (
    <div className={`p-4 rounded-lg border ${config.bg} ${config.border}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-200">{task.type}</span>
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${config.dot}`} />
          <span className={`text-xs font-medium capitalize ${config.text}`}>
            {task.status}
          </span>
        </div>
      </div>
      {task.result && (
        <p className="text-xs text-slate-400 mt-1 line-clamp-3">{task.result}</p>
      )}
    </div>
  );
}
