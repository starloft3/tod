-- Migration: Add vassal_of column to savediplomacy table
-- Date: 2026-01-13
-- Purpose: Support Troll Diplomacy and multi-faction control (Vassal/Sovereign system)

-- Add vassal_of column to savediplomacy table
-- Values: -1 = independent (not a vassal), 0+ = faction ID of sovereign
ALTER TABLE savediplomacy 
ADD COLUMN vassal_of INT DEFAULT -1;

-- Also add to diplomacydata (working state table) if it exists
ALTER TABLE diplomacydata 
ADD COLUMN vassal_of INT DEFAULT -1;

-- Verify the changes
-- SELECT * FROM savediplomacy LIMIT 5;
-- DESCRIBE savediplomacy;

