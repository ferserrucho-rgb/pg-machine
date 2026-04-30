-- ============================================================
-- PG Machine — Neon PostgreSQL Schema (consolidated)
-- No RLS, no auth.users dependency, local bcrypt auth
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- TABLES
-- ============================================================

-- Teams: organizational units for data isolation
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Profiles: standalone (no auth.users dependency)
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'presales'
        CHECK (role IN (
            'admin', 'vp', 'account_manager', 'regional_sales_manager',
            'partner_manager', 'regional_partner_manager', 'presales_manager', 'presales'
        )),
    phone TEXT DEFAULT '',
    specialty TEXT DEFAULT '',
    lang TEXT DEFAULT 'es',
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profiles_team ON profiles(team_id);
CREATE UNIQUE INDEX idx_profiles_email ON profiles(email);

-- Opportunities
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
    partner TEXT DEFAULT '',
    urgency TEXT DEFAULT NULL CHECK (urgency IN ('alta', 'media', 'baja')),
    gtm_type TEXT DEFAULT NULL,
    killed_at TIMESTAMPTZ DEFAULT NULL,
    kill_reason TEXT DEFAULT NULL
        CHECK (kill_reason IN ('ganada', 'perdida', 'error', 'done', 'not_priority', 'merged')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_opportunities_team ON opportunities(team_id);
CREATE INDEX idx_opportunities_owner ON opportunities(owner_id);
CREATE INDEX idx_opportunities_categoria ON opportunities(team_id, categoria);
CREATE INDEX idx_opportunities_active ON opportunities(team_id, monto DESC) WHERE killed_at IS NULL;
CREATE INDEX idx_opportunities_killed ON opportunities(team_id, killed_at DESC) WHERE killed_at IS NOT NULL;

-- Activities
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
    respondida_ts DATE,
    feedback TEXT DEFAULT '',
    response_token TEXT,
    token_expires_at TIMESTAMPTZ,
    meeting_metadata JSONB DEFAULT NULL,
    photos JSONB DEFAULT '[]'
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

-- Team configuration
CREATE TABLE team_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value JSONB NOT NULL DEFAULT '{}',
    UNIQUE(team_id, key)
);

CREATE INDEX idx_team_config_team_key ON team_config(team_id, key);

-- Calendar inbox
CREATE TABLE calendar_inbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    user_email TEXT NOT NULL,
    subject TEXT NOT NULL DEFAULT '',
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    organizer TEXT DEFAULT '',
    attendees JSONB DEFAULT '[]'::jsonb,
    location TEXT DEFAULT '',
    body TEXT DEFAULT '',
    outlook_event_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'dismissed')),
    assigned_opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    assigned_activity_id UUID REFERENCES activities(id) ON DELETE SET NULL,
    assigned_at TIMESTAMPTZ,
    assigned_by UUID REFERENCES profiles(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_calendar_inbox_team ON calendar_inbox(team_id);
CREATE INDEX idx_calendar_inbox_profile ON calendar_inbox(profile_id);
CREATE INDEX idx_calendar_inbox_pending ON calendar_inbox(team_id, status) WHERE status = 'pending';
CREATE INDEX idx_calendar_inbox_outlook_event ON calendar_inbox(outlook_event_id) WHERE outlook_event_id IS NOT NULL;

-- Pipeline snapshots
CREATE TABLE pipeline_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    week_ending DATE NOT NULL,
    snapshot_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (team_id, week_ending)
);

CREATE INDEX idx_pipeline_snapshots_team_week ON pipeline_snapshots(team_id, week_ending DESC);

-- Viajes (trips)
CREATE TABLE viajes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    destino TEXT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado TEXT NOT NULL DEFAULT 'planeado' CHECK (estado IN ('planeado', 'en_curso', 'completado', 'cancelado')),
    notas TEXT DEFAULT '',
    visitas JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_viajes_team ON viajes(team_id);
CREATE INDEX idx_viajes_created_by ON viajes(created_by);
CREATE INDEX idx_viajes_estado ON viajes(team_id, estado);
CREATE INDEX idx_viajes_fechas ON viajes(fecha_inicio, fecha_fin);

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Auto-update updated_at on opportunities
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

-- Seed default team config on team creation
CREATE OR REPLACE FUNCTION seed_team_config()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO team_config (team_id, key, value) VALUES
        (NEW.id, 'sla_opciones', '{
            "\ud83d\udea8 Urgente (2-4h)": {"horas": 4, "color": "#ef4444"},
            "\u26a0\ufe0f Importante (2d)": {"dias": 2, "color": "#f59e0b"},
            "\u2615 No urgente (7d)": {"dias": 7, "color": "#3b82f6"}
        }'::jsonb),
        (NEW.id, 'categorias', '["LEADS", "OFFICIAL", "GTM"]'::jsonb),
        (NEW.id, 'sla_respuesta', '{
            "3 d\u00edas": 3,
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
