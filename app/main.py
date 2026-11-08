"""Application factory.  Run with:  uvicorn app.main:app --reload"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import __version__
from .config import Settings
from .errors import DuplicateError, NotFoundError
from .routers import auth, background, basics, items, streaming, uploads
from .schemas import ItemCreate
from .store import ItemStore, UserStore


def seed(app: FastAPI) -> None:
    """Demo data.  The passwords below are for local experiments only."""
    app.state.users.create("alice", "alice-password", "user")
    app.state.users.create("admin", "admin-password", "admin")
    for name, price, tags in [("Widget", 9.99, ["tools"]), ("Gadget", 24.5, ["tools", "tech"]),
                              ("Gizmo", 3.25, ["tech"])]:
        app.state.items.create(ItemCreate(name=name, price=price, tags=tags))


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.events.append("startup")     # open connections, load models, ...
        yield
        app.state.events.append("shutdown")    # ... and release them

    app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan,
                  description="Examples of FastAPI server features.")
    app.state.settings = settings
    app.state.items = ItemStore()
    app.state.users = UserStore(settings.hash_iterations)
    app.state.audit_log = []
    app.state.events = []
    if settings.seed_demo_data:
        seed(app)

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"
        return response

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(DuplicateError)
    async def duplicate_handler(request: Request, exc: DuplicateError):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.get("/", tags=["meta"])
    def root():
        return {"name": settings.app_name, "version": __version__, "docs": "/docs"}

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok", "version": __version__}

    for module in (basics, items, auth, background, streaming, uploads):
        app.include_router(module.router)
    return app


app = create_app()
