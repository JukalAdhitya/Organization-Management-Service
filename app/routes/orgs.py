from fastapi import APIRouter, HTTPException, status, Depends
from app.models import OrgCreate, OrgOut, OrgUpdate
from app.auth import get_current_admin
from app.services.org_service import OrganizationService


router = APIRouter(prefix="/org", tags=["org"])

@router.post("/create", response_model=OrgOut)
async def create_org(payload: OrgCreate):
    """
    Creates a new organization + admin + dynamic collection.
    Delegates to OrganizationService.
    """
    return await OrganizationService.create_organization(payload)


@router.get("/get", response_model=OrgOut)
async def get_org(organization_name: str):
    """
    Retrieves organization metadata.
    Delegates to OrganizationService.
    """
    return await OrganizationService.get_organization(organization_name)


@router.put("/update", response_model=OrgOut)
async def update_org(payload: OrgUpdate, current_admin: dict = Depends(get_current_admin)):
    """
    Updates organization settings or renames organization (triggering data sync).
    Delegates to OrganizationService.
    """
    return await OrganizationService.update_organization(current_admin, payload)


@router.delete("/delete")
async def delete_org(organization_name: str, current_admin: dict = Depends(get_current_admin)):
    """
    Deletes an organization and its data.
    Delegates to OrganizationService.
    """
    return await OrganizationService.delete_organization(organization_name, current_admin)
