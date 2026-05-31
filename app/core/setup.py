from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import select


from app.core.security import hash_password
from app.models.users import User
from app import models  # loads models in memory, don't delete
from app.core.database import AsyncSessionLocal, Base, engine
from app.schemas.enum import Role


async def create_default_admin():
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.role == Role.ADMIN)
        result = await session.execute(stmt)
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("Admin already exists, skipping...")
            return

        admin = User(
            first_name="admin",
            last_name="admin",
            username="adminadmin",
            email="admin@email.com",
            hashed_password=hash_password("adminadmin"),
            role=Role.ADMIN,
        )

        session.add(admin)
        await session.commit()
        print("Default admin created!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await create_default_admin()

    yield

    await engine.dispose()
