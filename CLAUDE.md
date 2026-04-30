# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
pip install -r requirements.txt
streamlit run pg_machine_app.py
```

### Prerequisites
1. **Neon PostgreSQL** — Create free DB at neon.tech, run `neon/migrations/001_schema.sql` in SQL console
2. **SendGrid account** — For email notifications (optional, app works without it)
3. **Secrets** — Fill `.streamlit/secrets.toml` with your `DATABASE_URL` (Neon connection string) and SendGrid API key

No test framework, linter, or build system is configured.

## Architecture

Multi-file Streamlit application with Neon PostgreSQL backend (psycopg2) for persistent multi-user data.

### File Structure
```
pg_machine_app.py          # Main app: auth gate + UI (no data logic)
lib/
  __init__.py
  db.py                    # Connection pool (psycopg2 ThreadedConnectionPool)
  auth.py                  # Login/register/session management (bcrypt local auth)
  dal.py                   # Data Access Layer (all psycopg2 CRUD)
  scheduler.py             # SLA checks on page load (replaces pg_cron)
  notifications.py         # SendGrid email notifications
  i18n.py                  # Internationalization (ES/EN)
  translations.py          # Translation dictionary
pages/
  respond.py               # Streamlit page for email response tokens
neon/
  migrations/
    001_schema.sql          # Full DB schema (no RLS, bcrypt auth)
    002_data_migration.py   # Supabase → Neon migration script
requirements.txt
.streamlit/secrets.toml    # Neon DATABASE_URL + SendGrid credentials (gitignored)
```

### Backend: Neon PostgreSQL
- **PostgreSQL** tables: teams, profiles, opportunities, activities, notifications, team_config, calendar_inbox, pipeline_snapshots, viajes
- **Application-level team isolation** via `team_id` WHERE clauses (no RLS)
- **On-page-load SLA checks** throttled to every 15 minutes (replaces pg_cron)
- **Streamlit page** (`pages/respond.py`) for handling email response tokens (replaces Edge Function)

### Connection Pool (lib/db.py)
- `psycopg2.pool.ThreadedConnectionPool` (min=1, max=3)
- `RealDictCursor` — all rows return as `dict`
- Exports: `fetch_all()`, `fetch_one()`, `execute()`, `execute_returning()`, `execute_returning_all()`

### Auth Flow (lib/auth.py)
- Local bcrypt authentication (no external auth provider)
- Session stored in `st.session_state["user"]`
- Three registration paths: Create Team, Join Team, Login
- First user of a team gets `admin` role
- 8 roles: `admin`, `vp`, `account_manager`, `regional_sales_manager`, `partner_manager`, `regional_partner_manager`, `presales_manager`, `presales`
- Role constants: `ALL_ROLES`, `JOINABLE_ROLES` (excludes admin), `ROLE_LABELS` (display names)
- `has_control_access()` — admin + vp + all manager roles (Control tab visibility)
- `can_see_all_opportunities()` — any authenticated user with a team_id
- Migrated users with temporary password are prompted to set a new one

### Data Access Layer (lib/dal.py)
All database operations go through DAL functions using raw psycopg2 SQL.
- `get_opportunities(team_id)`, `get_opportunities_for_user(team_id, user_id, role)`, `create_opportunity(...)`, `update_opportunity(...)`, `delete_opportunity(...)`
- `get_activities_for_opportunity(opp_id)`, `get_all_activities(team_id)`, `get_all_activities_for_user(team_id, user_id, role)`, `create_activity(...)`, `update_activity(...)`
- `get_team_members(team_id)`, `update_team_member(...)`, `get_all_members_for_team(team_id)`, `move_member_to_team(profile_id, new_team_id)`
- `get_all_teams()`, `create_team(name)`, `update_team(team_id, data)`, `delete_team(team_id)`
- `get_team_config(team_id, key)`, `set_team_config(team_id, key, value)`
- `get_sla_options(team_id)`, `get_sla_respuesta(team_id)`, `get_categorias(team_id)`
- Photo upload/delete functions removed (photos feature temporarily disabled)

### Notifications (lib/notifications.py)
- SendGrid for email delivery
- Triggers: assignment, SLA warning, SLA expired, blocked
- Response links point to `pages/respond.py` Streamlit page

### Admin Panel
- Visible only to users with `role = 'admin'`
- Team member CRUD (name, email, role with all 8 options, specialty, active/inactive)
- Admin can reset passwords for team members
- Team management: create new teams, rename teams, view all teams with role coverage, move members between teams, delete empty teams
- Configurable SLA options, response SLAs, and categories (stored as JSONB in team_config)
- Team invitation via email or shareable team ID
- Each team should have the full 8-role structure; admin console shows missing roles per team

## Data Model

**teams** — organizational units for data isolation
**profiles** — standalone with `password_hash` (bcrypt), team_id, role, email (UNIQUE)
**opportunities** — projects with cuenta, proyecto, monto, categoria, opp_id, stage, close_date, partner, kill tracking
**activities** — linked to opportunities, with SLA tracking, assignment, response tokens, photos (JSONB, UI disabled)
**notifications** — email queue for SLA alerts
**team_config** — per-team configurable settings (SLA options, categories, etc.)
**calendar_inbox** — queue for calendar events from external sync
**pipeline_snapshots** — weekly pipeline snapshots (JSONB)
**viajes** — trip planning with embedded visit checklist

## Conventions

- All code, comments, and UI text are in **Spanish**
- Custom CSS is embedded via `st.markdown()` with `unsafe_allow_html=True`
- Dictionary-based data model via psycopg2 RealDictCursor (no classes or ORM)
- Emojis used extensively in the UI for visual hierarchy
- Team-scoped data: all queries filter by `team_id` in WHERE clauses
- Role-scoped data: admin/VP see all team data, other roles see only owned + assigned data
- Mobile responsive: CSS media queries + JS-based `_mob` query param for layout adjustments
