"""API routes package."""

from fastapi import APIRouter

from app.api.webhooks import router as webhooks_router
from app.api.inventory import router as inventory_router
from app.api.rates import router as rates_router
from app.api.properties import router as properties_router

api_router = APIRouter()

# Include all routers
api_router.include_router(webhooks_router, prefix="/webhook", tags=["Webhooks"])
api_router.include_router(inventory_router, prefix="/api/v1/inventory", tags=["Inventory"])
api_router.include_router(rates_router, prefix="/api/v1/rates", tags=["Rates"])
api_router.include_router(properties_router, prefix="/api/v1/properties", tags=["Properties"])
