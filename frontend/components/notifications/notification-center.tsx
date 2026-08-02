"use client";

import { useEffect, useState } from "react";
import { getNotifications, markNotificationRead } from "@/lib/api";

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const unread = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  async function loadNotifications() {
    try {
      const data = await getNotifications(20);
      setNotifications(data.notifications || []);
    } catch { /* ignore */ }
  }

  async function handleMarkRead(id: string) {
    await markNotificationRead(id);
    setNotifications(notifications.map((n) =>
      n.id === id ? { ...n, read: true } : n
    ));
  }

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)}
        className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-brand-pink text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-10 w-80 max-h-96 overflow-y-auto bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50">
          <div className="p-3 border-b border-slate-700">
            <h4 className="text-sm font-semibold text-white">Notifications</h4>
          </div>
          {notifications.length === 0 ? (
            <p className="p-4 text-sm text-slate-400">No notifications.</p>
          ) : (
            notifications.map((n) => (
              <div key={n.id} onClick={() => handleMarkRead(n.id)}
                className={`p-3 border-b border-slate-700/50 cursor-pointer hover:bg-slate-700/50 ${!n.read ? "bg-slate-700/20" : ""}`}>
                <p className="text-sm text-white font-medium">{n.title}</p>
                <p className="text-xs text-slate-400">{n.body}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
