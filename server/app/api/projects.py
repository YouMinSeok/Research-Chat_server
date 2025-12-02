from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.config import get_db
from app.auth import get_current_user
from app.models import User, Project, ProjectMember, ChatRoom
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectMemberResponse,
    JoinProjectRequest,
    ProjectWithMembers
)
from app.utils.invite_code import generate_invite_code

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project and generate a unique invite code.
    The creator is automatically added as 'owner'.
    A project chat room is automatically created.
    """
    # Generate unique invite code
    invite_code = generate_invite_code(db)

    # Create project
    project = Project(
        id=str(uuid.uuid4()),
        name=project_data.name,
        description=project_data.description,
        invite_code=invite_code,
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(project)

    # Add creator as owner
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner",
        joined_at=datetime.utcnow()
    )
    db.add(member)

    # Create project chat room
    chat_room = ChatRoom(
        id=str(uuid.uuid4()),
        name=f"{project_data.name} - 프로젝트 채팅",
        description="프로젝트 전체 채팅방",
        type="project",
        project_id=project.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(chat_room)

    db.commit()
    db.refresh(project)

    return project


@router.post("/join", response_model=ProjectResponse)
async def join_project(
    join_data: JoinProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join a project using an invite code.
    """
    # Find project by invite code
    project = db.query(Project).filter(
        Project.invite_code == join_data.invite_code
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Invalid invite code")

    # Check if already a member
    existing_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project.id,
        ProjectMember.user_id == current_user.id
    ).first()

    if existing_member:
        raise HTTPException(status_code=400, detail="Already a member of this project")

    # Add as member
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="member",
        joined_at=datetime.utcnow()
    )
    db.add(member)
    db.commit()

    return project


@router.get("/my", response_model=List[ProjectResponse])
async def get_my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all projects where the current user is a member.
    """
    memberships = db.query(ProjectMember).filter(
        ProjectMember.user_id == current_user.id
    ).all()

    project_ids = [m.project_id for m in memberships]
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all()

    return projects


@router.get("/{project_id}", response_model=ProjectWithMembers)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get project details with members.
    """
    # Check if user is a member
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get members with user info
    members_query = db.query(ProjectMember, User).join(
        User, ProjectMember.user_id == User.id
    ).filter(ProjectMember.project_id == project_id).all()

    members_response = []
    for pm, user in members_query:
        members_response.append(ProjectMemberResponse(
            id=pm.id,
            project_id=pm.project_id,
            user_id=pm.user_id,
            role=pm.role,
            joined_at=pm.joined_at,
            user_name=user.name,
            user_email=user.email,
            user_role=user.role.value
        ))

    return ProjectWithMembers(
        id=project.id,
        name=project.name,
        description=project.description,
        invite_code=project.invite_code,
        created_by=project.created_by,
        created_at=project.created_at,
        members=members_response
    )


@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
async def get_project_members(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all members of a project.
    """
    # Check if user is a member
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this project")

    # Get members with user info
    members_query = db.query(ProjectMember, User).join(
        User, ProjectMember.user_id == User.id
    ).filter(ProjectMember.project_id == project_id).all()

    members_response = []
    for pm, user in members_query:
        members_response.append(ProjectMemberResponse(
            id=pm.id,
            project_id=pm.project_id,
            user_id=pm.user_id,
            role=pm.role,
            joined_at=pm.joined_at,
            user_name=user.name,
            user_email=user.email,
            user_role=user.role.value
        ))

    return members_response


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project (owner only).
    """
    # Check if user is the owner
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == current_user.id,
        ProjectMember.role == "owner"
    ).first()

    if not member:
        raise HTTPException(
            status_code=403,
            detail="Only the project owner can delete the project"
        )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully"}
