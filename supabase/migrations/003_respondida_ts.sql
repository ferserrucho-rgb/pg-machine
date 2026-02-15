-- Migration: Add respondida_ts to track when customer responded
-- Run this in Supabase SQL Editor after 002_expand_roles.sql

ALTER TABLE activities ADD COLUMN IF NOT EXISTS respondida_ts DATE;
