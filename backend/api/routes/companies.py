"""
Company metadata endpoints.

These endpoints are reserved for future use when a proper company
data source (database or live API) is added. The previous mock data
has been removed because it was never consumed by the frontend and
returned static, incorrect moat ratings that bypass the live analysis pipeline.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])
