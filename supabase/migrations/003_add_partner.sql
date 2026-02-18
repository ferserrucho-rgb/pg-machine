-- Add partner column to opportunities
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS partner TEXT DEFAULT '';
