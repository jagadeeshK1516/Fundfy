"use client";

import { useState, useEffect } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { listDocuments } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { DocumentGenerateForm } from "@/components/documents/document-generate-form";
import { DocumentList } from "@/components/documents/document-list";
import { DocumentViewer } from "@/components/documents/document-viewer";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import type { Document } from "@/lib/types";

export default function DocumentsPage() {
  const { state } = useWorkspace();
  const { addToast } = useToast();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewingDoc, setViewingDoc] = useState<Document | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!state.businessId) return;
    let cancelled = false;
    setLoading(true);
    listDocuments(state.businessId)
      .then((data) => {
        if (!cancelled) setDocuments(data);
      })
      .catch((err) => {
        if (!cancelled) {
          addToast(err instanceof Error ? err.message : "Failed to load documents", "error");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [state.businessId, addToast, refreshKey]);

  const fetchDocuments = () => setRefreshKey((k) => k + 1);

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Document Center</h1>
        <p className="text-slate-400 mt-1">
          Generate and manage your business documents.
        </p>
      </div>

      <DocumentGenerateForm onGenerated={fetchDocuments} />

      <div>
        <h2 className="text-lg font-semibold text-slate-200 mb-4">Your Documents</h2>
        {loading ? (
          <LoadingSpinner />
        ) : (
          <DocumentList documents={documents} onView={setViewingDoc} />
        )}
      </div>

      {viewingDoc && (
        <DocumentViewer document={viewingDoc} onClose={() => setViewingDoc(null)} />
      )}
    </div>
  );
}
