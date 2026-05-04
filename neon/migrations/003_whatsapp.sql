-- Migration 003: WhatsApp notifications via CallMeBot
-- Run this in the Neon SQL console

ALTER TABLE notifications ADD COLUMN whatsapp_sent BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE notifications ADD COLUMN whatsapp_sent_at TIMESTAMPTZ;
ALTER TABLE profiles ADD COLUMN whatsapp_apikey TEXT DEFAULT '';
