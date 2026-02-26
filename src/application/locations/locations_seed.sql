-- =====================================
-- Seed data for countries and cities
-- =====================================

BEGIN;

-- -----------------
-- COUNTRIES
-- -----------------
INSERT INTO countries (id, name, created_at, updated_at) VALUES
(1, 'Kazakhstan', NOW(), NOW()),
(2, 'United States', NOW(), NOW()),
(3, 'Germany', NOW(), NOW()),
(4, 'United Kingdom', NOW(), NOW()),
(5, 'Canada', NOW(), NOW());

-- -----------------
-- CITIES
-- -----------------
INSERT INTO cities (id, name, country_id, created_at, updated_at) VALUES

-- Kazakhstan
(1, 'Almaty', 1, NOW(), NOW()),
(2, 'Astana', 1, NOW(), NOW()),
(3, 'Shymkent', 1, NOW(), NOW()),

-- United States
(4, 'New York', 2, NOW(), NOW()),
(5, 'San Francisco', 2, NOW(), NOW()),
(6, 'Austin', 2, NOW(), NOW()),

-- Germany
(7, 'Berlin', 3, NOW(), NOW()),
(8, 'Munich', 3, NOW(), NOW()),
(9, 'Hamburg', 3, NOW(), NOW()),

-- United Kingdom
(10, 'London', 4, NOW(), NOW()),
(11, 'Manchester', 4, NOW(), NOW()),
(12, 'Birmingham', 4, NOW(), NOW()),

-- Canada
(13, 'Toronto', 5, NOW(), NOW()),
(14, 'Vancouver', 5, NOW(), NOW()),
(15, 'Montreal', 5, NOW(), NOW());

-- -----------------
-- Fix sequences (important if id is SERIAL)
-- -----------------
SELECT setval('countries_id_seq', (SELECT MAX(id) FROM countries));
SELECT setval('cities_id_seq', (SELECT MAX(id) FROM cities));

COMMIT;