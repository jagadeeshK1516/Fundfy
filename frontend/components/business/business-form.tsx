"use client";

import { useState, useEffect } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { createBusiness, getBusiness } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import { ErrorMessage } from "@/components/ui/error-message";
import type { Business } from "@/lib/types";

export function BusinessForm() {
  const { state, dispatch } = useWorkspace();
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [business, setBusiness] = useState<Business | null>(null);

  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [stage, setStage] = useState("");
  const [goals, setGoals] = useState("");

  useEffect(() => {
    if (!state.businessId) return;
    let cancelled = false;
    setFetching(true);
    getBusiness(state.businessId)
      .then((biz) => {
        if (cancelled) return;
        setBusiness(biz);
        setName(biz.name);
        setIndustry(biz.industry);
        setStage(biz.stage);
        setGoals(biz.goals);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load business");
      })
      .finally(() => {
        if (!cancelled) setFetching(false);
      });
    return () => { cancelled = true; };
  }, [state.businessId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.founderId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await createBusiness({
        founder_id: state.founderId,
        name,
        industry,
        stage,
        goals,
      });
      setBusiness(result);
      dispatch({ type: "SET_BUSINESS", payload: { id: result.id, name: result.name } });
      addToast("Business profile saved successfully!", "success");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save business";
      setError(msg);
      addToast(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      {error && <ErrorMessage message={error} onRetry={() => setError(null)} />}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            Business Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-purple transition-colors"
            placeholder="Enter your business name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            Industry
          </label>
          <input
            type="text"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-purple transition-colors"
            placeholder="e.g., FinTech, HealthTech, SaaS"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            Stage
          </label>
          <select
            value={stage}
            onChange={(e) => setStage(e.target.value)}
            required
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-brand-purple transition-colors"
          >
            <option value="">Select stage</option>
            <option value="idea">Idea</option>
            <option value="mvp">MVP</option>
            <option value="pre-seed">Pre-Seed</option>
            <option value="seed">Seed</option>
            <option value="series-a">Series A</option>
            <option value="growth">Growth</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            Goals
          </label>
          <textarea
            value={goals}
            onChange={(e) => setGoals(e.target.value)}
            required
            rows={4}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 resize-none focus:outline-none focus:border-brand-purple transition-colors"
            placeholder="What are your primary business goals?"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple text-white font-medium text-sm hover:shadow-lg hover:shadow-brand-purple/20 disabled:opacity-50 transition-all duration-200"
        >
          {loading ? "Saving..." : business ? "Update Business" : "Create Business"}
        </button>
      </form>

      {/* Display current business */}
      {business && (
        <div className="mt-8 p-5 bg-slate-800/50 border border-slate-700 rounded-xl space-y-3">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
            Current Business Profile
          </h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-slate-500">Name:</span>
              <p className="text-slate-200">{business.name}</p>
            </div>
            <div>
              <span className="text-slate-500">Industry:</span>
              <p className="text-slate-200">{business.industry}</p>
            </div>
            <div>
              <span className="text-slate-500">Stage:</span>
              <p className="text-slate-200 capitalize">{business.stage}</p>
            </div>
            <div className="col-span-2">
              <span className="text-slate-500">Goals:</span>
              <p className="text-slate-200">{business.goals}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
