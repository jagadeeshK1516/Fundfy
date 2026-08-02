"use client";

import { useState } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { generateDocument } from "@/lib/api";
import { useToast } from "@/components/ui/toast";

const DOC_TYPES = [
  "Business Plan",
  "Executive Summary",
  "Pitch Deck",
  "PRD",
  "BRD",
  "SOP",
  "Financial Model",
  "DPR",
  "Company Profile",
];

interface DocumentGenerateFormProps {
  onGenerated: () => void;
}

export function DocumentGenerateForm({ onGenerated }: DocumentGenerateFormProps) {
  const { state } = useWorkspace();
  const { addToast } = useToast();
  const [docType, setDocType] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!state.businessId) {
      addToast("Please create a business profile first", "error");
      return;
    }
    if (!docType) return;

    setLoading(true);
    try {
      await generateDocument({
        business_id: state.businessId,
        doc_type: docType,
        context: context.trim() || undefined,
      });
      addToast("Document generated successfully!", "success");
      setDocType("");
      setContext("");
      onGenerated();
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : "Failed to generate document",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleGenerate} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
      <h2 className="text-lg font-semibold text-slate-100">Generate Document</h2>
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1.5">
          Document Type
        </label>
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          required
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-brand-purple transition-colors"
        >
          <option value="">Select type...</option>
          {DOC_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
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
          placeholder="Additional context for the document..."
        />
      </div>
      <button
        type="submit"
        disabled={loading || !state.businessId}
        className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple text-white font-medium text-sm hover:shadow-lg hover:shadow-brand-purple/20 disabled:opacity-50 transition-all duration-200"
      >
        {loading ? "Generating..." : "Generate"}
      </button>
      {!state.businessId && (
        <p className="text-xs text-slate-500">Create a business profile to generate documents.</p>
      )}
    </form>
  );
}
