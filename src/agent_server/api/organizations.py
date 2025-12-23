"""Routes for organization management."""

from fastapi import APIRouter, Depends

from ..core.auth_deps import get_current_user
from ..models import (
    MembershipCreate,
    MembershipUpdate,
    OrganizationCreate,
    OrganizationMember,
    OrganizationView,
    OrganizationWithMembers,
    User,
)
from ..services.organization_service import (
    OrganizationService,
    get_organization_service,
)

router = APIRouter()


@router.post("/organizations", response_model=OrganizationWithMembers)
async def create_organization(
    request: OrganizationCreate,
    user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationWithMembers:
    """Create a new organization where the caller becomes admin."""
    return await service.create_organization(request, user.identity)


@router.get("/organizations", response_model=list[OrganizationView])
async def list_organizations(
    user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> list[OrganizationView]:
    """List organizations the caller belongs to."""
    return await service.list_organizations(user.identity)


@router.get("/organizations/{org_id}", response_model=OrganizationWithMembers)
async def get_organization(
    org_id: str,
    user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationWithMembers:
    """Get organization details if the caller is a member."""
    return await service.get_organization(org_id, user.identity)


@router.get("/organizations/{org_id}/members", response_model=list[OrganizationMember])
async def list_members(
    org_id: str,
    user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> list[OrganizationMember]:
    """List members of an organization (requires membership)."""
    organization = await service.get_organization(org_id, user.identity)
    return organization.members


@router.post("/organizations/{org_id}/members", response_model=OrganizationMember)
async def add_member(
    org_id: str,
    request: MembershipCreate,
    user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationMember:
    """Add a member to the organization (admin only)."""
    return await service.add_member(org_id, request, user.identity)


@router.patch("/organizations/{org_id}/members/{member_id}", response_model=OrganizationMember)
async def update_member(
    org_id: str,
    member_id: str,
    request: MembershipUpdate,
    user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> OrganizationMember:
    """Update a member role (admin only)."""
    return await service.update_member(org_id, member_id, request, user.identity)


@router.delete("/organizations/{org_id}/members/{member_id}")
async def remove_member(
    org_id: str,
    member_id: str,
    user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> None:
    """Remove a member from the organization (admin only)."""
    return await service.remove_member(org_id, member_id, user.identity)


@router.delete("/organizations/{org_id}", status_code=204)
async def delete_organization(
    org_id: str,
    user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service),
) -> None:
    """Delete an organization (admin only)."""
    await service.delete_organization(org_id, user.identity)
