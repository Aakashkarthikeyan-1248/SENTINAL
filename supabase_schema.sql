-- SENTINAL Incidents Table for Supabase (PostgreSQL)
-- Execute this script in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    video_source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.0,
    evidence_path TEXT,
    summary TEXT,
    status TEXT NOT NULL DEFAULT 'NEW', -- NEW, ACKNOWLEDGED, DISMISSED, ESCALATED
    reviewer_notes TEXT DEFAULT '',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;

-- Allow public read/write for hackathon demo (tune for production)
CREATE POLICY "Public full access for hackathon" ON incidents
    FOR ALL
    USING (true)
    WITH CHECK (true);
