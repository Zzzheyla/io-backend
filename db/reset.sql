-- Deja la tabla exactamente igual antes de cada prueba de carga,
-- para que las tres APIs se midan con los mismos datos.

TRUNCATE items RESTART IDENTITY;

INSERT INTO items (name, price)
SELECT 'producto-' || g, ROUND((g * 7 % 1000)::numeric / 10, 2)
FROM generate_series(1, 1000) AS g;

VACUUM ANALYZE items;
