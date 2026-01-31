from fastapi import APIRouter
from .prices.views import router as prices_router

router = APIRouter()
router.include_router(prices_router, prefix="/prices")
