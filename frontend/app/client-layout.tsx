"use client";

import { SessionProvider } from "next-auth/react";
import { WorkspaceProvider, useWorkspace } from "@/lib/workspace-context";
import { Sidebar, MobileMenuButton } from "@/components/sidebar";
import { ToastProvider } from "@/components/ui/toast";

function LayoutInner({ children }: { children: React.ReactNode }) {
  const { state } = useWorkspace();
  const collapsed = state.sidebarCollapsed;

  return (
    <div className="flex h-full">
      <Sidebar />
      <main
        className={`
          flex-1 min-h-screen transition-all duration-300
          ${collapsed ? "md:ml-16" : "md:ml-64"}
          ml-0
        `}
      >
        <MobileMenuButton />
        <div className="animate-fade-in h-full">{children}</div>
      </main>
    </div>
  );
}

export function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <WorkspaceProvider>
        <ToastProvider>
          <LayoutInner>{children}</LayoutInner>
        </ToastProvider>
      </WorkspaceProvider>
    </SessionProvider>
  );
}
