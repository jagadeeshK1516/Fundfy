"use client";

import { useState } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { executeObjective } from "@/lib/api";
import { useToast } from "@/components/ui/toast";

interface ExecutionTriggerProps {
  onExecuted: () => void;
}

export function ExecutionTrigger({ onExecuted }: ExecutionTriggerProps) {
  const { state } = useWorkspace();
  const { addToast } = useToast();
  const [objective, setObjective] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.businessId) {
      addToast("Please create a business profile first", "error");
      return;
    }
    if (!objective.trim()) return;

    setLoading(true);
    try {
      await executeObjective({
        business_id: state.businessId,
        objective: objective.trim(),
        context: context.trim() || undefined,
      });
      addToast("Execution started successfully!", "success");
      setObjective("");
      setContext("");
      onExecuted();
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : "Execution failed",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleExecute} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
      <h2 className="text-lg font-semibold text-slate-100">Trigger Execution</h2>
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1.5">
          Objective
        </label>
        <input
          type="text"
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          required
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-purple transition-colors"
          placeholder="What do you want to accomplish?"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1.5">
          Context (optional)
        </label>
        <textarea
          value={context}
          onChange={(e) => setContext(e.target.value)}
          rows={2}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 resize-none focus:outline-none focus:border-brand-purple transition-colors"
          placeholder="Additional context or constraints..."
        />
      </div>
      <button
        type="submit"
        disabled={loading || !state.businessId}
        className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple text-white font-medium text-sm hover:shadow-lg hover:shadow-brand-purple/20 disabled:opacity-50 transition-all duration-200"
      >
        {loading ? "Executing..." : "Execute"}
      </button>
      {!state.businessId && (
        <p className="text-xs text-slate-500">Create a business profile to enable execution.</p>
      )}
    </form>
  );
}
