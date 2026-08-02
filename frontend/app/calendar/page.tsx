"use client";

import { useEffect, useState } from "react";
import { getCalendarEvents, createCalendarEvent } from "@/lib/api";

export default function CalendarPage() {
  const [events, setEvents] = useState<any[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newEvent, setNewEvent] = useState({ summary: "", start: "", end: "", attendees: "" });

  useEffect(() => {
    loadEvents();
  }, []);

  async function loadEvents() {
    try {
      const data = await getCalendarEvents();
      setEvents(data.events || []);
      setConnected(data.connected);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    const attendees = newEvent.attendees ? newEvent.attendees.split(",").map((a) => a.trim()) : [];
    await createCalendarEvent({
      summary: newEvent.summary,
      start: newEvent.start,
      end: newEvent.end,
      attendees,
      meet_link: true,
    });
    setShowNew(false);
    setNewEvent({ summary: "", start: "", end: "", attendees: "" });
    loadEvents();
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-white">Calendar</h1>
        {connected && (
          <button onClick={() => setShowNew(!showNew)} className="px-4 py-2 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple text-white text-sm font-medium">
            New Event
          </button>
        )}
      </div>

      {!connected && !loading && (
        <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
          <p className="text-slate-400">Connect Google in Integrations to view your calendar.</p>
        </div>
      )}

      {showNew && (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-6">
          <h3 className="text-white font-semibold mb-4">New Event</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <input type="text" placeholder="Event title" value={newEvent.summary} onChange={(e) => setNewEvent({ ...newEvent, summary: e.target.value })} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
            <input type="text" placeholder="Attendees (comma-separated)" value={newEvent.attendees} onChange={(e) => setNewEvent({ ...newEvent, attendees: e.target.value })} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
            <input type="datetime-local" value={newEvent.start} onChange={(e) => setNewEvent({ ...newEvent, start: e.target.value })} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
            <input type="datetime-local" value={newEvent.end} onChange={(e) => setNewEvent({ ...newEvent, end: e.target.value })} className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm" />
          </div>
          <button onClick={handleCreate} className="px-4 py-2 rounded-lg bg-green-600 text-white text-sm">Create</button>
        </div>
      )}

      {loading ? (
        <p className="text-slate-400">Loading...</p>
      ) : (
        <div className="space-y-3">
          {events.length === 0 ? (
            <p className="text-slate-400 text-center py-8">No upcoming events.</p>
          ) : (
            events.map((event: any, i: number) => (
              <div key={event.id || i} className="bg-slate-800 rounded-xl p-4 border border-slate-700 flex items-center justify-between">
                <div>
                  <p className="text-white font-medium">{event.summary}</p>
                  <p className="text-sm text-slate-400">{event.start?.dateTime || event.start?.date}</p>
                </div>
                {event.hangoutLink && (
                  <a href={event.hangoutLink} target="_blank" rel="noreferrer" className="text-sm text-brand-pink hover:underline">
                    Join Meet
                  </a>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
