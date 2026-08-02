# Phase C — Real-World Integrations: Implementation Plan

## Prerequisites & Decisions

- **Token encryption**: Use `cryptography.fernet.Fernet` with a key derived from a new `FERNET_KEY` env var added to `Settings`. Tokens stored as encrypted blobs in the DB.
- **Google OAuth**: A single `GoogleOAuthToken` model stores access + refresh tokens per founder per service scope. The backend handles the OAuth2 code exchange; frontend redirects to Google consent.
- **SSE transport**: Use `sse-starlette` package for Server-Sent Events. Notification fanout via Redis pub/sub channel per founder.
- **CRM pipeline stages**: Enum values `lead, contacted, meeting, proposal, negotiation, closed_won, closed_lost`.
- **Investor/Grant DB**: Stored in PostgreSQL (searchable via SQL filters). Seeded with a JSON fixture loaded by an Alembic data migration.
- **Excel export**: Use `openpyxl` (new dependency). Financial model includes formulas as cell references.
- **Frontend**: New pages added to the existing Next.js app router at `frontend/app/`. No additional frontend dependencies needed (use built-in React 19 + Tailwind).

---

## Implementation Plan

- [ ] 1. **Add new Python dependencies to `pyproject.toml`.**
      Add `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`, `cryptography`, `openpyxl`, and `sse-starlette` to the `[project.dependencies]` list.
      Files: `pyproject.toml`
      Verify: `pip install -e ".[dev]"` completes without errors.

- [ ] 2. **Add Fernet encryption settings and utility module.**
      Add `FERNET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` to `fundfy/config.py` Settings class. Create `fundfy/crypto.py` with `encrypt_token(plaintext: str) -> str` and `decrypt_token(ciphertext: str) -> str` using Fernet.
      Files: `fundfy/config.py`, `fundfy/crypto.py`
      Verify: `pytest tests/test_crypto.py` — new unit tests for encrypt/decrypt round-trip pass.

- [ ] 3. **Create new database models for Google OAuth tokens, Investors, Grants, CRM, and Notifications.**
      Create model files following existing patterns (uuid PK, datetime columns, ForeignKey to founders/businesses):
      - `fundfy/models/oauth_token.py` — `GoogleOAuthToken` (id, founder_id, scopes, encrypted_access_token, encrypted_refresh_token, expires_at, created_at, updated_at)
      - `fundfy/models/investor.py` — `Investor` (id, name, firm, focus_areas_json, stage_preference, check_size_min, check_size_max, portfolio_json, contact_email, website, created_at)
      - `fundfy/models/grant.py` — `Grant` (id, name, provider, amount_min, amount_max, deadline, eligibility, url, industry, description, created_at)
      - `fundfy/models/grant_application.py` — `GrantApplication` (id, founder_id, grant_id, status, notes, applied_at, created_at)
      - `fundfy/models/contact.py` — `Contact` (id, founder_id, name, email, company, role, pipeline_stage, notes, last_interaction_at, created_at)
      - `fundfy/models/interaction.py` — `Interaction` (id, contact_id, founder_id, type, summary, occurred_at, created_at)
      - `fundfy/models/notification.py` — `Notification` (id, founder_id, type, title, body, read, data_json, created_at)
      Register all new models in `fundfy/models/__init__.py`.
      Files: `fundfy/models/oauth_token.py`, `fundfy/models/investor.py`, `fundfy/models/grant.py`, `fundfy/models/grant_application.py`, `fundfy/models/contact.py`, `fundfy/models/interaction.py`, `fundfy/models/notification.py`, `fundfy/models/__init__.py`
      Verify: `pytest tests/test_db.py` — existing DB tests still pass (auto-creates tables from metadata).

- [ ] 4. **Create Alembic migration for Phase C schema.**
      New migration file `alembic/versions/002_phase_c_integrations.py` with `revision="002"`, `down_revision="001"`. Creates all 7 new tables. Add an investor seed data step that inserts ~30 curated investors and ~20 grants from a JSON fixture at `fundfy/data/seed_investors.json` and `fundfy/data/seed_grants.json`.
      Files: `alembic/versions/002_phase_c_integrations.py`, `fundfy/data/seed_investors.json`, `fundfy/data/seed_grants.json`
      Verify: `alembic upgrade head` succeeds against a fresh SQLite test DB (set `DATABASE_URL=sqlite+aiosqlite:///./test_migration.db`).

- [ ] 5. **Implement Google OAuth service layer.**
      Create `fundfy/integrations/google_oauth.py` with:
      - `get_authorization_url(founder_id, scopes)` → returns Google consent URL with state token
      - `exchange_code(code, state)` → exchanges code for tokens, encrypts & stores in DB
      - `get_credentials(founder_id, scopes)` → loads tokens, refreshes if expired, returns `google.oauth2.credentials.Credentials`
      - `revoke_tokens(founder_id)` → revokes and deletes stored tokens
      Files: `fundfy/integrations/__init__.py`, `fundfy/integrations/google_oauth.py`
      Verify: `pytest tests/test_google_oauth.py` — tests with mocked Google endpoints pass.

- [ ] 6. **Implement Gmail integration service and agent tools.**
      Create `fundfy/integrations/gmail.py` with helper functions: `send_email(credentials, to, subject, body)`, `read_emails(credentials, query, max_results)`, `list_drafts(credentials)`, `create_draft(credentials, to, subject, body)`.
      Create `fundfy/tools/gmail_tools.py` with three tools extending `BaseTool`:
      - `SendEmailTool` — creates a pending-approval record, does NOT send immediately; returns draft for review
      - `ReadEmailsTool` — reads recent emails with optional query filter
      - `ManageDraftsTool` — list/create/delete Gmail drafts
      Files: `fundfy/integrations/gmail.py`, `fundfy/tools/gmail_tools.py`
      Verify: `pytest tests/test_gmail_tools.py` — tests with mocked Gmail API pass.

- [ ] 7. **Implement email approval workflow API endpoints.**
      Create `fundfy/api/routes_email.py` with:
      - `POST /api/email/approve/{draft_id}` — founder approves, actually sends via Gmail API
      - `POST /api/email/reject/{draft_id}` — marks draft as rejected
      - `GET /api/email/pending` — list drafts awaiting approval
      - `GET /api/email/sent` — list sent emails
      - `GET /api/email/received` — list received emails (from Gmail)
      Register router in `fundfy/main.py`.
      Files: `fundfy/api/routes_email.py`, `fundfy/main.py`
      Verify: `pytest tests/test_email_api.py` — endpoint tests with mocked Gmail pass.

- [ ] 8. **Implement Google Calendar integration service and agent tools.**
      Create `fundfy/integrations/calendar.py` with: `create_event(credentials, summary, start, end, attendees, meet_link=True)`, `list_events(credentials, time_min, time_max)`, `check_availability(credentials, time_min, time_max)`.
      Create `fundfy/tools/calendar_tools.py` with three tools:
      - `ScheduleMeetingTool` — creates a calendar event with Meet link
      - `CheckAvailabilityTool` — checks free/busy for a time range
      - `ListUpcomingMeetingsTool` — lists upcoming events
      Files: `fundfy/integrations/calendar.py`, `fundfy/tools/calendar_tools.py`
      Verify: `pytest tests/test_calendar_tools.py` — tests with mocked Calendar API pass.

- [ ] 9. **Implement Google Drive integration service and agent tool.**
      Create `fundfy/integrations/drive.py` with: `upload_file(credentials, file_path, folder_name)`, `ensure_folder(credentials, folder_name)`, `list_files(credentials, folder_name)`.
      Create `fundfy/tools/drive_tool.py` with `UploadToDriveTool` — uploads a generated file to founder's Drive in an organized folder structure (`Fundfy/Pitch Decks/`, `Fundfy/Business Plans/`, etc.).
      Files: `fundfy/integrations/drive.py`, `fundfy/tools/drive_tool.py`
      Verify: `pytest tests/test_drive_tool.py` — tests with mocked Drive API pass.

- [ ] 10. **Implement polished document exporters.**
       Rewrite `fundfy/tools/exporters.py` to add:
       - `export_pitch_deck(sections: dict) -> str` — Professional PPTX with 8 named slide layouts (Title, Problem, Solution, Market, Business Model, Traction, Team, Ask), brand colors, formatted text
       - `export_business_plan_pdf(title, sections: list[dict]) -> str` — PDF with TOC, headers/footers, page numbers using reportlab's `BaseDocTemplate` with PageTemplates
       - `export_financial_model(data: dict) -> str` — XLSX with sheets (Revenue, Costs, P&L, Cash Flow), cell formulas (`=SUM(...)`, `=B2-B3`), number formatting, and a basic chart via openpyxl
       Keep existing `export_markdown`, `export_pdf`, `export_docx`, `export_pptx` backward-compatible.
       Files: `fundfy/tools/exporters.py`
       Verify: `pytest tests/test_documents.py tests/test_exporters.py` — existing + new exporter tests pass; generated files are valid (check file size > 0 and correct extension).

- [ ] 11. **Implement Investor Database tool.**
       Create `fundfy/tools/investor_db_tool.py` with `SearchInvestorDatabaseTool` extending `BaseTool`. Accepts filters: `industry`, `stage`, `min_check_size`, `max_check_size`, `name_query`. Queries the `investors` table via SQLAlchemy async session. Returns structured results.
       Files: `fundfy/tools/investor_db_tool.py`
       Verify: `pytest tests/test_investor_db.py` — tests seed data into test DB, run tool, verify filtering works.

- [ ] 12. **Implement Grant Database and tracking tools.**
       Create `fundfy/tools/grant_db_tools.py` with:
       - `SearchGrantDatabaseTool` — filters by industry, amount range, deadline (upcoming), eligibility keywords
       - `TrackGrantApplicationTool` — creates/updates a `GrantApplication` record, triggers deadline reminders
       Auto-match logic: given a founder's business industry/stage, return matching grants sorted by relevance.
       Files: `fundfy/tools/grant_db_tools.py`
       Verify: `pytest tests/test_grant_db.py` — search and tracking tests pass.

- [ ] 13. **Implement CRM service and API endpoints.**
       Create `fundfy/api/routes_crm.py` with:
       - `POST /api/crm/contacts` — create contact
       - `GET /api/crm/contacts` — list contacts with pipeline_stage filter
       - `PATCH /api/crm/contacts/{id}` — update contact (including stage transitions)
       - `POST /api/crm/contacts/{id}/interactions` — log an interaction
       - `GET /api/crm/contacts/{id}/interactions` — list interactions
       - `GET /api/crm/pipeline` — grouped contacts by stage (for kanban view)
       Register router in `fundfy/main.py`.
       Files: `fundfy/api/routes_crm.py`, `fundfy/api/schemas.py` (add CRM schemas), `fundfy/main.py`
       Verify: `pytest tests/test_crm_api.py` — CRUD + pipeline endpoint tests pass.

- [ ] 14. **Implement Notification system with Redis pub/sub + SSE.**
       Create `fundfy/notifications/` package:
       - `fundfy/notifications/__init__.py`
       - `fundfy/notifications/publisher.py` — `publish_notification(founder_id, type, title, body, data)` publishes to Redis channel `notifications:{founder_id}` and persists to DB
       - `fundfy/notifications/subscriber.py` — async generator that subscribes to a Redis channel and yields events
       Create `fundfy/api/routes_notifications.py` with:
       - `GET /api/notifications/stream` — SSE endpoint using `sse-starlette`'s `EventSourceResponse`, subscribes to founder's channel
       - `GET /api/notifications` — list recent notifications
       - `PATCH /api/notifications/{id}/read` — mark as read
       Register router in `fundfy/main.py`.
       Files: `fundfy/notifications/__init__.py`, `fundfy/notifications/publisher.py`, `fundfy/notifications/subscriber.py`, `fundfy/api/routes_notifications.py`, `fundfy/main.py`
       Verify: `pytest tests/test_notifications.py` — publish/subscribe test with fakeredis, SSE endpoint returns events.

- [ ] 15. **Implement Google OAuth API endpoints.**
       Create `fundfy/api/routes_integrations.py` with:
       - `GET /api/integrations/google/authorize` — returns authorization URL
       - `GET /api/integrations/google/callback` — handles OAuth callback, stores tokens
       - `GET /api/integrations/google/status` — returns connected/disconnected status per scope
       - `POST /api/integrations/google/disconnect` — revokes and removes tokens
       Register router in `fundfy/main.py`.
       Files: `fundfy/api/routes_integrations.py`, `fundfy/main.py`
       Verify: `pytest tests/test_integrations_api.py` — OAuth flow tests with mocked Google endpoints pass.

- [ ] 16. **Register all new tools in the tool registry.**
       Update `fundfy/tools/registry.py` to instantiate and include: `SendEmailTool`, `ReadEmailsTool`, `ManageDraftsTool`, `ScheduleMeetingTool`, `CheckAvailabilityTool`, `ListUpcomingMeetingsTool`, `UploadToDriveTool`, `SearchInvestorDatabaseTool`, `SearchGrantDatabaseTool`, `TrackGrantApplicationTool`. Pass DB session factory + google_oauth service as dependencies. Update `create_tool_registry` signature to accept `async_session` and pass it to DB-backed tools.
       Files: `fundfy/tools/registry.py`, `fundfy/main.py` (pass session to registry), `fundfy/dependencies.py`
       Verify: `pytest tests/test_tools.py tests/test_react_agent.py` — existing tool tests + new registry tests pass.

- [ ] 17. **Wire notification triggers into integration points.**
       Add notification publishing calls to:
       - Email approval workflow (when email is sent successfully, when reply detected)
       - Calendar events (meeting reminders via scheduled worker task)
       - Grant deadline approaching (worker checks daily)
       - Background job completion
       Create `fundfy/worker/scheduled_tasks.py` with periodic tasks: `check_grant_deadlines`, `check_email_replies`, `send_meeting_reminders`. Register in `fundfy/worker/settings.py` cron jobs.
       Files: `fundfy/worker/scheduled_tasks.py`, `fundfy/worker/settings.py`
       Verify: `pytest tests/test_scheduled_tasks.py` — scheduled task logic tests pass with mocked dependencies.

- [ ] 18. **Frontend: Integrations settings page.**
       Create `frontend/app/integrations/page.tsx` with a Google OAuth connect/disconnect UI. Shows connection status for Gmail, Calendar, Drive. Connect button redirects to backend OAuth URL; disconnect calls the disconnect endpoint.
       Add "Integrations" nav item to `frontend/components/sidebar.tsx`.
       Files: `frontend/app/integrations/page.tsx`, `frontend/components/sidebar.tsx`
       Verify: `cd frontend && npm run build` — builds without errors.

- [ ] 19. **Frontend: Email panel.**
       Create `frontend/app/email/page.tsx` and `frontend/components/email/` with:
       - `email-list.tsx` — shows pending drafts, sent, received tabs
       - `email-approval-card.tsx` — card with approve/reject buttons for pending drafts
       - `email-compose.tsx` — form to trigger agent email drafting
       Add "Email" nav item to sidebar.
       Files: `frontend/app/email/page.tsx`, `frontend/components/email/email-list.tsx`, `frontend/components/email/email-approval-card.tsx`, `frontend/components/email/email-compose.tsx`, `frontend/components/sidebar.tsx`
       Verify: `cd frontend && npm run build` — builds without errors.

- [ ] 20. **Frontend: Calendar panel.**
       Create `frontend/app/calendar/page.tsx` and `frontend/components/calendar/` with:
       - `upcoming-meetings.tsx` — lists upcoming meetings from API
       - `schedule-form.tsx` — form to schedule a new meeting via agent
       Add "Calendar" nav item to sidebar.
       Files: `frontend/app/calendar/page.tsx`, `frontend/components/calendar/upcoming-meetings.tsx`, `frontend/components/calendar/schedule-form.tsx`, `frontend/components/sidebar.tsx`
       Verify: `cd frontend && npm run build` — builds without errors.

- [ ] 21. **Frontend: CRM/Pipeline panel.**
       Create `frontend/app/crm/page.tsx` and `frontend/components/crm/` with:
       - `pipeline-board.tsx` — kanban board with columns per stage, drag-and-drop via React state (no extra lib)
       - `contact-card.tsx` — compact card showing name, company, stage, last interaction
       - `contact-detail-modal.tsx` — modal showing full contact info + interaction history
       - `add-contact-form.tsx` — form to create a new contact
       Add "CRM" nav item to sidebar.
       Files: `frontend/app/crm/page.tsx`, `frontend/components/crm/pipeline-board.tsx`, `frontend/components/crm/contact-card.tsx`, `frontend/components/crm/contact-detail-modal.tsx`, `frontend/components/crm/add-contact-form.tsx`, `frontend/components/sidebar.tsx`
       Verify: `cd frontend && npm run build` — builds without errors.

- [ ] 22. **Frontend: Notification center.**
       Create `frontend/components/notifications/` with:
       - `notification-bell.tsx` — bell icon in top bar with unread count badge, opens dropdown
       - `notification-dropdown.tsx` — dropdown list of recent notifications, click to mark read
       - `use-notifications.ts` — custom hook that connects to SSE `/api/notifications/stream` and manages state
       Integrate notification bell into `frontend/app/client-layout.tsx` (top bar area).
       Files: `frontend/components/notifications/notification-bell.tsx`, `frontend/components/notifications/notification-dropdown.tsx`, `frontend/components/notifications/use-notifications.ts`, `frontend/app/client-layout.tsx`
       Verify: `cd frontend && npm run build` — builds without errors.

- [ ] 23. **Frontend: Update API client and types.**
       Add new API functions and TypeScript types for: email endpoints, calendar endpoints, CRM endpoints, notifications endpoints, integrations endpoints.
       Files: `frontend/lib/api.ts`, `frontend/lib/types.ts`
       Verify: `cd frontend && npm run build` — builds without errors.

- [ ] 24. **Write comprehensive integration tests for Phase C.**
       Create `tests/test_phase_c_integration.py` that tests the full flows:
       - OAuth connect → Gmail send with approval → notification fires
       - Investor DB search returns seeded data
       - Grant tracking with deadline notification
       - CRM contact creation → interaction logging → pipeline view
       All Google APIs mocked. Uses the test DB fixture from `conftest.py`.
       Files: `tests/test_phase_c_integration.py`
       Verify: `pytest tests/ -v --tb=short` — all tests pass (existing 60 + new Phase C tests).

- [ ] 25. **Update Docker Compose and CI workflow.**
       Add `FERNET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` env vars to `docker-compose.yml` backend and worker services. Update `.env.example` with new vars. Add Phase C dependencies to CI test job pip install step (already covered by `pip install -e ".[dev]"`). No CI changes needed if `pyproject.toml` is correct.
       Files: `docker-compose.yml`, `.env.example`
       Verify: `docker compose config` — validates without errors.

- [ ] 26. **Update README with Phase C features and setup instructions.**
       Add a "Phase C — Integrations" section documenting: Google OAuth setup (how to create credentials), CRM usage, notification system, and new agent tools.
       Files: `README.md`
       Verify: File renders correctly (manual check; no automated verification needed).

---

## Dependency Order Summary

Steps 1 → 2 → 3 → 4 are sequential (each depends on prior).
Steps 5 depends on 2+3.
Steps 6, 8, 9 depend on 5.
Step 7 depends on 6.
Step 10 depends on 1.
Steps 11, 12 depend on 3+4.
Step 13 depends on 3+4.
Step 14 depends on 1+3.
Step 15 depends on 5.
Step 16 depends on 6, 8, 9, 11, 12.
Step 17 depends on 14, 16.
Steps 18-22 depend on 15, 7, 8, 13, 14 (backend APIs must exist).
Step 23 depends on 18-22.
Step 24 depends on all backend steps (1-17).
Step 25 depends on 1.
Step 26 is last.
