from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.core.config import settings
from src.api.routes import router

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.include_router(router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
