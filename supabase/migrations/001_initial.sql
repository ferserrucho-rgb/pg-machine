-- ============================================================
-- PG Machine — Full Database Schema
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New query)
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- pg_cron must be enabled from the Supabase dashboard (Database → Extensions → pg_cron)

-- ============================================================
-- TABLES
-- ============================================================

-- Teams: organizational units for data isolation
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Profiles: extends Supabase auth.users
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'presales' CHECK (role IN ('admin', 'manager', 'presales')),
    phone TEXT DEFAULT '',
    specialty TEXT DEFAULT '',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_team ON profiles(team_id);
CREATE INDEX idx_profiles_email ON profiles(email);

-- Opportunities: replaces in-memory db_leads
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES profiles(id),
    proyecto TEXT NOT NULL,
    cuenta TEXT NOT NULL,
    monto NUMERIC NOT NULL DEFAULT 0,
    categoria TEXT NOT NULL CHECK (categoria IN ('LEADS', 'OFFICIAL', 'GTM')),
    opp_id TEXT DEFAULT '',
    stage TEXT DEFAULT '',
    close_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_opportunities_team ON opportunities(team_id);
CREATE INDEX idx_opportunities_owner ON opportunities(owner_id);
CREATE INDEX idx_opportunities_categoria ON opportunities(team_id, categoria);

-- Activities: replaces actividades[] nested list
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES profiles(id),
    assigned_to UUID REFERENCES profiles(id),
    tipo TEXT NOT NULL,
    fecha DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    objetivo TEXT DEFAULT '',
    descripcion TEXT DEFAULT '',
    estado TEXT NOT NULL DEFAULT 'Pendiente' CHECK (estado IN ('Pendiente', 'Enviada', 'Respondida')),
    sla_key TEXT DEFAULT '',
    sla_hours INTEGER,
    sla_deadline TIMESTAMPTZ,
    sla_respuesta_dias INTEGER DEFAULT 7,
    destinatario TEXT DEFAULT '',
    enviada_ts TIMESTAMPTZ,
    response_deadline TIMESTAMPTZ,
    feedback TEXT DEFAULT '',
    response_token TEXT,
    token_expires_at TIMESTAMPTZ
);

CREATE INDEX idx_activities_opportunity ON activities(opportunity_id);
CREATE INDEX idx_activities_team ON activities(team_id);
CREATE INDEX idx_activities_assigned ON activities(assigned_to);
CREATE INDEX idx_activities_estado ON activities(estado);
CREATE INDEX idx_activities_sla_deadline ON activities(sla_deadline) WHERE estado = 'Pendiente';
CREATE INDEX idx_activities_response_deadline ON activities(response_deadline) WHERE estado = 'Enviada';
CREATE INDEX idx_activities_token ON activities(response_token) WHERE response_token IS NOT NULL;

-- Notifications: email queue
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    activity_id UUID NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES profiles(id),
    type TEXT NOT NULL CHECK (type IN ('assignment', 'sla_warning', 'sla_expired', 'blocked')),
    sent BOOLEAN NOT NULL DEFAULT false,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_notifications_unsent ON notifications(sent) WHERE sent = false;
CREATE INDEX idx_notifications_activity ON notifications(activity_id);

-- Team configuration: configurable settings per team
CREATE TABLE team_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value JSONB NOT NULL DEFAULT '{}',
    UNIQUE(team_id, key)
);

CREATE INDEX idx_team_config_team_key ON team_config(team_id, key);

-- ============================================================
-- AUTO-UPDATE updated_at TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER opportunities_updated_at
    BEFORE UPDATE ON opportunities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- ROW-LEVEL SECURITY
-- ============================================================

ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_config ENABLE ROW LEVEL SECURITY;

-- Helper: get current user's team_id
CREATE OR REPLACE FUNCTION get_my_team_id()
RETURNS UUID AS $$
    SELECT team_id FROM profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Teams: users can only see their own team
CREATE POLICY "team_read" ON teams
    FOR SELECT USING (id = get_my_team_id());

-- Profiles: users can see all profiles in their team
CREATE POLICY "profiles_read" ON profiles
    FOR SELECT USING (team_id = get_my_team_id());

CREATE POLICY "profiles_insert" ON profiles
    FOR INSERT WITH CHECK (team_id = get_my_team_id() OR NOT EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid()));

CREATE POLICY "profiles_update" ON profiles
    FOR UPDATE USING (team_id = get_my_team_id());

-- Opportunities: team isolation
CREATE POLICY "opportunities_select" ON opportunities
    FOR SELECT USING (team_id = get_my_team_id());

CREATE POLICY "opportunities_insert" ON opportunities
    FOR INSERT WITH CHECK (team_id = get_my_team_id());

CREATE POLICY "opportunities_update" ON opportunities
    FOR UPDATE USING (team_id = get_my_team_id());

CREATE POLICY "opportunities_delete" ON opportunities
    FOR DELETE USING (team_id = get_my_team_id());

-- Activities: team isolation
CREATE POLICY "activities_select" ON activities
    FOR SELECT USING (team_id = get_my_team_id());

CREATE POLICY "activities_insert" ON activities
    FOR INSERT WITH CHECK (team_id = get_my_team_id());

CREATE POLICY "activities_update" ON activities
    FOR UPDATE USING (team_id = get_my_team_id());

CREATE POLICY "activities_delete" ON activities
    FOR DELETE USING (team_id = get_my_team_id());

-- Notifications: team isolation
CREATE POLICY "notifications_select" ON notifications
    FOR SELECT USING (team_id = get_my_team_id());

CREATE POLICY "notifications_insert" ON notifications
    FOR INSERT WITH CHECK (team_id = get_my_team_id());

CREATE POLICY "notifications_update" ON notifications
    FOR UPDATE USING (team_id = get_my_team_id());

-- Team config: team isolation
CREATE POLICY "team_config_select" ON team_config
    FOR SELECT USING (team_id = get_my_team_id());

CREATE POLICY "team_config_insert" ON team_config
    FOR INSERT WITH CHECK (team_id = get_my_team_id());

CREATE POLICY "team_config_update" ON team_config
    FOR UPDATE USING (team_id = get_my_team_id());

-- ============================================================
-- SPECIAL RLS: Allow new users to create team + profile on registration
-- These use service_role key from the backend, bypassing RLS
-- ============================================================

-- Policy to allow inserting into teams during registration (no existing profile yet)
CREATE POLICY "teams_insert_registration" ON teams
    FOR INSERT WITH CHECK (true);

-- ============================================================
-- DEFAULT TEAM CONFIG SEED (inserted per-team on creation)
-- ============================================================

CREATE OR REPLACE FUNCTION seed_team_config()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO team_config (team_id, key, value) VALUES
        (NEW.id, 'sla_opciones', '{
            "🚨 Urgente (2-4h)": {"horas": 4, "color": "#ef4444"},
            "⚠️ Importante (2d)": {"dias": 2, "color": "#f59e0b"},
            "☕ No urgente (7d)": {"dias": 7, "color": "#3b82f6"}
        }'::jsonb),
        (NEW.id, 'categorias', '["LEADS", "OFFICIAL", "GTM"]'::jsonb),
        (NEW.id, 'sla_respuesta', '{
            "3 días": 3,
            "1 semana": 7,
            "2 semanas": 14,
            "1 mes": 30
        }'::jsonb);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER team_created_seed_config
    AFTER INSERT ON teams
    FOR EACH ROW EXECUTE FUNCTION seed_team_config();

-- ============================================================
-- pg_cron: SLA MONITORING (runs every 15 minutes)
-- NOTE: Enable pg_cron extension from Supabase Dashboard first
-- Then run these separately after enabling the extension
-- ============================================================

-- Uncomment after enabling pg_cron from Supabase Dashboard:

-- SELECT cron.schedule('check-sla-expired', '*/15 * * * *', $$
--   INSERT INTO notifications (team_id, activity_id, recipient_id, type)
--   SELECT a.team_id, a.id, COALESCE(a.assigned_to, a.created_by), 'sla_expired'
--   FROM activities a
--   WHERE a.estado = 'Pendiente'
--     AND a.sla_deadline IS NOT NULL
--     AND a.sla_deadline < now()
--     AND NOT EXISTS (
--       SELECT 1 FROM notifications n
--       WHERE n.activity_id = a.id AND n.type = 'sla_expired'
--     );
-- $$);

-- SELECT cron.schedule('check-blocked', '*/15 * * * *', $$
--   INSERT INTO notifications (team_id, activity_id, recipient_id, type)
--   SELECT a.team_id, a.id, a.created_by, 'blocked'
--   FROM activities a
--   WHERE a.estado = 'Enviada'
--     AND a.response_deadline IS NOT NULL
--     AND a.response_deadline < now()
--     AND NOT EXISTS (
--       SELECT 1 FROM notifications n
--       WHERE n.activity_id = a.id AND n.type = 'blocked'
--     );
-- $$);

-- SELECT cron.schedule('check-sla-warning', '*/15 * * * *', $$
--   INSERT INTO notifications (team_id, activity_id, recipient_id, type)
--   SELECT a.team_id, a.id, COALESCE(a.assigned_to, a.created_by), 'sla_warning'
--   FROM activities a
--   WHERE a.estado = 'Pendiente'
--     AND a.sla_deadline IS NOT NULL
--     AND a.sla_deadline > now()
--     AND (a.sla_deadline - now()) < (a.sla_deadline - a.created_at) * 0.5
--     AND NOT EXISTS (
--       SELECT 1 FROM notifications n
--       WHERE n.activity_id = a.id AND n.type = 'sla_warning'
--     );
-- $$);
