from fastapi import FastAPI
from
from app.core.exceptions import register_exception_handlers
from app.core.setup import lifespan
from app.routers import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Corehub",
        lifespan=lifespan,
    )

    app.include_router(api_router)
    register_exception_handlers(app)
    return app


app = create_app()
