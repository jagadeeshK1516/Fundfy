"use client";

import { CoachingChat } from "@/components/communication/coaching-chat";

export default function CommunicationPage() {
  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 md:p-6 pb-0">
        <h1 className="text-2xl font-bold text-slate-100">Communication Coach</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Practice interviews, pitches, and Q&A sessions with AI feedback.
        </p>
      </div>
      <div className="flex-1 min-h-0">
        <CoachingChat />
      </div>
    </div>
  );
}
