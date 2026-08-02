"use client";

import { useEffect, useState } from "react";
import { getGoogleAuthUrl, getGoogleStatus, disconnectGoogle } from "@/lib/api";

export default function IntegrationsPage() {
  const [googleStatus, setGoogleStatus] = useState<{ connected: boolean; scopes?: string[] }>({ connected: false });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  async function loadStatus() {
    try {
      const status = await getGoogleStatus();
      setGoogleStatus(status);
    } catch {
      // Not connected
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect() {
    try {
      const { auth_url } = await getGoogleAuthUrl();
      window.location.href = auth_url;
    } catch (err) {
      console.error("Failed to get auth URL", err);
    }
  }

  async function handleDisconnect() {
    await disconnectGoogle();
    setGoogleStatus({ connected: false });
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-8">Integrations</h1>

      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-lg bg-white flex items-center justify-center">
              <svg className="w-8 h-8" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Google Workspace</h3>
              <p className="text-sm text-slate-400">Gmail, Calendar, Drive</p>
            </div>
          </div>
          <div>
            {loading ? (
              <span className="text-slate-400">Loading...</span>
            ) : googleStatus.connected ? (
              <div className="flex items-center gap-3">
                <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm font-medium">Connected</span>
                <button onClick={handleDisconnect} className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 text-sm">
                  Disconnect
                </button>
              </div>
            ) : (
              <button onClick={handleConnect} className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple text-white font-medium hover:opacity-90">
                Connect Google
              </button>
            )}
          </div>
        </div>
        {googleStatus.connected && googleStatus.scopes && (
          <div className="mt-4 pt-4 border-t border-slate-700">
            <p className="text-sm text-slate-400">Scopes: {googleStatus.scopes.join(", ")}</p>
          </div>
        )}
      </div>
    </div>
  );
}
