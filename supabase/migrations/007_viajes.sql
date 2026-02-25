-- ============================================================
-- PG Machine — Viajes (Trip Planning)
-- Run this in Supabase SQL Editor
-- ============================================================

-- Viajes: trip planning with embedded visit checklist
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

-- Indexes
CREATE INDEX idx_viajes_team ON viajes(team_id);
CREATE INDEX idx_viajes_created_by ON viajes(created_by);
CREATE INDEX idx_viajes_estado ON viajes(team_id, estado);
CREATE INDEX idx_viajes_fechas ON viajes(fecha_inicio, fecha_fin);

-- RLS
ALTER TABLE viajes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "viajes_select" ON viajes
    FOR SELECT USING (team_id = get_my_team_id());

CREATE POLICY "viajes_insert" ON viajes
    FOR INSERT WITH CHECK (team_id = get_my_team_id());

CREATE POLICY "viajes_update" ON viajes
    FOR UPDATE USING (team_id = get_my_team_id());

CREATE POLICY "viajes_delete" ON viajes
    FOR DELETE USING (team_id = get_my_team_id());
