"use client";

import { useState, useEffect } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { getWorkstreams } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { ExecutionTrigger } from "@/components/execution/execution-trigger";
import { WorkstreamTimeline } from "@/components/execution/workstream-timeline";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import type { Workstream } from "@/lib/types";

export default function ExecutionPage() {
  const { state } = useWorkspace();
  const { addToast } = useToast();
  const [workstreams, setWorkstreams] = useState<Workstream[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!state.businessId) return;
    let cancelled = false;
    setLoading(true);
    getWorkstreams(state.businessId)
      .then((data) => {
        if (!cancelled) setWorkstreams(data);
      })
      .catch((err) => {
        if (!cancelled) {
          addToast(err instanceof Error ? err.message : "Failed to load workstreams", "error");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [state.businessId, addToast, refreshKey]);

  const fetchWorkstreams = () => setRefreshKey((k) => k + 1);

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Execution Timeline</h1>
        <p className="text-slate-400 mt-1">
          Set objectives and track AI-driven task execution.
        </p>
      </div>

      <ExecutionTrigger onExecuted={fetchWorkstreams} />

      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-4">Workstreams</h2>
        {loading ? <LoadingSpinner /> : <WorkstreamTimeline workstreams={workstreams} />}
      </div>
    </div>
  );
}
