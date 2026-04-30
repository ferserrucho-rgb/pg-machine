-- 009_kill_reason_merged.sql
-- Allow 'merged' as a kill_reason for lead-to-opportunity conversions

ALTER TABLE opportunities
  DROP CONSTRAINT IF EXISTS opportunities_kill_reason_check;

ALTER TABLE opportunities
  ADD CONSTRAINT opportunities_kill_reason_check
    CHECK (kill_reason IN ('ganada', 'perdida', 'error', 'done', 'not_priority', 'merged'));
