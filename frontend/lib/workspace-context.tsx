"use client";

import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  type ReactNode,
} from "react";

function generateUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

interface WorkspaceState {
  founderId: string;
  businessId: string | null;
  businessName: string | null;
  sidebarCollapsed: boolean;
  activePanel: string;
}

type WorkspaceAction =
  | { type: "SET_FOUNDER_ID"; payload: string }
  | { type: "SET_BUSINESS"; payload: { id: string; name: string } }
  | { type: "CLEAR_BUSINESS" }
  | { type: "TOGGLE_SIDEBAR" }
  | { type: "SET_SIDEBAR_COLLAPSED"; payload: boolean }
  | { type: "SET_ACTIVE_PANEL"; payload: string };

const initialState: WorkspaceState = {
  founderId: "",
  businessId: null,
  businessName: null,
  sidebarCollapsed: false,
  activePanel: "dashboard",
};

function workspaceReducer(
  state: WorkspaceState,
  action: WorkspaceAction
): WorkspaceState {
  switch (action.type) {
    case "SET_FOUNDER_ID":
      return { ...state, founderId: action.payload };
    case "SET_BUSINESS":
      return {
        ...state,
        businessId: action.payload.id,
        businessName: action.payload.name,
      };
    case "CLEAR_BUSINESS":
      return { ...state, businessId: null, businessName: null };
    case "TOGGLE_SIDEBAR":
      return { ...state, sidebarCollapsed: !state.sidebarCollapsed };
    case "SET_SIDEBAR_COLLAPSED":
      return { ...state, sidebarCollapsed: action.payload };
    case "SET_ACTIVE_PANEL":
      return { ...state, activePanel: action.payload };
    default:
      return state;
  }
}

interface WorkspaceContextValue {
  state: WorkspaceState;
  dispatch: React.Dispatch<WorkspaceAction>;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(workspaceReducer, initialState);

  useEffect(() => {
    let founderId = localStorage.getItem("fundfy_founder_id");
    if (!founderId) {
      founderId = generateUUID();
      localStorage.setItem("fundfy_founder_id", founderId);
    }
    dispatch({ type: "SET_FOUNDER_ID", payload: founderId });

    const businessId = localStorage.getItem("fundfy_business_id");
    const businessName = localStorage.getItem("fundfy_business_name");
    if (businessId && businessName) {
      dispatch({
        type: "SET_BUSINESS",
        payload: { id: businessId, name: businessName },
      });
    }
  }, []);

  useEffect(() => {
    if (state.businessId && state.businessName) {
      localStorage.setItem("fundfy_business_id", state.businessId);
      localStorage.setItem("fundfy_business_name", state.businessName);
    }
  }, [state.businessId, state.businessName]);

  return (
    <WorkspaceContext.Provider value={{ state, dispatch }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace(): WorkspaceContextValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return ctx;
}
