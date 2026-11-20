
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import (
    dashboard,
    risk,
    schedule,
    tasks,
    explanations,
    validation,
)


app = FastAPI(
    title="RailBlock API",
    description=(
        "ML-based asset risk prediction and "
        "railway maintenance block optimization."
    ),
    version="1.0.0",
)


# Allow frontend development servers to access the API.
# Restrict this to your frontend origin before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routes
app.include_router(
    dashboard.router,
    prefix="/api",
    tags=["Dashboard"],
)

app.include_router(
    risk.router,
    prefix="/api",
    tags=["Risk Prediction"],
)

app.include_router(
    schedule.router,
    prefix="/api",
    tags=["Scheduling"],
)

app.include_router(
    tasks.router,
    prefix="/api",
    tags=["Maintenance Tasks"],
)

app.include_router(
    explanations.router,
    prefix="/api",
    tags=["Explainability"],
)

app.include_router(
    validation.router,
    prefix="/api",
    tags=["Validation"],
)


@app.get("/")
def home():

    return {
        "project": "RailBlock",
        "message": "RailBlock API is running.",
        "version": "1.0.0",
        "documentation": "/docs",
    }


@app.get("/api/health")
def health():

    return {
        "status": "healthy",
        "service": "RailBlock Backend",
    }
