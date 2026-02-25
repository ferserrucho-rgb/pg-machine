-- Add photos column to activities (stores array of {url, name, uploaded_at})
ALTER TABLE activities ADD COLUMN IF NOT EXISTS photos JSONB DEFAULT '[]';

-- NOTE: The storage bucket 'activity-photos' must be created in Supabase Dashboard > Storage (set to public).
-- A RLS policy on the bucket should allow authenticated users to upload/delete.
-- INSERT INTO storage.buckets (id, name, public) VALUES ('activity-photos', 'activity-photos', true);
