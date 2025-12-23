"""Organization and membership models."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    """Request model for creating an organization."""

    name: str = Field(..., description="Display name for the organization")


class Organization(BaseModel):
    """Organization entity."""

    org_id: str
    name: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationView(Organization):
    """Organization plus the requesting user's role."""

    role: str


class OrganizationMember(BaseModel):
    """Organization membership details."""

    org_id: str
    user_id: str
    role: str
    invited_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationWithMembers(Organization):
    """Organization with member listing."""

    members: list[OrganizationMember] = Field(default_factory=list)


class MembershipUpdate(BaseModel):
    """Update membership role."""

    role: str = Field(..., description="New role for the member (admin/staff)")


class MembershipCreate(BaseModel):
    """Add a member to an organization."""

    user_id: str = Field(..., description="User to add")
    role: str = Field(..., description="Role for the user (admin/staff)")
