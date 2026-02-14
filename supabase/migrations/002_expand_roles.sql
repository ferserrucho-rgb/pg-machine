-- Migration: Expand role system from 3 to 8 roles
-- Run this in Supabase SQL Editor after 001_initial.sql

-- 1. Drop old CHECK constraint
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_role_check;

-- 2. Migrate existing 'manager' rows to 'account_manager'
UPDATE profiles SET role = 'account_manager' WHERE role = 'manager';

-- 3. Add new CHECK constraint with 8 roles
ALTER TABLE profiles ADD CONSTRAINT profiles_role_check
    CHECK (role IN (
        'admin',
        'vp',
        'account_manager',
        'regional_sales_manager',
        'partner_manager',
        'regional_partner_manager',
        'presales_manager',
        'presales'
    ));
