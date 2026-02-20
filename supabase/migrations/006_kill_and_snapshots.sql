-- 006_kill_and_snapshots.sql
-- Kill (cerrar) oportunidades y GTM + pipeline snapshots semanales
-- Oportunidades (LEADS/OFFICIAL): ganada, perdida, error
-- GTM: done, not_priority, error

-- 1. Kill columns on opportunities
ALTER TABLE opportunities
  ADD COLUMN IF NOT EXISTS killed_at TIMESTAMPTZ DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS kill_reason TEXT DEFAULT NULL
    CHECK (kill_reason IN ('ganada', 'perdida', 'error', 'done', 'not_priority'));

-- 2. GTM-specific columns (urgency + type for GTM items)
ALTER TABLE opportunities
  ADD COLUMN IF NOT EXISTS urgency TEXT DEFAULT NULL
    CHECK (urgency IN ('alta', 'media', 'baja')),
  ADD COLUMN IF NOT EXISTS gtm_type TEXT DEFAULT NULL;

-- Partial indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_opportunities_active
  ON opportunities (team_id, monto DESC)
  WHERE killed_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_opportunities_killed
  ON opportunities (team_id, killed_at DESC)
  WHERE killed_at IS NOT NULL;

-- 3. Pipeline snapshots table
CREATE TABLE IF NOT EXISTS pipeline_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  week_ending DATE NOT NULL,
  snapshot_data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (team_id, week_ending)
);

-- RLS on pipeline_snapshots
ALTER TABLE pipeline_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "pipeline_snapshots_team_isolation"
  ON pipeline_snapshots
  FOR ALL
  USING (team_id = get_my_team_id())
  WITH CHECK (team_id = get_my_team_id());

-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_pipeline_snapshots_team_week
  ON pipeline_snapshots (team_id, week_ending DESC);
