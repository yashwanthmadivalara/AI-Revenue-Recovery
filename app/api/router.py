from fastapi import APIRouter
from app.api.webhooks import router as webhooks_router
from app.api.recovery import router as recovery_router
from app.api.guardrails_api import router as guardrails_router
from app.api.ledger_api import router as ledger_router
from app.api.simulator_api import router as simulator_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(webhooks_router)
api_router.include_router(recovery_router)
api_router.include_router(guardrails_router)
api_router.include_router(ledger_router)
api_router.include_router(simulator_router)


@api_router.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "system": "AI Revenue Recovery Engine",
        "version": "1.0.0"
    }
