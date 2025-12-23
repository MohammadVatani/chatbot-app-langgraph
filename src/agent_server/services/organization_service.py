"""Service layer for organization management."""
"""Business logic for organizations and membership."""

from uuid import uuid4

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.orm import Organization as OrganizationORM
from ..core.orm import OrganizationMember as OrganizationMemberORM
from ..core.orm import get_session
from ..models import (
    MembershipCreate,
    MembershipUpdate,
    Organization,
    OrganizationCreate,
    OrganizationMember,
    OrganizationView,
    OrganizationWithMembers,
)


class OrganizationService:
    """Encapsulates organization business logic."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_membership(self, org_id: str, user_id: str) -> OrganizationMemberORM | None:
        stmt = select(OrganizationMemberORM).where(
            OrganizationMemberORM.org_id == org_id,
            OrganizationMemberORM.user_id == user_id,
        )
        return await self.session.scalar(stmt)

    async def _require_admin(self, org_id: str, user_id: str) -> OrganizationMemberORM:
        membership = await self._get_membership(org_id, user_id)
        if membership is None or membership.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return membership

    async def create_organization(
        self, request: OrganizationCreate, creator_id: str
    ) -> OrganizationWithMembers:
        existing = await self.session.scalar(
            select(OrganizationORM).where(OrganizationORM.name == request.name)
        )
        if existing:
            raise HTTPException(status_code=409, detail="Organization name already used")

        org = OrganizationORM(
            org_id=str(uuid4()),
            name=request.name,
            created_by=creator_id,
        )
        self.session.add(org)

        membership = OrganizationMemberORM(
            org_id=org.org_id,
            user_id=creator_id,
            role="admin",
            invited_by=creator_id,
        )
        self.session.add(membership)
        await self.session.commit()

        await self.session.refresh(org)
        await self.session.refresh(membership)

        return OrganizationWithMembers(
            **Organization.model_validate(org, from_attributes=True).model_dump(),
            members=[OrganizationMember.model_validate(membership, from_attributes=True)],
        )

    async def list_organizations(self, user_id: str) -> list[OrganizationView]:
        memberships = await self.session.scalars(
            select(OrganizationMemberORM).where(OrganizationMemberORM.user_id == user_id)
        )
        memberships = memberships.all()
        if not memberships:
            return []

        org_ids = [m.org_id for m in memberships]
        organizations = await self.session.scalars(
            select(OrganizationORM).where(OrganizationORM.org_id.in_(org_ids))
        )
        org_map = {org.org_id: org for org in organizations.all()}
        return [
            OrganizationView(
                **Organization.model_validate(org_map[m.org_id], from_attributes=True).model_dump(),
                role=m.role,
            )
            for m in memberships
            if m.org_id in org_map
        ]

    async def get_organization(self, org_id: str, user_id: str) -> OrganizationWithMembers:
        membership = await self._get_membership(org_id, user_id)
        if membership is None:
            raise HTTPException(status_code=403, detail="Not a member of this organization")

        org = await self.session.get(OrganizationORM, org_id)
        if org is None:
            raise HTTPException(status_code=404, detail="Organization not found")

        members = await self.session.scalars(
            select(OrganizationMemberORM).where(OrganizationMemberORM.org_id == org_id)
        )
        return OrganizationWithMembers(
            **Organization.model_validate(org, from_attributes=True).model_dump(),
            members=[
                OrganizationMember.model_validate(member, from_attributes=True)
                for member in members.all()
            ],
        )

    async def add_member(
        self, org_id: str, request: MembershipCreate, acting_user_id: str
    ) -> OrganizationMember:
        await self._require_admin(org_id, acting_user_id)

        target_membership = await self._get_membership(org_id, request.user_id)
        if target_membership:
            raise HTTPException(status_code=409, detail="User already in organization")

        member = OrganizationMemberORM(
            org_id=org_id,
            user_id=request.user_id,
            role=request.role,
            invited_by=acting_user_id,
        )
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(member)
        return OrganizationMember.model_validate(member, from_attributes=True)

    async def update_member(
        self, org_id: str, user_id: str, request: MembershipUpdate, acting_user_id: str
    ) -> OrganizationMember:
        await self._require_admin(org_id, acting_user_id)
        membership = await self._get_membership(org_id, user_id)
        if membership is None:
            raise HTTPException(status_code=404, detail="Member not found")

        membership.role = request.role
        await self.session.commit()
        await self.session.refresh(membership)
        return OrganizationMember.model_validate(membership, from_attributes=True)

    async def remove_member(
        self, org_id: str, user_id: str, acting_user_id: str
    ) -> None:
        await self._require_admin(org_id, acting_user_id)
        membership = await self._get_membership(org_id, user_id)
        if membership is None:
            raise HTTPException(status_code=404, detail="Member not found")
        await self.session.delete(membership)
        await self.session.commit()

    async def delete_organization(self, org_id: str, acting_user_id: str) -> None:
        """Delete an organization (admin only)."""
        org = await self.session.get(OrganizationORM, org_id)
        if org is None:
            raise HTTPException(status_code=404, detail="Organization not found")

        await self._require_admin(org_id, acting_user_id)

        await self.session.delete(org)
        await self.session.commit()


async def get_organization_service(
    session: AsyncSession = Depends(get_session),
) -> OrganizationService:
    return OrganizationService(session)
