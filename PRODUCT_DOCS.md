# PG Machine — Product & Technical Documentation

## 1. Overview

PG Machine is a **multi-tenant opportunity management platform** designed for sales teams. It provides end-to-end tracking of opportunities (deals/projects) and their associated activities (emails, calls, meetings, assignments), with SLA monitoring, role-based access control, email notifications, and Excel bulk import.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | [Streamlit](https://streamlit.io) (Python) with custom HTML/CSS/JS |
| Backend / Database | [Supabase](https://supabase.com) (PostgreSQL + Auth + Edge Functions) |
| Email Notifications | [SendGrid](https://sendgrid.com) |
| Guided Tour | [Driver.js](https://driverjs.com) v1.4 |
| Mobile | PWA-ready via Streamlit responsive design |

### Key Features

- Multi-team data isolation via Row-Level Security (RLS)
- 8-role permission system (admin through presales)
- Opportunity scorecards grouped by category and account
- Activity lifecycle: Pendiente → Enviada → Respondida (with traffic-light SLA tracking)
- Excel bulk import with 2-step analyze/execute workflow and diff detection
- Configurable SLAs, response SLAs, and categories per team
- Email notifications for assignments, SLA warnings, SLA expiration, and blocked activities
- Edge Function for email-based activity responses (no login required)
- Control panel with daily/weekly analytics and per-member performance
- Guided interactive tour (Driver.js) with role-specific steps
- Dynamic column discovery on the opportunities table

---

## 2. Architecture

### File Structure

```
pg_machine_app.py              # Main app: auth gate, UI, all tabs (~2500 lines)
lib/
  __init__.py
  auth.py                      # Login/register/session (Supabase Auth)
  dal.py                       # Data Access Layer (all Supabase CRUD)
  notifications.py             # SendGrid email notifications
supabase/
  migrations/
    001_initial.sql            # Full DB schema + RLS + pg_cron
    002_expand_roles.sql       # Expand 3-role to 8-role system
    003_respondida_ts.sql      # Add respondida_ts column
    003_add_partner.sql        # Add partner column to opportunities
  functions/
    handle-response/
      index.ts                 # Edge Function for email response tokens
requirements.txt               # Python dependencies
.streamlit/secrets.toml        # Supabase + SendGrid credentials (gitignored)
CLAUDE.md                      # Development guidance
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User's Browser                            │
│  ┌─────────────┐   ┌──────────┐   ┌───────────────────┐    │
│  │  Streamlit   │   │ Driver.js│   │ Custom JS (cards, │    │
│  │  Components  │   │  (Tour)  │   │ buttons, overlay) │    │
│  └──────┬───────┘   └──────────┘   └───────────────────┘    │
└─────────┼───────────────────────────────────────────────────┘
          │ HTTP (Streamlit protocol)
┌─────────▼───────────────────────────────────────────────────┐
│                  Streamlit Server                             │
│  ┌────────────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │pg_machine_app.py│  │ lib/auth │  │lib/notifications │    │
│  │  (UI + Logic)   │  │  (.py)   │  │     (.py)        │    │
│  └────────┬────────┘  └────┬─────┘  └────────┬─────────┘    │
│           │                │                  │              │
│  ┌────────▼────────────────▼──────────────────▼─────────┐   │
│  │                    lib/dal.py                          │   │
│  │              (Data Access Layer)                       │   │
│  └────────────────────────┬──────────────────────────────┘   │
└───────────────────────────┼──────────────────────────────────┘
                            │ HTTPS (Supabase client SDK)
┌───────────────────────────▼──────────────────────────────────┐
│                      Supabase                                 │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐ │
│  │PostgreSQL │  │ Auth     │  │ pg_cron │  │Edge Functions│ │
│  │ (6 tables)│  │(JWT+RLS) │  │(SLA mon)│  │(handle-resp) │ │
│  └──────────┘  └──────────┘  └─────────┘  └──────────────┘ │
└──────────────────────────────────────────────────────────────┘
                                                    │
                            ┌───────────────────────▼──────┐
                            │         SendGrid              │
                            │  (Email delivery)             │
                            └──────────────────────────────┘
```

### How Streamlit + Supabase Interact

1. **Auth gate**: `require_auth()` in `lib/auth.py` runs before any UI. It checks `st.session_state` and `st.query_params` for an existing session. If none, it shows the login/register page.
2. **Session persistence**: After login, tokens are stored in `st.query_params` (`_rt` and `_at`) so they survive Streamlit Cloud reruns (which reset `st.session_state`).
3. **Data access**: All database operations go through `lib/dal.py`, which uses the Supabase Python client with the user's JWT. RLS policies automatically enforce team-level data isolation.
4. **Custom JS**: A `components.html()` block injects JavaScript into Streamlit's parent document for click delegation (cards, buttons), category button styling, loading overlay, and mobile detection.

---

## 3. Setup & Deployment

### Prerequisites

- Python 3.10+
- A [Supabase](https://supabase.com) project (free tier works)
- A [SendGrid](https://sendgrid.com) account (optional — app works without it)

### Local Development

```bash
# 1. Clone the repository
git clone <repo-url>
cd "PG Machine"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your credentials
```

**`.streamlit/secrets.toml`** format:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "eyJ..."                      # anon/public key
SUPABASE_SERVICE_KEY = "eyJ..."              # service_role key (for admin operations)
SENDGRID_API_KEY = "SG.your-key"             # optional
SENDGRID_FROM_EMAIL = "noreply@yourdomain.com"
SENDGRID_FROM_NAME = "PG Machine"
APP_URL = "http://localhost:8501"            # or your deployed URL
```

```bash
# 4. Initialize database
# Go to Supabase Dashboard → SQL Editor → New query
# Run migrations in order:
#   001_initial.sql
#   002_expand_roles.sql
#   003_respondida_ts.sql
#   003_add_partner.sql

# 5. Run the app
streamlit run pg_machine_app.py
```

### Production: Streamlit Cloud

1. Push code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) → "New app"
3. Select your repo, branch, and `pg_machine_app.py` as the main file
4. Add secrets in the Streamlit Cloud dashboard (Settings → Secrets) using the same `secrets.toml` format
5. Deploy

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service_role key (bypasses RLS for admin ops) |
| `SENDGRID_API_KEY` | No | SendGrid API key for email notifications |
| `SENDGRID_FROM_EMAIL` | No | Sender email address |
| `SENDGRID_FROM_NAME` | No | Sender display name |
| `APP_URL` | No | Public URL of the deployed app |

---

## 4. Database Schema

Six PostgreSQL tables, all with RLS enabled:

### `teams`

Organizational units for data isolation.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `name` | TEXT | Team name |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

**Trigger**: `seed_team_config` — on INSERT, automatically creates default SLA, category, and response SLA config entries in `team_config`.

### `profiles`

Extends Supabase `auth.users` with app-specific data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK, FK → auth.users) | Same as auth user ID |
| `team_id` | UUID (FK → teams) | Team membership |
| `full_name` | TEXT | Display name |
| `email` | TEXT | User email |
| `role` | TEXT | One of 8 roles (CHECK constraint) |
| `phone` | TEXT | Phone number |
| `specialty` | TEXT | Area of expertise |
| `active` | BOOLEAN | Active/inactive toggle |
| `created_at` | TIMESTAMPTZ | Registration timestamp |

**Indexes**: `team_id`, `email`

### `opportunities`

Sales opportunities (deals/projects).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `team_id` | UUID (FK → teams) | Team ownership |
| `owner_id` | UUID (FK → profiles) | Creator/owner |
| `proyecto` | TEXT | Project/opportunity name |
| `cuenta` | TEXT | Account/company name |
| `monto` | NUMERIC | Annual Contract Value (ACV) in USD |
| `categoria` | TEXT | Category: LEADS, OFFICIAL, GTM |
| `opp_id` | TEXT | External opportunity ID (e.g. SFDC) |
| `stage` | TEXT | Deal stage |
| `partner` | TEXT | Partner name |
| `close_date` | DATE | Expected close date |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Auto-updated via trigger |

**Note**: The table supports **dynamic columns** — any additional columns added via ALTER TABLE are auto-discovered by the app (see section 10).

**Indexes**: `team_id`, `owner_id`, `(team_id, categoria)`

**Trigger**: `update_updated_at` — auto-updates `updated_at` on every UPDATE.

### `activities`

Actions linked to opportunities with SLA tracking.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `opportunity_id` | UUID (FK → opportunities, CASCADE) | Parent opportunity |
| `team_id` | UUID (FK → teams) | Team ownership |
| `created_by` | UUID (FK → profiles) | Creator |
| `assigned_to` | UUID (FK → profiles, nullable) | Assigned team member |
| `tipo` | TEXT | Channel: Email, Llamada, Reunión, Asignación |
| `fecha` | DATE | Scheduled date |
| `objetivo` | TEXT | Objective/goal |
| `descripcion` | TEXT | Description/notes |
| `estado` | TEXT | Status: Pendiente, Enviada, Respondida |
| `sla_key` | TEXT | SLA option key (e.g. "Urgente (2-4h)") |
| `sla_hours` | INTEGER | SLA deadline in hours |
| `sla_deadline` | TIMESTAMPTZ | Calculated SLA deadline |
| `sla_respuesta_dias` | INTEGER | Response SLA in days (default 7) |
| `destinatario` | TEXT | Recipient name/contact |
| `enviada_ts` | TIMESTAMPTZ | Timestamp when marked as Enviada |
| `response_deadline` | TIMESTAMPTZ | Calculated response deadline |
| `respondida_ts` | DATE | Date when customer responded |
| `feedback` | TEXT | Customer feedback text |
| `response_token` | TEXT | Unique token for email-based responses |
| `token_expires_at` | TIMESTAMPTZ | Token expiration (48h) |

**Indexes**: `opportunity_id`, `team_id`, `assigned_to`, `estado`, partial indexes on `sla_deadline` and `response_deadline` for pending/sent activities, partial index on `response_token`.

### `notifications`

Email notification queue.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `team_id` | UUID (FK → teams) | Team ownership |
| `activity_id` | UUID (FK → activities, CASCADE) | Related activity |
| `recipient_id` | UUID (FK → profiles) | Notification recipient |
| `type` | TEXT | assignment, sla_warning, sla_expired, blocked |
| `sent` | BOOLEAN | Whether email was sent |
| `sent_at` | TIMESTAMPTZ | Send timestamp |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

**Indexes**: partial index on `sent = false`, `activity_id`.

### `team_config`

Per-team configurable settings stored as JSONB.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Auto-generated |
| `team_id` | UUID (FK → teams) | Team ownership |
| `key` | TEXT | Config key |
| `value` | JSONB | Config value |

**Unique constraint**: `(team_id, key)` — enables upsert behavior.

**Default keys** (seeded automatically on team creation):

- `sla_opciones` — SLA deadline options with hours/days and colors
- `sla_respuesta` — Response SLA options (days)
- `categorias` — Array of opportunity category names

### Row-Level Security (RLS)

All tables have RLS enabled. A helper function `get_my_team_id()` returns the authenticated user's `team_id`:

```sql
CREATE FUNCTION get_my_team_id() RETURNS UUID AS $$
    SELECT team_id FROM profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;
```

Every SELECT/INSERT/UPDATE/DELETE policy checks `team_id = get_my_team_id()`, ensuring complete team isolation at the database level.

**Exception**: The `teams` table allows INSERT for registration (new users don't have a profile yet), and admin operations use the `SUPABASE_SERVICE_KEY` to bypass RLS.

### Entity Relationships

```
teams 1──┬──N profiles
         ├──N opportunities 1──N activities
         ├──N notifications
         └──N team_config

profiles 1──N opportunities (owner_id)
profiles 1──N activities (created_by, assigned_to)
profiles 1──N notifications (recipient_id)
```

---

## 5. Authentication & Roles

### Auth Flow (`lib/auth.py`)

1. **`require_auth()`** — called at the top of `pg_machine_app.py` before any UI
   - Tries to restore session from `st.query_params` tokens
   - If no session, shows the auth page (login/register/join)
   - Returns `True` if authenticated, `False` otherwise

2. **Registration paths**:
   - **Create Team**: registers user + creates new team + creates profile with `role = 'admin'`
   - **Join Team**: registers user + creates profile in existing team with chosen role
   - **Login**: authenticates existing user

3. **Session persistence**: tokens stored in `st.query_params["_rt"]` (refresh) and `st.query_params["_at"]` (access) to survive Streamlit Cloud reruns.

### 8-Role System

| Role | Label | `can_see_all_opportunities()` | `has_control_access()` | `is_admin()` |
|------|-------|------|------|------|
| `admin` | Admin | Yes | Yes | Yes |
| `vp` | VP | Yes | Yes | No |
| `account_manager` | Account Manager | No | Yes | No |
| `regional_sales_manager` | Regional Sales Manager | No | Yes | No |
| `partner_manager` | Partner Manager | No | Yes | No |
| `regional_partner_manager` | Regional Partner Manager | No | Yes | No |
| `presales_manager` | Presales Manager | No | Yes | No |
| `presales` | Presales | No | No | No |

### Access Functions

- **`is_admin()`** — only `admin` role. Full platform access including team/config management.
- **`has_control_access()`** — all roles except `presales`. Controls visibility of the Control (analytics) tab.
- **`can_see_all_opportunities()`** — only `admin` and `vp`. Other roles see only opportunities they own or have activities assigned to them.
- **`is_manager_or_admin()`** — legacy function for `admin`, `manager`, `account_manager`.

### Data Scoping Rules

- **Admin/VP**: see all opportunities and activities in the team
- **All other roles**: see opportunities where `owner_id = user_id` OR where they have activities with `assigned_to = user_id` or `created_by = user_id`

### Role Constants

```python
ALL_ROLES = ["admin", "vp", "account_manager", "regional_sales_manager",
             "partner_manager", "regional_partner_manager", "presales_manager", "presales"]

JOINABLE_ROLES = [r for r in ALL_ROLES if r != "admin"]  # admin excluded from self-registration

ROLE_LABELS = {
    "admin": "Admin", "vp": "VP", "account_manager": "Account Manager",
    "regional_sales_manager": "Regional Sales Manager", ...
}
```

---

## 6. Data Access Layer (DAL)

All database operations are in `lib/dal.py`. No direct Supabase calls exist outside this module.

### Opportunities

| Function | Description |
|----------|-------------|
| `get_opportunities(team_id)` | All opportunities for a team, ordered by monto DESC |
| `get_opportunities_for_user(team_id, user_id, role)` | Role-scoped: admin/VP get all; others get owned + assigned |
| `get_opportunity(opp_id)` | Single opportunity by ID |
| `get_opportunity_extra_columns(team_id)` | Discovers dynamic columns (see section 10) |
| `create_opportunity(team_id, owner_id, data)` | Creates with dynamic field pass-through |
| `update_opportunity(opp_id, data)` | Updates with dynamic field pass-through |
| `delete_opportunity(opp_id)` | Deletes (CASCADE deletes activities) |
| `delete_opportunities_by_account(team_id, cuenta)` | Bulk delete by account name |
| `bulk_create_opportunities(team_id, owner_id, items)` | Bulk insert for Excel import |

### Activities

| Function | Description |
|----------|-------------|
| `get_activities_for_opportunity(opp_id)` | Activities for one opportunity with joined profile data |
| `get_all_activities(team_id)` | All team activities with opportunity + profile joins |
| `get_all_activities_for_user(team_id, user_id, role)` | Role-scoped activities |
| `create_activity(opp_id, team_id, created_by, data)` | Creates with SLA deadline calculation + response token generation |
| `update_activity(act_id, data)` | Updates; auto-calculates `response_deadline` when estado → Enviada |
| `delete_activity(act_id)` | Deletes single activity |

### Team Members

| Function | Description |
|----------|-------------|
| `get_team_members(team_id, active_only)` | Team profiles, optionally filtered to active |
| `get_team_member(profile_id)` | Single profile by ID |
| `update_team_member(profile_id, data)` | Update profile fields |
| `delete_team_member(profile_id)` | Deletes profile + auth user |
| `get_all_members_for_team(team_id)` | All members (bypasses RLS via service key) |
| `move_member_to_team(profile_id, new_team_id)` | Moves member to different team |

### Teams

| Function | Description |
|----------|-------------|
| `get_team(team_id)` | Single team info |
| `get_all_teams()` | All teams (bypasses RLS) |
| `create_team(name)` | Creates new team |
| `update_team(team_id, data)` | Updates team info |
| `delete_team(team_id)` | Deletes team (CASCADE) |

### Team Config

| Function | Description |
|----------|-------------|
| `get_team_config(team_id, key)` | Get config value by key |
| `set_team_config(team_id, key, value)` | Upsert config value |
| `get_sla_options(team_id)` | SLA deadline options (with defaults) |
| `get_sla_respuesta(team_id)` | Response SLA options (with defaults) |
| `get_categorias(team_id)` | Category names (with defaults) |

### Notifications

| Function | Description |
|----------|-------------|
| `create_notification(team_id, activity_id, recipient_id, type)` | Queue a notification |
| `get_unsent_notifications()` | Fetch unsent with joined recipient + activity data |
| `mark_notification_sent(notif_id)` | Mark as sent with timestamp |

### Admin Supabase Client

`_get_admin_supabase()` returns a Supabase client initialized with `SUPABASE_SERVICE_KEY` (bypasses RLS). Used for cross-team operations: `get_all_teams`, `create_team`, `update_team`, `delete_team`, `get_all_members_for_team`, `move_member_to_team`, `delete_team_member`.

---

## 7. SLA System

PG Machine has two types of SLAs:

### Activity SLA (Deadline)

Tracks how long an activity can remain in "Pendiente" status before it's considered overdue.

- **Configuration**: stored in `team_config` under key `sla_opciones`
- **Default options**:
  - Urgente (2-4h): 4 hours
  - Importante (2d): 2 days (48h)
  - No urgente (7d): 7 days (168h)
- **Calculation**: `sla_deadline = created_at + sla_hours`
- **Traffic light**:
  - `>50%` remaining → green
  - `<50%` remaining → yellow
  - Expired → red ("Vencida")

### Response SLA

Tracks how long a customer can take to respond after an activity is marked "Enviada".

- **Configuration**: stored in `team_config` under key `sla_respuesta`
- **Default options**: 3 days, 1 week, 2 weeks, 1 month
- **Calculation**: `response_deadline = enviada_ts + sla_respuesta_dias`
- **Traffic light**:
  - Waiting → purple ("Esp. rpta Xd")
  - Expired → red ("Bloqueada")

### pg_cron Monitoring

Three cron jobs run every 15 minutes (must be enabled manually in Supabase):

1. **`check-sla-expired`**: finds Pendiente activities past `sla_deadline`, creates `sla_expired` notifications
2. **`check-blocked`**: finds Enviada activities past `response_deadline`, creates `blocked` notifications
3. **`check-sla-warning`**: finds Pendiente activities where `<50%` time remains, creates `sla_warning` notifications

All cron jobs use `NOT EXISTS` to prevent duplicate notifications.

### Traffic Light Function (`_traffic_light`)

Located in `pg_machine_app.py`, this function computes a visual status indicator for each activity:

| Emoji | Status | Condition |
|-------|--------|-----------|
| `🟩` | Respondida | Activity completed |
| `🟪` | Esp. rpta Xd | Enviada, waiting for response within SLA |
| `🟥` | Bloqueada | Enviada, response SLA expired |
| `🔵` | Programada DD/MM | Pendiente, scheduled date in the future |
| `🟧` | Hoy | Pendiente, scheduled for today |
| `🟩` | Xh/Xd rest. | Pendiente, `>50%` of SLA remaining |
| `🟨` | Xh/Xd rest. | Pendiente, `<50%` of SLA remaining |
| `🟥` | Vencida | Pendiente, SLA expired |

---

## 8. Notification System

### SendGrid Integration (`lib/notifications.py`)

- **`_get_sendgrid()`**: returns a SendGrid client or `None` if not configured
- Email templates use inline HTML with the PG Machine visual style (dark header, white card body)

### Notification Types

| Type | Trigger | Recipient |
|------|---------|-----------|
| `assignment` | Activity created with `assigned_to` | Assigned team member |
| `sla_warning` | SLA `<50%` remaining (pg_cron) | Assigned member or creator |
| `sla_expired` | SLA deadline passed (pg_cron) | Assigned member or creator |
| `blocked` | Response deadline passed (pg_cron) | Activity creator |

### Assignment Notification Flow

1. User creates activity with an assigned team member
2. `dal.create_activity()` generates a `response_token` (48h expiry)
3. `notifications.send_assignment_notification()` sends an HTML email with activity details and a "Responder desde el celular" button linking to the Edge Function

### Response Token Flow

1. Assignment email includes a link: `{SUPABASE_URL}/functions/v1/handle-response?token=<token>`
2. Recipient clicks link → Edge Function shows a mobile-friendly HTML form
3. Recipient submits feedback → Edge Function updates activity to "Respondida" with the feedback text
4. Token is cleared after use to prevent reuse

### Edge Function (`supabase/functions/handle-response/index.ts`)

- Deno-based Supabase Edge Function
- Handles GET (show form) and POST (process response)
- Validates token existence, activity association, and expiration
- Uses the `SUPABASE_SERVICE_ROLE_KEY` to bypass RLS for updates
- Returns styled HTML pages for all states (form, success, error, expired)

### Pending Notification Processing

`notifications.process_pending_notifications()` fetches all unsent notifications and sends them via SendGrid, marking each as sent. This can be called manually or by the Edge Function.

---

## 9. Excel Import

### Two Import Formats

#### Leads Propios

Source: custom lead tracking spreadsheets.

| Excel Column | Maps to | Default |
|-------------|---------|---------|
| Proyecto | `proyecto` | — |
| Empresa / Cuenta | `cuenta` | — |
| Annual Contract Value (ACV) / Valor / Monto | `monto` | 0 |
| Close Date | `close_date` | null |
| Partner | `partner` | '' |
| *(category forced)* | `categoria` | "LEADS" |

#### Forecast BMC (Official)

Source: Salesforce/BMC export files.

| Excel Column | Maps to | Default |
|-------------|---------|---------|
| Opportunity Name | `proyecto` | — |
| Account Name | `cuenta` | — |
| Annual Contract Value (ACV) / Amount (USD) | `monto` | 0 |
| SFDC Opportunity Id / BMC Opportunity Id | `opp_id` | '' |
| Stage | `stage` | '' |
| Close Date | `close_date` | null |
| Partner | `partner` | '' |
| *(category forced)* | `categoria` | "OFFICIAL" |

### 2-Step Analyze/Execute Workflow

**Step 1: Analyze** (`Analizar Archivo` button)

1. Parse Excel with pandas
2. Map columns to opportunity fields based on selected format
3. Compare each row against existing opportunities:
   - Match by `opp_id` first (for Official/Forecast)
   - Then match by `(proyecto, cuenta)` composite key
4. Classify into three buckets:
   - **New**: no match found
   - **Unchanged**: match found, all compared fields identical
   - **Changed**: match found, some fields differ
5. Display results with individual checkboxes for new items and changed items
6. Changed items show a tooltip with field-by-field diff

**Step 2: Execute** (`Ejecutar Importación` button)

1. Create selected new opportunities via `dal.bulk_create_opportunities()`
2. Update selected changed opportunities via `dal.update_opportunity()`
3. Skip unchanged opportunities
4. Display summary: "X creadas, Y actualizadas, Z sin cambios, W omitidas"

### Template Downloads

Both formats have downloadable `.xlsx` templates with the correct column headers, generated on-the-fly with openpyxl.

### Date Parsing

The `_parse_date()` function handles multiple date formats:
- `YYYY-MM-DD`, `Mon DD, YYYY`, `DD/MM/YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD HH:MM:SS`
- Falls back to pandas `to_datetime()` for ambiguous formats

---

## 10. Dynamic Columns

### How Extra Columns Are Discovered

`dal.get_opportunity_extra_columns(team_id)` fetches one row from `opportunities` and compares its keys against two exclusion sets:

```python
SYSTEM_COLS = {"id", "team_id", "owner_id", "created_at", "updated_at"}
UI_COLS = {"proyecto", "cuenta", "monto", "categoria", "opp_id", "stage", "close_date", "partner"}
```

Any column not in either set is considered a "dynamic" extra column and returned as a sorted list.

### Where Dynamic Columns Appear

1. **Manual creation form** (sidebar): extra text inputs are generated for each dynamic column
2. **Edit opportunity form** (detail view): same, with current values pre-filled
3. **Opportunity scorecards** (dashboard): extra columns shown as pills on the card
4. **Detail meta-bar**: extra columns shown as badge pills
5. **Excel import diff comparison**: dynamic columns included in the `compare_fields` list

### Adding a New Dynamic Column

To add a new column (e.g., `region`):

```sql
ALTER TABLE opportunities ADD COLUMN region TEXT DEFAULT '';
```

The app will automatically discover it on the next page load. No code changes needed.

---

## 11. Guided Tour

### Technology

[Driver.js](https://driverjs.com) v1.4 loaded via CDN. Custom CSS overrides match the PG Machine visual style.

### Role-Specific Steps

The tour builds steps dynamically based on the user's role:

1. **Welcome** — shows role name and role-specific description
2. **Sidebar** (desktop only) — profile, logout, Excel import, Tour button
3. **Tab bar** — navigation overview
4. **Tablero tab** — scorecards and category filters
5. **Actividades tab** — activity table and filters
6. **Presales-specific step** (if role is `presales`) — emphasizes "Mis tareas" workflow
7. **Historial tab** — chronological view
8. **Control tab** (if `has_control_access`) — analytics dashboard
9. **Equipo tab** — team management (admin gets expanded description)
10. **Excel import** (desktop only) — sidebar expander
11. **Finish** — reminder about Tour button

### First-Visit Detection

- Uses `localStorage` key: `pgm_tour_seen_{role}`
- Tour auto-starts on first visit for each role
- `markTourSeen()` sets the key after tour completion or dismissal
- Manual replay via the **Tour** button in the sidebar (sets `st.session_state["_trigger_tour"]`)

### Anti-Rerun Protection

- `doc._pgmTourActive` flag prevents re-triggering during Streamlit reruns
- Polls for DOM readiness (tab list + Driver.js loaded) with 50 attempts at 100ms intervals

---

## 12. Mobile Responsiveness

### CSS Media Queries

Two breakpoints in the embedded CSS:

- **768px**: columns stack to 100% width, larger touch targets (48px min-height), 16px font for inputs
- **480px**: further reduced font sizes for very small screens

### JS-Based Mobile Detection

```javascript
if (window.parent.innerWidth <= 768) {
    params.set('_mob', '1');
}
```

The `_mob=1` query parameter is detected in Python via `st.query_params.get("_mob")`, and the `is_mobile` flag controls layout decisions:

- **Dashboard**: single-column layout (vs. multi-column on desktop)
- **Historial**: stacked groups/timeline (vs. side-by-side on desktop)
- **Tour**: skips sidebar and Excel import steps

### Loading Overlay

A MutationObserver watches for Streamlit's `[data-testid="stStatusWidget"]` element (visible during reruns) and shows/hides a fullscreen overlay with a bouncing rocket emoji and "Cargando..." text.

### Custom Click Delegation

Since Streamlit doesn't support click handlers on custom HTML, a global event listener on `document.body` handles clicks on:

- Dashboard cards (`.pgm-card-wrap`) → triggers hidden Streamlit buttons
- Activity action buttons (`.act-btn-*`) → triggers corresponding Streamlit buttons
- Meta-bar buttons (`.meta-btn-*`) → triggers hidden Streamlit buttons

This enables a native-app feel with custom-styled UI elements backed by Streamlit's state management.
