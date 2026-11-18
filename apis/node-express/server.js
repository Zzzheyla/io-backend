const express = require('express');
const { Pool } = require('pg');

const PORT = process.env.PORT || 3000;
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://io:io@localhost:5432/io',
  max: 10,
});

const app = express();
app.use(express.json());

function countPrimes(n) {
  let count = 0;
  for (let i = 2; i <= n; i++) {
    let isPrime = true;
    for (let d = 2; d * d <= i; d++) {
      if (i % d === 0) {
        isPrime = false;
        break;
      }
    }
    if (isPrime) count++;
  }
  return count;
}

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/items', async (req, res, next) => {
  try {
    const limit = Number(req.query.limit ?? 100);
    if (!Number.isInteger(limit) || limit < 1 || limit > 1000) {
      return res.status(422).json({ error: 'limit debe estar entre 1 y 1000' });
    }
    const { rows } = await pool.query(
      'SELECT id, name, price, created_at FROM items ORDER BY id DESC LIMIT $1',
      [limit]
    );
    res.json(rows);
  } catch (err) {
    next(err);
  }
});

app.post('/items', async (req, res, next) => {
  try {
    const { name, price } = req.body ?? {};
    if (typeof name !== 'string' || name.length < 1 || name.length > 100 ||
        typeof price !== 'number' || price < 0) {
      return res.status(422).json({ error: 'datos invalidos' });
    }
    const { rows } = await pool.query(
      'INSERT INTO items (name, price) VALUES ($1, $2) RETURNING id, name, price, created_at',
      [name, price]
    );
    res.status(201).json(rows[0]);
  } catch (err) {
    next(err);
  }
});

app.get('/primes', (req, res) => {
  const n = Number(req.query.n ?? 20000);
  if (!Number.isInteger(n) || n < 2 || n > 200000) {
    return res.status(422).json({ error: 'n debe estar entre 2 y 200000' });
  }
  res.json({ n, count: countPrimes(n) });
});

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: 'error interno' });
});

app.listen(PORT, () => console.log(`API Node escuchando en el puerto ${PORT}`));
