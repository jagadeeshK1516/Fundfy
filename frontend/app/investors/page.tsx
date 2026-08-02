"use client";

import { useEffect, useState } from "react";
import { searchInvestors } from "@/lib/api";

export default function InvestorsPage() {
  const [investors, setInvestors] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ stage: "", industry: "", location: "" });

  useEffect(() => {
    loadInvestors();
  }, []);

  async function loadInvestors() {
    setLoading(true);
    try {
      const data = await searchInvestors(filters.stage || filters.industry || filters.location ? filters : undefined);
      setInvestors(data.investors || []);
    } catch {
      setInvestors([]);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch() {
    loadInvestors();
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-2">Investor Database</h1>
      <p className="text-slate-400 mb-6">Search 50+ VCs and angel investors by stage, industry, and location.</p>

      <div className="flex gap-3 mb-6">
        <select value={filters.stage} onChange={(e) => setFilters({ ...filters, stage: e.target.value })} className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm">
          <option value="">All Stages</option>
          <option value="pre-seed">Pre-Seed</option>
          <option value="seed">Seed</option>
          <option value="series-a">Series A</option>
          <option value="series-b">Series B</option>
        </select>
        <input type="text" placeholder="Industry (e.g. AI/ML, SaaS)" value={filters.industry} onChange={(e) => setFilters({ ...filters, industry: e.target.value })} className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm flex-1" />
        <input type="text" placeholder="Location" value={filters.location} onChange={(e) => setFilters({ ...filters, location: e.target.value })} className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
        <button onClick={handleSearch} className="px-4 py-2 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple text-white text-sm font-medium">
          Search
        </button>
      </div>

      {loading ? (
        <p className="text-slate-400">Loading...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {investors.map((inv: any) => (
            <div key={inv.id} className="bg-slate-800 rounded-xl p-5 border border-slate-700">
              <h3 className="text-white font-semibold">{inv.name}</h3>
              {inv.firm && <p className="text-sm text-brand-purple">{inv.firm}</p>}
              <div className="mt-3 space-y-1">
                {inv.stage_preference && (
                  <p className="text-xs text-slate-400">Stage: <span className="text-slate-300">{inv.stage_preference}</span></p>
                )}
                {inv.location && (
                  <p className="text-xs text-slate-400">Location: <span className="text-slate-300">{inv.location}</span></p>
                )}
                {inv.check_size_min != null && inv.check_size_max != null && (
                  <p className="text-xs text-slate-400">Check size: <span className="text-slate-300">${(inv.check_size_min / 1000).toFixed(0)}K - ${(inv.check_size_max / 1000000).toFixed(1)}M</span></p>
                )}
              </div>
              {inv.focus_areas?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {inv.focus_areas.slice(0, 4).map((area: string) => (
                    <span key={area} className="px-2 py-0.5 rounded text-xs bg-brand-purple/20 text-brand-purple">{area}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      {!loading && investors.length === 0 && (
        <p className="text-slate-400 text-center py-8">No investors found. Try adjusting your filters.</p>
      )}
    </div>
  );
}
