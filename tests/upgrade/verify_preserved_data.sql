DO $$
BEGIN
    IF (SELECT count(*) FROM "user" WHERE id = 1 AND username = 'upgrade-admin'
        AND password_hash = 'preserved-password-hash' AND role = 'admin') <> 1 THEN
        RAISE EXCEPTION 'user data was not preserved';
    END IF;

    IF (SELECT count(*) FROM app_settings WHERE id = 1
        AND base_url = 'http://brewweb.example.test'
        AND unit_preference = 'metric') <> 1 THEN
        RAISE EXCEPTION 'application settings were not preserved';
    END IF;

    IF (SELECT count(*) FROM yeast WHERE id = 1 AND name = 'Upgrade Test Yeast'
        AND notes = 'Preserve this custom yeast') <> 1 THEN
        RAISE EXCEPTION 'custom yeast data was not preserved';
    END IF;

    IF (SELECT count(*) FROM recipe WHERE id = 1 AND name = 'Upgrade Test Recipe'
        AND content = 'Preserved recipe content') <> 1 THEN
        RAISE EXCEPTION 'recipe data was not preserved';
    END IF;

    IF (SELECT count(*) FROM batch WHERE id = 1 AND recipe_id = 1
        AND name = 'Upgrade Test Batch' AND batch_size = 5.0
        AND initial_gravity = 1.100 AND notes = 'Preserved batch notes') <> 1 THEN
        RAISE EXCEPTION 'batch data or its recipe relationship was not preserved';
    END IF;

    IF (SELECT count(*) FROM ingredient WHERE id = 1 AND recipe_id = 1
        AND name = 'Honey' AND amount_per_gallon = 378.541) <> 1 THEN
        RAISE EXCEPTION 'ingredient data or its recipe relationship was not preserved';
    END IF;

    IF (SELECT count(*) FROM measurement WHERE id = 1 AND batch_id = 1
        AND gravity = 1.075 AND temperature = 68.0
        AND notes = 'Preserved measurement') <> 1 THEN
        RAISE EXCEPTION 'measurement data or its batch relationship was not preserved';
    END IF;

    IF (SELECT count(*) FROM calendar_event WHERE id = 1 AND batch_id = 1
        AND created_by = 1 AND title = 'Upgrade Test Event'
        AND description = 'Preserved calendar description') <> 1 THEN
        RAISE EXCEPTION 'calendar data or its relationships were not preserved';
    END IF;

    IF (SELECT count(*) FROM alembic_version
        WHERE version_num = 'eaf3a864a154') <> 1 THEN
        RAISE EXCEPTION 'database was not stamped at the expected migration revision';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'batch' AND column_name = 'tosna_enabled'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'calendar_event' AND column_name = 'note'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'user' AND column_name = 'theme'
    ) THEN
        RAISE EXCEPTION 'legacy compatibility columns were not applied';
    END IF;
END $$;
