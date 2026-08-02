"use client";

import Link from "next/link";
import { useWorkspace } from "@/lib/workspace-context";

const stats = [
  { label: "Documents Generated", value: "—", icon: DocStatIcon },
  { label: "Active Workstreams", value: "—", icon: WorkstreamStatIcon },
  { label: "Readiness Score", value: "—", icon: ScoreStatIcon },
];

const quickActions = [
  { label: "Start Chat", href: "/chat", description: "Talk to your AI business advisor" },
  { label: "Create Business", href: "/business", description: "Set up your business profile" },
  { label: "Generate Document", href: "/documents", description: "Create business documents" },
];

export default function DashboardPage() {
  const { state } = useWorkspace();

  return (
    <div className="p-6 md:p-8 max-w-6xl mx-auto space-y-8">
      {/* Welcome Header */}
      <div className="space-y-2">
        <h1 className="text-3xl md:text-4xl font-bold">
          Welcome to{" "}
          <span className="bg-gradient-to-r from-brand-pink to-brand-purple bg-clip-text text-transparent">
            Fundfy.ai
          </span>
        </h1>
        <p className="text-slate-400 text-lg">
          {state.businessName
            ? `Managing: ${state.businessName}`
            : "Your AI-powered business planning and execution platform"}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4 hover:border-slate-700 transition-colors"
          >
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-brand-pink/20 to-brand-purple/20 flex items-center justify-center">
              <stat.icon className="w-6 h-6 text-brand-purple" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-100">{stat.value}</p>
              <p className="text-sm text-slate-400">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-200">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="group bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-brand-purple/50 transition-all duration-200 hover:shadow-lg hover:shadow-brand-purple/5"
            >
              <h3 className="font-semibold text-slate-100 group-hover:text-white mb-1">
                {action.label}
              </h3>
              <p className="text-sm text-slate-400">{action.description}</p>
              <div className="mt-3 text-brand-pink text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                Get started →
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Status */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-lg font-semibold text-slate-200 mb-3">Platform Status</h2>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse-subtle" />
          <span className="text-sm text-slate-400">All systems operational</span>
        </div>
      </div>
    </div>
  );
}

function DocStatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function WorkstreamStatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}

function ScoreStatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  );
}
