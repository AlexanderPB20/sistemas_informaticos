-- 1. Análisis sin índices específicos (Seq Scan)
EXPLAIN ANALYZE
SELECT p."purchaseID", p."purchaseDate", p."total", u."username", c."name" AS "country"
FROM "purchase" p
JOIN "user" u ON u."UUID" = p."UUID"
JOIN "country" c ON c."countryID" = u."countryID"
WHERE EXTRACT(YEAR FROM p."purchaseDate") = 2026
  AND c."name" ILIKE 'Spain';

-- 2. Creación de índices para optimizar la consulta
CREATE INDEX IF NOT EXISTS idx_country_name ON "country" (lower("name"));
CREATE INDEX IF NOT EXISTS idx_user_countryID ON "user" ("countryID");
CREATE INDEX IF NOT EXISTS idx_purchase_year ON "purchase" (EXTRACT(YEAR FROM "purchaseDate"));

-- 3. Análisis tras aplicar los índices
EXPLAIN ANALYZE
SELECT p."purchaseID", p."purchaseDate", p."total", u."username", c."name" AS "country"
FROM "purchase" p
JOIN "user" u ON u."UUID" = p."UUID"
JOIN "country" c ON c."countryID" = u."countryID"
WHERE EXTRACT(YEAR FROM p."purchaseDate") = 2026
  AND lower(c."name") = lower('Spain');

