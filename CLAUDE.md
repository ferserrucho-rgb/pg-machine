# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
pip install -r requirements.txt
streamlit run pg_machine_app.py
```

### Prerequisites
1. **Supabase project** — Create at supabase.com, run `supabase/migrations/001_initial.sql` in SQL Editor
2. **SendGrid account** — For email notifications (optional, app works without it)
3. **Secrets** — Copy `.streamlit/secrets.toml` and fill in your Supabase URL/keys and SendGrid API key

No test framework, linter, or build system is configured.

## Architecture

Multi-file Streamlit application with Supabase backend for persistent multi-user data.

### File Structure
```
pg_machine_app.py          # Main app: auth gate + UI (no data logic)
lib/
  __init__.py
  auth.py                  # Login/register/session management (Supabase Auth)
  dal.py                   # Data Access Layer (all Supabase CRUD)
  notifications.py         # SendGrid email notifications
supabase/
  migrations/
    001_initial.sql        # Full DB schema + RLS + pg_cron
  functions/
    handle-response/
      index.ts             # Edge Function for email response tokens
requirements.txt
.streamlit/secrets.toml    # Supabase + SendGrid credentials (gitignored)
```

### Backend: Supabase
- **PostgreSQL** tables: teams, profiles, opportunities, activities, notifications, team_config
- **Row-Level Security** on all tables using `team_id` for data isolation
- **pg_cron** jobs for background SLA monitoring (every 15 min)
- **Edge Functions** for handling email response tokens

### Auth Flow (lib/auth.py)
- Supabase Auth with email/password
- Session persisted via `st.query_params` (survives Streamlit Cloud reruns)
- Three registration paths: Create Team, Join Team, Login
- First user of a team gets `admin` role

### Data Access Layer (lib/dal.py)
All database operations go through DAL functions. No direct `st.session_state.db_leads` usage.
- `get_opportunities(team_id)`, `create_opportunity(...)`, `update_opportunity(...)`, `delete_opportunity(...)`
- `get_activities_for_opportunity(opp_id)`, `get_all_activities(team_id)`, `create_activity(...)`, `update_activity(...)`
- `get_team_members(team_id)`, `update_team_member(...)`
- `get_team_config(team_id, key)`, `set_team_config(team_id, key, value)`
- `get_sla_options(team_id)`, `get_sla_respuesta(team_id)`, `get_categorias(team_id)`

### Notifications (lib/notifications.py)
- SendGrid for email delivery
- Triggers: assignment, SLA warning, SLA expired, blocked
- Background processing via pg_cron + Edge Functions

### Admin Panel
- Visible only to users with `role = 'admin'`
- Team member CRUD (name, email, role, specialty, active/inactive)
- Configurable SLA options, response SLAs, and categories (stored as JSONB in team_config)
- Team invitation via email or shareable team ID

## Data Model

**teams** — organizational units for data isolation
**profiles** — extends auth.users with team_id, role (admin/manager/presales), specialty
**opportunities** — projects with cuenta, proyecto, monto, categoria, opp_id, stage, close_date
**activities** — linked to opportunities, with SLA tracking, assignment, response tokens
**notifications** — email queue for SLA alerts
**team_config** — per-team configurable settings (SLA options, categories, etc.)

## Conventions

- All code, comments, and UI text are in **Spanish**
- Custom CSS is embedded via `st.markdown()` with `unsafe_allow_html=True`
- Dictionary-based data model via Supabase (no classes or ORM)
- Emojis used extensively in the UI for visual hierarchy
- Team-scoped data: all queries filter by `team_id` via RLS
