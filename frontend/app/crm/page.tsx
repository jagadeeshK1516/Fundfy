"use client";

import { useEffect, useState } from "react";
import { getCRMContacts, getCRMPipeline, addCRMContact, updateCRMContact } from "@/lib/api";

const STAGES = ["lead", "contacted", "meeting", "proposal", "negotiation", "closed_won", "closed_lost"];

const STAGE_COLORS: Record<string, string> = {
  lead: "bg-slate-600",
  contacted: "bg-blue-600",
  meeting: "bg-yellow-600",
  proposal: "bg-purple-600",
  negotiation: "bg-orange-600",
  closed_won: "bg-green-600",
  closed_lost: "bg-red-600",
};

export default function CRMPage() {
  const [contacts, setContacts] = useState<any[]>([]);
  const [pipeline, setPipeline] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newContact, setNewContact] = useState({ name: "", email: "", company: "", type: "investor" });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [contactData, pipelineData] = await Promise.all([getCRMContacts(), getCRMPipeline()]);
      setContacts(contactData.contacts || []);
      setPipeline(pipelineData.pipeline || {});
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd() {
    await addCRMContact(newContact);
    setShowAdd(false);
    setNewContact({ name: "", email: "", company: "", type: "investor" });
    loadData();
  }

  async function handleMoveStage(contactId: string, stage: string) {
    await updateCRMContact(contactId, { pipeline_stage: stage });
    loadData();
  }

  const contactsByStage = STAGES.reduce((acc, stage) => {
    acc[stage] = contacts.filter((c) => c.pipeline_stage === stage);
    return acc;
  }, {} as Record<string, any[]>);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-white">CRM Pipeline</h1>
        <button onClick={() => setShowAdd(!showAdd)} className="px-4 py-2 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple text-white text-sm font-medium">
          Add Contact
        </button>
      </div>

      {showAdd && (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-6 max-w-2xl">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <input type="text" placeholder="Name" value={newContact.name} onChange={(e) => setNewContact({ ...newContact, name: e.target.value })} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
            <input type="email" placeholder="Email" value={newContact.email} onChange={(e) => setNewContact({ ...newContact, email: e.target.value })} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
            <input type="text" placeholder="Company" value={newContact.company} onChange={(e) => setNewContact({ ...newContact, company: e.target.value })} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
            <select value={newContact.type} onChange={(e) => setNewContact({ ...newContact, type: e.target.value })} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm">
              <option value="investor">Investor</option>
              <option value="mentor">Mentor</option>
              <option value="partner">Partner</option>
              <option value="other">Other</option>
            </select>
          </div>
          <button onClick={handleAdd} className="px-4 py-2 rounded-lg bg-green-600 text-white text-sm">Save</button>
        </div>
      )}

      {loading ? (
        <p className="text-slate-400">Loading...</p>
      ) : (
        <div className="grid grid-cols-7 gap-3 overflow-x-auto">
          {STAGES.map((stage) => (
            <div key={stage} className="min-w-[180px]">
              <div className={`flex items-center gap-2 mb-3 px-3 py-1.5 rounded-lg ${STAGE_COLORS[stage]}/20`}>
                <span className="text-xs font-semibold text-white uppercase">{stage.replace("_", " ")}</span>
                <span className="ml-auto text-xs text-slate-400">{pipeline[stage] || 0}</span>
              </div>
              <div className="space-y-2">
                {contactsByStage[stage]?.map((contact: any) => (
                  <div key={contact.id} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                    <p className="text-sm font-medium text-white">{contact.name}</p>
                    {contact.company && <p className="text-xs text-slate-400">{contact.company}</p>}
                    <p className="text-xs text-slate-500 mt-1">{contact.type}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
