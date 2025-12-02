from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: str
    invite_code: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ProjectMember Schemas
class ProjectMemberBase(BaseModel):
    user_id: str
    role: str = "member"


class ProjectMemberResponse(BaseModel):
    id: int
    project_id: str
    user_id: str
    role: str
    joined_at: datetime

    # User info
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None

    class Config:
        from_attributes = True


# Join Project Request
class JoinProjectRequest(BaseModel):
    invite_code: str


# Project with members
class ProjectWithMembers(ProjectResponse):
    members: List[ProjectMemberResponse] = []

    class Config:
        from_attributes = True
