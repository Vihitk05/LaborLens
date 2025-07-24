from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.analysis import router as analysis_router
from app.api.events import router as events_router
from app.api.auth import router as auth_router
from app.config import settings
from app.core.event_bus import connect_event_bus

app = FastAPI(title=settings.PROJECT_NAME)

# Initialize event bus connection
connect_event_bus(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
app.include_router(events_router, prefix="/events", tags=["events"])

@app.get("/")
def read_root():
    return {"message": "Job Market Analysis API"}