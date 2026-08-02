"use client";

import { useEffect, useState } from "react";
import { searchGrants, getGrantApplications } from "@/lib/api";

export default function GrantsPage() {
  const [grants, setGrants] = useState<any[]>([]);
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ industry: "", region: "" });

  useEffect(() => { loadData(); }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [gData, aData] = await Promise.all([
        searchGrants(filters.industry || filters.region ? filters : undefined),
        getGrantApplications(),
      ]);
      setGrants(gData.grants || []);
      setApplications(aData.applications || []);
    } catch { /* ignore */ } finally { setLoading(false); }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-2">Grants</h1>
      <p className="text-slate-400 mb-6">Browse and track grant opportunities.</p>
      <div className="flex gap-3 mb-6">
        <input type="text" placeholder="Industry" value={filters.industry}
          onChange={(e) => setFilters({ ...filters, industry: e.target.value })}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
        <input type="text" placeholder="Region" value={filters.region}
          onChange={(e) => setFilters({ ...filters, region: e.target.value })}
          className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
        <button onClick={loadData}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple text-white text-sm font-medium">
          Search
        </button>
      </div>
      {loading ? <p className="text-slate-400">Loading...</p> : (
        <div className="space-y-4">
          {grants.map((g: any) => (
            <div key={g.id} className="bg-slate-800 rounded-xl p-5 border border-slate-700">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-white font-semibold">{g.name}</h3>
                  <p className="text-sm text-brand-purple">{g.provider}</p>
                </div>
                {g.amount_max && (
                  <span className="text-sm text-green-400 font-medium">
                    Up to ${(g.amount_max / 1000).toFixed(0)}K
                  </span>
                )}
              </div>
              {g.description && <p className="text-sm text-slate-400 mt-2">{g.description}</p>}
              <div className="flex gap-4 mt-3 text-xs text-slate-500">
                {g.deadline && <span>Deadline: {g.deadline}</span>}
                {g.region && <span>Region: {g.region}</span>}
              </div>
            </div>
          ))}
          {grants.length === 0 && <p className="text-slate-400 text-center py-8">No grants found.</p>}
        </div>
      )}
    </div>
  );
}
