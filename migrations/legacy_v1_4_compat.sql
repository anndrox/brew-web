-- One-time compatibility repair for databases created before committed
-- Alembic migrations were introduced. The entry point runs this only when it
-- detects application tables without an alembic_version table.

CREATE TABLE IF NOT EXISTS yeast (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    alcohol_type VARCHAR(20) NOT NULL,
    tolerance VARCHAR(50),
    strength VARCHAR(50),
    sweetness_retention VARCHAR(50),
    notes TEXT,
    flocculation VARCHAR(50),
    attenuation VARCHAR(10),
    is_default BOOLEAN DEFAULT FALSE
);

ALTER TABLE IF EXISTS recipe ADD COLUMN IF NOT EXISTS yeast_id INTEGER;
ALTER TABLE IF EXISTS batch ADD COLUMN IF NOT EXISTS yeast_id INTEGER;
ALTER TABLE IF EXISTS batch ADD COLUMN IF NOT EXISTS tosna_total FLOAT;
ALTER TABLE IF EXISTS batch ADD COLUMN IF NOT EXISTS tosna_per_day FLOAT;
ALTER TABLE IF EXISTS batch ADD COLUMN IF NOT EXISTS tosna_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE IF EXISTS "user" ADD COLUMN IF NOT EXISTS theme VARCHAR(20) DEFAULT 'dark';
ALTER TABLE IF EXISTS "user" ADD COLUMN IF NOT EXISTS font_size VARCHAR(10) DEFAULT '16px';
ALTER TABLE IF EXISTS calendar_event ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE IF EXISTS app_settings ADD COLUMN IF NOT EXISTS unit_preference VARCHAR(10) DEFAULT 'imperial';

DO $$ BEGIN
    IF to_regclass('public.recipe') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'recipe_yeast_id_fkey') THEN
        ALTER TABLE recipe ADD CONSTRAINT recipe_yeast_id_fkey
            FOREIGN KEY (yeast_id) REFERENCES yeast(id);
    END IF;

    IF to_regclass('public.batch') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'batch_yeast_id_fkey') THEN
        ALTER TABLE batch ADD CONSTRAINT batch_yeast_id_fkey
            FOREIGN KEY (yeast_id) REFERENCES yeast(id);
    END IF;
END $$;
