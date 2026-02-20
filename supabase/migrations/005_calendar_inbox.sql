-- ============================================================
-- PG Machine — Calendar Inbox (Power Automate sync)
-- Run this in Supabase SQL Editor
-- ============================================================

-- Calendar inbox: queue for incoming Outlook calendar events
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

-- Indexes
CREATE INDEX idx_calendar_inbox_team ON calendar_inbox(team_id);
CREATE INDEX idx_calendar_inbox_profile ON calendar_inbox(profile_id);
CREATE INDEX idx_calendar_inbox_pending ON calendar_inbox(team_id, status) WHERE status = 'pending';
CREATE INDEX idx_calendar_inbox_outlook_event ON calendar_inbox(outlook_event_id) WHERE outlook_event_id IS NOT NULL;

-- RLS
ALTER TABLE calendar_inbox ENABLE ROW LEVEL SECURITY;

CREATE POLICY "calendar_inbox_select" ON calendar_inbox
    FOR SELECT USING (team_id = get_my_team_id());

CREATE POLICY "calendar_inbox_insert" ON calendar_inbox
    FOR INSERT WITH CHECK (team_id = get_my_team_id());

CREATE POLICY "calendar_inbox_update" ON calendar_inbox
    FOR UPDATE USING (team_id = get_my_team_id());

CREATE POLICY "calendar_inbox_delete" ON calendar_inbox
    FOR DELETE USING (team_id = get_my_team_id());
