from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.core.config import settings
from src.api.routes import router
from src.agent.session import session_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    session_store.start_cleanup()
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

app.include_router(router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
