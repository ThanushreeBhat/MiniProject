from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import (
    dashboard,
    risk,
    tasks,
    schedule,
    explanations,
    validation,
)

app = FastAPI(
    title="RailBlock API",
    description="Neuro-Symbolic AI for Railway Maintenance Scheduling & Risk Prediction",
    version="1.0.0",
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes with /api prefix matching Swagger & requirements
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(risk.router, prefix="/api", tags=["Risk Prediction"])
app.include_router(tasks.router, prefix="/api", tags=["Maintenance Tasks"])
app.include_router(schedule.router, prefix="/api", tags=["Optimization & Schedule"])
app.include_router(explanations.router, prefix="/api", tags=["Explainability"])
app.include_router(validation.router, prefix="/api", tags=["Safety Validation"])


@app.get("/")
def root():
    return {
        "service": "RailBlock Neuro-Symbolic AI API",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": [
            "/api/dashboard",
            "/api/risks",
            "/api/risks/{asset_id}",
            "/api/tasks",
            "/api/tasks/{task_id}",
            "/api/schedule",
            "/api/unscheduled",
            "/api/explanations",
            "/api/explanations/{task_id}",
            "/api/validation",
        ],
    }


@app.get("/api/health")
def health():
    return {"status": "healthy"}
