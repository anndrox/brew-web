CREATE TABLE app_settings (
    id SERIAL PRIMARY KEY,
    base_url VARCHAR(255),
    unit_preference VARCHAR(10) DEFAULT 'imperial'
);

CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user'
);

CREATE TABLE yeast (
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

CREATE TABLE recipe (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    alcohol_type VARCHAR(20),
    content TEXT,
    created_date TIMESTAMP,
    instructions TEXT,
    notes TEXT,
    water_type VARCHAR(50)
);

CREATE TABLE batch (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipe(id),
    name VARCHAR(100) NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    batch_size FLOAT,
    fermentation_temp VARCHAR(50),
    initial_gravity FLOAT,
    final_gravity FLOAT,
    abv FLOAT,
    yeast_type VARCHAR(100),
    backsweetened BOOLEAN,
    flavor_additions TEXT,
    pectic_used BOOLEAN,
    notes TEXT,
    water_type VARCHAR(50),
    alcohol_type VARCHAR(20)
);

CREATE TABLE ingredient (
    id SERIAL PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipe(id),
    name VARCHAR(100) NOT NULL,
    amount_per_gallon FLOAT NOT NULL,
    unit VARCHAR(20) NOT NULL,
    note VARCHAR(200)
);

CREATE TABLE measurement (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batch(id),
    date TIMESTAMP,
    gravity FLOAT,
    ph FLOAT,
    temperature FLOAT,
    notes TEXT
);

CREATE TABLE calendar_event (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES batch(id),
    title VARCHAR(100) NOT NULL,
    start DATE NOT NULL,
    "end" DATE,
    description TEXT,
    all_day BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES "user"(id)
);

INSERT INTO app_settings (id, base_url, unit_preference)
VALUES (1, 'http://brewweb.example.test', 'metric');

INSERT INTO "user" (id, username, password_hash, is_admin, role)
VALUES (1, 'upgrade-admin', 'preserved-password-hash', TRUE, 'admin');

INSERT INTO yeast (
    id, name, alcohol_type, tolerance, strength, sweetness_retention,
    notes, flocculation, attenuation, is_default
)
VALUES (
    1, 'Upgrade Test Yeast', 'Mead', '18%', 'Strong', 'Medium',
    'Preserve this custom yeast', 'High', '80%', FALSE
);

INSERT INTO recipe (
    id, name, alcohol_type, content, created_date, instructions, notes, water_type
)
VALUES (
    1, 'Upgrade Test Recipe', 'Mead', 'Preserved recipe content',
    '2026-01-02 03:04:05', 'Preserved instructions', 'Preserved recipe notes',
    'Spring Water'
);

INSERT INTO batch (
    id, recipe_id, name, start_date, end_date, batch_size,
    fermentation_temp, initial_gravity, final_gravity, abv, yeast_type,
    backsweetened, flavor_additions, pectic_used, notes, water_type, alcohol_type
)
VALUES (
    1, 1, 'Upgrade Test Batch', '2026-01-03 00:00:00', NULL, 5.0,
    '68', 1.100, 1.010, 11.81, 'Upgrade Test Yeast', TRUE,
    'Orange peel', TRUE, 'Preserved batch notes', 'Spring Water', 'Mead'
);

INSERT INTO ingredient (id, recipe_id, name, amount_per_gallon, unit, note)
VALUES (1, 1, 'Honey', 378.541, 'g', 'Preserved ingredient note');

INSERT INTO measurement (id, batch_id, date, gravity, ph, temperature, notes)
VALUES (1, 1, '2026-01-04 00:00:00', 1.075, 3.5, 68.0, 'Preserved measurement');

INSERT INTO calendar_event (
    id, batch_id, title, start, "end", description, all_day, created_by
)
VALUES (
    1, 1, 'Upgrade Test Event', '2026-01-05', NULL,
    'Preserved calendar description', TRUE, 1
);
