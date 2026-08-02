"use client";

import type { Workstream } from "@/lib/types";
import { TaskCard } from "./task-card";

interface WorkstreamTimelineProps {
  workstreams: Workstream[];
}

export function WorkstreamTimeline({ workstreams }: WorkstreamTimelineProps) {
  if (workstreams.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        <p className="text-lg">No workstreams yet</p>
        <p className="text-sm mt-1">Trigger an execution to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {workstreams.map((ws) => (
        <div
          key={ws.id}
          className="bg-slate-900 border border-slate-800 rounded-xl p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-100">{ws.objective}</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Status: <span className="capitalize">{ws.status}</span>
              </p>
            </div>
          </div>
          {ws.tasks.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {ws.tasks.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No tasks in this workstream.</p>
          )}
        </div>
      ))}
    </div>
  );
}
