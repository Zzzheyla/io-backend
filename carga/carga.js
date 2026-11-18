// Prueba de carga con k6. La misma para las tres APIs.
// Mezcla fija por cada 10 iteraciones: 7 lecturas, 2 escrituras y 1 calculo pesado.

import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE_URL;
const PRIMES_N = __ENV.PRIMES_N || '20000';

export const options = {
  vus: Number(__ENV.VUS || 50),
  duration: __ENV.DURATION || '60s',
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)'],
};

export default function () {
  const paso = __ITER % 10;

  if (paso < 7) {
    const res = http.get(`${BASE}/items?limit=100`, { tags: { endpoint: 'lectura' } });
    check(res, { 'lectura 200': (r) => r.status === 200 });
  } else if (paso < 9) {
    const body = JSON.stringify({ name: `item-${__VU}-${__ITER}`, price: (__ITER % 1000) / 10 });
    const res = http.post(`${BASE}/items`, body, {
      headers: { 'Content-Type': 'application/json' },
      tags: { endpoint: 'escritura' },
    });
    check(res, { 'escritura 201': (r) => r.status === 201 });
  } else {
    const res = http.get(`${BASE}/primes?n=${PRIMES_N}`, { tags: { endpoint: 'calculo' } });
    check(res, { 'calculo 200': (r) => r.status === 200 });
  }
}
