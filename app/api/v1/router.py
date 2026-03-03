from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    invoices,
    documents,
    gmail,
    gmail_imap,
    search,
    analytics,
    classification
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(gmail.router, prefix="/gmail", tags=["Gmail"])
api_router.include_router(gmail_imap.router, prefix="/gmail", tags=["Gmail IMAP"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(classification.router, prefix="/classification", tags=["Classification"])
