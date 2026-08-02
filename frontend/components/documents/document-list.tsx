"use client";

import type { Document } from "@/lib/types";

interface DocumentListProps {
  documents: Document[];
  onView: (doc: Document) => void;
}

export function DocumentList({ documents, onView }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        <p className="text-lg">No documents yet</p>
        <p className="text-sm mt-1">Generate your first business document above.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="bg-slate-900 border border-slate-800 rounded-xl p-4 hover:border-slate-700 transition-colors"
        >
          <div className="flex items-start justify-between mb-2">
            <h3 className="font-medium text-slate-200 text-sm line-clamp-2">{doc.title}</h3>
          </div>
          <span className="inline-block px-2 py-0.5 text-xs rounded-full bg-brand-purple/20 text-brand-purple border border-brand-purple/30 mb-3">
            {doc.doc_type}
          </span>
          {doc.created_at && (
            <p className="text-xs text-slate-500 mb-3">
              {new Date(doc.created_at).toLocaleDateString()}
            </p>
          )}
          <button
            onClick={() => onView(doc)}
            className="text-sm text-brand-pink hover:text-brand-purple transition-colors font-medium"
          >
            View →
          </button>
        </div>
      ))}
    </div>
  );
}
