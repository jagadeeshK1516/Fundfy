"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useWorkspace } from "@/lib/workspace-context";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: DashboardIcon },
  { href: "/chat", label: "Chat", icon: ChatIcon },
  { href: "/business", label: "Business", icon: BusinessIcon },
  { href: "/execution", label: "Execution", icon: ExecutionIcon },
  { href: "/documents", label: "Documents", icon: DocumentsIcon },
  { href: "/communication", label: "Communication", icon: CommunicationIcon },
  { href: "/emails", label: "Emails", icon: EmailIcon },
  { href: "/calendar", label: "Calendar", icon: CalendarIcon },
  { href: "/crm", label: "CRM", icon: CRMIcon },
  { href: "/investors", label: "Investors", icon: InvestorsIcon },
  { href: "/grants", label: "Grants", icon: GrantsIcon },
  { href: "/integrations", label: "Integrations", icon: IntegrationsIcon },
];

export function Sidebar() {
  const pathname = usePathname();
  const { state, dispatch } = useWorkspace();
  const collapsed = state.sidebarCollapsed;

  return (
    <>
      {/* Mobile overlay */}
      {!collapsed && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => dispatch({ type: "SET_SIDEBAR_COLLAPSED", payload: true })}
        />
      )}

      <aside
        className={`
          fixed top-0 left-0 h-full z-50 flex flex-col
          bg-slate-900 border-r border-slate-800
          transition-all duration-300 ease-in-out
          ${collapsed ? "w-16" : "w-64"}
          ${collapsed ? "-translate-x-full md:translate-x-0" : "translate-x-0"}
        `}
      >
        {/* Logo / Brand */}
        <div className="flex items-center h-16 px-4 border-b border-slate-800">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-brand-pink to-brand-purple flex items-center justify-center flex-shrink-0">
              <span className="text-white font-bold text-sm">F</span>
            </div>
            {!collapsed && (
              <span className="text-lg font-bold bg-gradient-to-r from-brand-pink to-brand-purple bg-clip-text text-transparent whitespace-nowrap">
                Fundfy.ai
              </span>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg
                  transition-all duration-200
                  ${collapsed ? "justify-center" : ""}
                  ${
                    isActive
                      ? "bg-gradient-to-r from-brand-pink/20 to-brand-purple/20 text-white border border-brand-purple/30"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
                  }
                `}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-brand-pink" : ""}`} />
                {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="p-3 border-t border-slate-800">
          <button
            onClick={() => dispatch({ type: "TOGGLE_SIDEBAR" })}
            className="w-full flex items-center justify-center p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <CollapseIcon className={`w-5 h-5 transition-transform duration-300 ${collapsed ? "rotate-180" : ""}`} />
          </button>
        </div>
      </aside>
    </>
  );
}

// Mobile hamburger button
export function MobileMenuButton() {
  const { dispatch } = useWorkspace();
  return (
    <button
      onClick={() => dispatch({ type: "SET_SIDEBAR_COLLAPSED", payload: false })}
      className="md:hidden fixed top-4 left-4 z-30 p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white"
      aria-label="Open menu"
    >
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>
  );
}

// Icons
function DashboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  );
}

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  );
}

function BusinessIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  );
}

function ExecutionIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
}

function DocumentsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function CommunicationIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function CollapseIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
    </svg>
  );
}

function EmailIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}

function CRMIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  );
}

function InvestorsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function GrantsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2zM10 8.5a.5.5 0 11-1 0 .5.5 0 011 0zm5 5a.5.5 0 11-1 0 .5.5 0 011 0z" />
    </svg>
  );
}

function IntegrationsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  );
}
