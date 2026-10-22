-- Análisis sin índices
EXPLAIN
SELECT "purchase"."purchaseID", "purchase"."purchaseDate", "purchase"."total", "user"."username", "country"."name" AS "country"
FROM "purchase"
JOIN "user" ON "user"."UUID" = "purchase"."UUID"
JOIN "country" ON "country"."countryID" = "user"."countryID"
WHERE EXTRACT(YEAR FROM "purchase"."purchaseDate") = 2026
  AND "country"."name" ILIKE 'Spain';

-- Indexado de la conslta
CREATE INDEX IF NOT EXISTS idx_country_name ON "country" (lower("name"));
CREATE INDEX IF NOT EXISTS idx_user_countryID ON "user" ("countryID");
CREATE INDEX IF NOT EXISTS idx_purchase_year ON "purchase" (EXTRACT(YEAR FROM "purchaseDate"));

-- Búsqueda indexada
EXPLAIN
SELECT "purchase"."purchaseID", "purchase"."purchaseDate", "purchase"."total", "user"."username", "country"."name" AS "country"
FROM "purchase"
JOIN "user" ON "user"."UUID" = "purchase"."UUID"
JOIN "country" ON "country"."countryID" = "user"."countryID"
WHERE EXTRACT(YEAR FROM "purchase"."purchaseDate") = 2026
  AND lower("country"."name") = lower('Spain');