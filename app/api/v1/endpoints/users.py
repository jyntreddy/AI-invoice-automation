from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_optional_user, get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.invoice_schema import User as UserSchema, UserUpdate
from app.schemas.response_schema import Response

router = APIRouter()


@router.get("/", response_model=Response[List[UserSchema]])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get all users - open access."""
    users = db.query(User).offset(skip).limit(limit).all()
    return Response(
        success=True,
        message=f"Retrieved {len(users)} users",
        data=users
    )


@router.get("/{user_id}", response_model=Response[UserSchema])
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get user by ID - open access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return Response(
        success=True,
        message="User retrieved successfully",
        data=user
    )


@router.put("/{user_id}", response_model=Response[UserSchema])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Update user information - open access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return Response(
        success=True,
        message="User updated successfully",
        data=user
    )


@router.delete("/{user_id}", response_model=Response)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Delete a user - open access."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return Response(
        success=True,
        message="User deleted successfully"
    )
