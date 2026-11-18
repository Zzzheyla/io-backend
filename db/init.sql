-- Base de datos compartida por las tres APIs.
-- Se ejecuta automaticamente la primera vez que arranca el contenedor de PostgreSQL.

CREATE TABLE IF NOT EXISTS items (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100)     NOT NULL,
    price       DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

-- 1000 registros de prueba, identicos en cada ejecucion
INSERT INTO items (name, price)
SELECT 'producto-' || g, ROUND((g * 7 % 1000)::numeric / 10, 2)
FROM generate_series(1, 1000) AS g;
