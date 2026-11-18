import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://io:io@localhost:5432/io")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    yield
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(ge=0)


def to_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "price": row["price"],
        "created_at": row["created_at"].isoformat(),
    }


def count_primes(n: int) -> int:
    count = 0
    for i in range(2, n + 1):
        is_prime = True
        d = 2
        while d * d <= i:
            if i % d == 0:
                is_prime = False
                break
            d += 1
        if is_prime:
            count += 1
    return count


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/items")
async def list_items(limit: int = Query(100, ge=1, le=1000)):
    rows = await app.state.pool.fetch(
        "SELECT id, name, price, created_at FROM items ORDER BY id DESC LIMIT $1", limit
    )
    return [to_dict(r) for r in rows]


@app.post("/items", status_code=201)
async def create_item(item: ItemIn):
    row = await app.state.pool.fetchrow(
        "INSERT INTO items (name, price) VALUES ($1, $2) "
        "RETURNING id, name, price, created_at",
        item.name,
        item.price,
    )
    return to_dict(row)


@app.get("/primes")
def primes(n: int = Query(20000, ge=2, le=200000)):
    return {"n": n, "count": count_primes(n)}
