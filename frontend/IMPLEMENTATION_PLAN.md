# Frontend Implementation Plan — Fundfy.ai Workspace UI

## Design Decisions

1. **Next.js 14 App Router** — Using the `app/` directory with layout.tsx as the shell. The workspace is a single-page app with a persistent sidebar and swappable main content panel using client-side routing (`/chat`, `/business`, `/execution`, `/documents`, `/communication`, `/dashboard`).

2. **State management: React Context + useReducer** — No external state library. A `WorkspaceContext` holds the current `founderId`, `businessId`, and sidebar state. These two IDs are generated client-side on first load and persisted in `localStorage`. This is sufficient for a single-founder V1 with no auth.

3. **API layer: plain fetch with a thin wrapper** — A single `lib/api.ts` module exports typed functions for each endpoint. No axios dependency; fetch is adequate and reduces bundle size.

4. **Styling: Tailwind CSS with a custom theme** — Dark mode as default via `class` strategy. Custom colors: `brand-pink: #FF6B6B`, `brand-purple: #8B5CF6`, gradient utility `bg-gradient-to-r from-brand-pink to-brand-purple`. All components use Tailwind; no component library.

5. **No authentication** — The `founderId` is a UUID stored in localStorage and sent with every request. No login page.

6. **Streaming appearance** — The backend `/api/chat` returns a full response (not SSE). We simulate streaming on the client by revealing the response text character-by-character with a short interval (typewriter effect).

---

## Implementation Steps

- [ ] 1. **Scaffold the Next.js project with TypeScript and Tailwind CSS.**
      Initialize the project at `/projects/sandbox/Fundfy/frontend/` using `npx create-next-app@latest` with App Router, TypeScript, Tailwind, ESLint, and no `src/` directory.
      Files: `frontend/` (generated scaffold)
      Verify: `cd frontend && npm run build` — builds successfully with zero errors.

- [ ] 2. **Configure Tailwind theme with brand colors and dark mode.**
      Edit `tailwind.config.ts` to add `darkMode: 'class'`, extend colors with `brand-pink` (#FF6B6B) and `brand-purple` (#8B5CF6), and add a `gradient-brand` utility. Update `app/globals.css` to set `<html class="dark">` styles, body background to slate-950, and default text to slate-100.
      Files: `frontend/tailwind.config.ts`, `frontend/app/globals.css`
      Verify: `npm run build` — no errors; inspect output confirms dark-mode classes present.

- [ ] 3. **Create the API client module with typed functions for all backend endpoints.**
      Create `lib/api.ts` exporting: `sendChat`, `createBusiness`, `getBusiness`, `executeObjective`, `getWorkstreams`, `generateDocument`, `getDocument`, `listDocuments`, `startCommunicationSession`, `healthCheck`. Each function calls `http://localhost:8000/api/...` and returns typed data matching the backend schemas. Define TypeScript interfaces matching the Pydantic response models in a `lib/types.ts` file.
      Files: `frontend/lib/api.ts`, `frontend/lib/types.ts`
      Verify: `npm run build` — compiles without type errors.

- [ ] 4. **Create the WorkspaceContext provider (founderId, businessId, sidebar state).**
      A React context in `lib/workspace-context.tsx` that initializes `founderId` from localStorage (or generates a new UUID), holds `businessId | null`, current active panel name, and sidebar collapsed state. Wrap the root layout with this provider.
      Files: `frontend/lib/workspace-context.tsx`
      Verify: `npm run build` — no errors.

- [ ] 5. **Build the root layout shell with sidebar and main content area.**
      `app/layout.tsx` renders a flex row: fixed-width Sidebar component on the left (w-64, collapsible to w-16) and a flex-1 main area. The Sidebar contains nav links for: Dashboard, Chat, Business Profile, Execution Timeline, Documents, Communication. Each links to its route. Active link highlighted with the brand gradient. The layout wraps children with `WorkspaceProvider`.
      Files: `frontend/app/layout.tsx`, `frontend/components/sidebar.tsx`
      Verify: `npm run dev` (manual) or `npm run build` — builds clean.

- [ ] 6. **Build the Dashboard/Home page (`/dashboard`).**
      A page at `app/dashboard/page.tsx` showing a welcome header ("Welcome to Fundfy.ai"), quick-stat cards (placeholder values for documents generated, active workstreams, readiness score), and quick-action buttons (Start Chat, Create Business, Generate Document) that navigate to respective panels. Make this the default redirect from `/` using `app/page.tsx` with a redirect to `/dashboard`.
      Files: `frontend/app/dashboard/page.tsx`, `frontend/app/page.tsx`
      Verify: `npm run build` — succeeds.

- [ ] 7. **Build the Chat page (`/chat`) — the primary conversational workspace.**
      Components: `app/chat/page.tsx`, `components/chat/chat-panel.tsx`, `components/chat/message-bubble.tsx`, `components/chat/chat-input.tsx`, `components/chat/mode-switcher.tsx`.
      - Messages stored in local state as `{role: 'user'|'assistant', content: string, timestamp: Date}[]`.
      - On submit, push user message, call `sendChat()`, then reveal the response with a typewriter animation (10ms per char using `setInterval`).
      - Mode switcher tabs at top: Chat, Mock Interview, Pitch Practice, Q&A Rehearsal. When a non-Chat mode is selected, messages route to the `/api/communication/session` endpoint instead.
      - Context indicator badge showing the active business name (from context) or "No business set".
      - Input bar pinned to bottom with a textarea and send button. Gradient border on focus.
      Files: `frontend/app/chat/page.tsx`, `frontend/components/chat/chat-panel.tsx`, `frontend/components/chat/message-bubble.tsx`, `frontend/components/chat/chat-input.tsx`, `frontend/components/chat/mode-switcher.tsx`
      Verify: `npm run build` — succeeds with no type errors.

- [ ] 8. **Build the Business Profile page (`/business`).**
      `app/business/page.tsx` with a form (name, industry, stage, goals textarea) and a display section. On submit, call `createBusiness()` and store the returned `businessId` in WorkspaceContext. If a business already exists (businessId in context), fetch and display it on mount via `getBusiness()`. Form inputs styled with dark backgrounds, brand-gradient submit button.
      Files: `frontend/app/business/page.tsx`, `frontend/components/business/business-form.tsx`
      Verify: `npm run build` — succeeds.

- [ ] 9. **Build the Execution Timeline page (`/execution`).**
      `app/execution/page.tsx` with two sections:
      - **Trigger panel**: text input for objective + optional context, button to call `executeObjective()`.
      - **Timeline display**: fetches workstreams via `getWorkstreams(businessId)` on mount and after execution. Renders a vertical timeline (or kanban columns: Pending / Running / Completed). Each task card shows type, status badge (color-coded), and result summary.
      Status badges: pending=yellow, running=blue pulse animation, completed=green.
      Files: `frontend/app/execution/page.tsx`, `frontend/components/execution/execution-trigger.tsx`, `frontend/components/execution/workstream-timeline.tsx`, `frontend/components/execution/task-card.tsx`
      Verify: `npm run build` — succeeds.

- [ ] 10. **Build the Document Center page (`/documents`).**
       `app/documents/page.tsx` with:
       - **Generate form**: dropdown for doc_type (Business Plan, Executive Summary, Pitch Deck, PRD, BRD, SOP, Financial Model, DPR, Company Profile), optional context textarea, Generate button calling `generateDocument()`.
       - **Document list**: calls `listDocuments(businessId)` on mount, renders cards with title, type badge, and "View" button.
       - **Document viewer modal/panel**: clicking View shows the full markdown content in a scrollable panel with a close button.
       Files: `frontend/app/documents/page.tsx`, `frontend/components/documents/document-generate-form.tsx`, `frontend/components/documents/document-list.tsx`, `frontend/components/documents/document-viewer.tsx`
       Verify: `npm run build` — succeeds.

- [ ] 11. **Build the Communication/Coaching page (`/communication`).**
       `app/communication/page.tsx` — a dedicated chat interface specifically for practice sessions.
       - Mode selector at top (Mock Interview, Pitch Practice, Q&A Rehearsal) — no plain "Chat" here since that's the main chat page.
       - Chat messages area and input, calling `startCommunicationSession()` with the selected mode.
       - Feedback styling: assistant messages get a subtle left-border with gradient color indicating coaching feedback.
       Files: `frontend/app/communication/page.tsx`, `frontend/components/communication/coaching-chat.tsx`
       Verify: `npm run build` — succeeds.

- [ ] 12. **Add loading states, error handling, and toast notifications.**
       Create a reusable `components/ui/loading-spinner.tsx`, `components/ui/error-message.tsx`, and `components/ui/toast.tsx`. Wrap all API calls in try/catch, show loading spinners during fetch, and display error toasts on failure. Add a toast container to the root layout.
       Files: `frontend/components/ui/loading-spinner.tsx`, `frontend/components/ui/error-message.tsx`, `frontend/components/ui/toast.tsx`, update `frontend/app/layout.tsx`
       Verify: `npm run build` — succeeds.

- [ ] 13. **Add responsive polish and transitions.**
       - Sidebar collapse/expand animation (transition-all duration-300).
       - Page content fade-in using CSS animation on mount.
       - Mobile: sidebar becomes a hamburger overlay at `md` breakpoint.
       - Chat message slide-in animation.
       - Gradient shimmer on loading states.
       Files: `frontend/app/globals.css` (animations), `frontend/components/sidebar.tsx` (responsive), various component tweaks.
       Verify: `npm run build` — succeeds.

- [ ] 14. **Create a `next.config.js` with API proxy rewrite and final build validation.**
       Add a `rewrites()` config that proxies `/api/:path*` to `http://localhost:8000/api/:path*` so the frontend can call `/api/chat` without CORS in production. Update `lib/api.ts` base URL to use relative `/api/` paths (works in both dev proxy and when backend CORS is enabled). Run full production build.
       Files: `frontend/next.config.js` (or `.mjs`), `frontend/lib/api.ts` (update base URL)
       Verify: `npm run build && npm run lint` — both pass with no errors or warnings.

---

## Dependency Order Summary

```
1 (scaffold) → 2 (theme) → 3 (API client) → 4 (context) → 5 (layout/sidebar)
     ↓
6 (dashboard), 7 (chat), 8 (business), 9 (execution), 10 (documents), 11 (communication)
     ↓               [all depend on 3, 4, 5]
12 (UX polish) → 13 (animations) → 14 (proxy + final build)
```

Steps 6–11 are independent of each other and can be done in any order, but all depend on steps 1–5 being complete.
