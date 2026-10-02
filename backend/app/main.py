from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, SessionLocal, engine, get_db
from app.routers import groups
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Tests replace get_db with their own temporary database, so we leave the real one alone.
    if get_db not in app.dependency_overrides:
        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            seed_demo_data(db)
    yield


app = FastAPI(title="Gastos compartidos API", version="1.0.0", lifespan=lifespan)
app.include_router(groups.router)
