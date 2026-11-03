from fastapi import APIRouter

from app.api.v1 import (
    customers,
    deliveries,
    orders,
    organizations,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(
    organizations.router,
    prefix="/organizations",
    tags=["Organizations"],
)
api_router.include_router(
    customers.router,
    prefix="/customers",
    tags=["Customers"],
)
api_router.include_router(
    orders.router,
    prefix="/orders",
    tags=["Orders"],
)
api_router.include_router(
    deliveries.router,
    prefix="/deliveries",
    tags=["Deliveries"],
)

# Include recordings router
from app.api.v1 import recordings
api_router.include_router(
    recordings.router,
    prefix="/recordings",
    tags=["Recordings"],
)
