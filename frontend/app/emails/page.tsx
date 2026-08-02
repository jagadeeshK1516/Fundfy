"use client";

import { useEffect, useState } from "react";
import { getPendingEmails, approveEmail, rejectEmail } from "@/lib/api";

export default function EmailsPage() {
  const [emails, setEmails] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEmails();
  }, []);

  async function loadEmails() {
    try {
      const data = await getPendingEmails();
      setEmails(data);
    } catch {
      setEmails([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(id: string) {
    await approveEmail(id);
    setEmails(emails.filter((e) => e.id !== id));
  }

  async function handleReject(id: string) {
    await rejectEmail(id);
    setEmails(emails.filter((e) => e.id !== id));
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-2">Email Approvals</h1>
      <p className="text-slate-400 mb-8">Review and approve emails drafted by the AI agent.</p>

      {loading ? (
        <p className="text-slate-400">Loading...</p>
      ) : emails.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
          <p className="text-slate-400">No pending emails. The AI will draft emails here for your approval.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {emails.map((email) => (
            <div key={email.id} className="bg-slate-800 rounded-xl p-6 border border-slate-700">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-white font-medium">{email.subject}</p>
                  <p className="text-sm text-slate-400">To: {email.to}</p>
                </div>
                <span className="px-2 py-1 rounded text-xs bg-yellow-500/20 text-yellow-400">Pending</span>
              </div>
              <p className="text-slate-300 text-sm mb-4 whitespace-pre-wrap">{email.body}</p>
              <div className="flex gap-3">
                <button onClick={() => handleApprove(email.id)} className="px-4 py-2 rounded-lg bg-green-600 text-white text-sm hover:bg-green-700">
                  Approve & Send
                </button>
                <button onClick={() => handleReject(email.id)} className="px-4 py-2 rounded-lg bg-slate-700 text-slate-300 text-sm hover:bg-slate-600">
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
