"""Gmail IMAP endpoints for email fetching."""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.security import get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.services.gmail_imap_service import gmail_imap_service
from app.schemas.response_schema import Response

router = APIRouter()


class GmailIMAPConnect(BaseModel):
    """Gmail IMAP connection credentials."""
    email: EmailStr
    password: str


@router.post("/imap/connect", response_model=Response)
async def connect_gmail_imap(
    credentials: GmailIMAPConnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Connect to Gmail via IMAP - open access."""
    result = gmail_imap_service.connect(credentials.email, credentials.password)
    
    if result["success"]:
        return Response(
            success=True,
            message=result["message"],
            data={"email": result["email"]}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"]
        )


@router.post("/imap/disconnect", response_model=Response)
async def disconnect_gmail_imap(
    current_user: User = Depends(get_optional_user)
):
    """Disconnect from Gmail IMAP - open access."""
    gmail_imap_service.disconnect()
    
    return Response(
        success=True,
        message="Disconnected from Gmail"
    )


@router.get("/imap/messages", response_model=Response[List[Dict[str, Any]]])
async def get_imap_messages(
    limit: int = 50,
    has_attachments: bool = True,
    current_user: User = Depends(get_optional_user)
):
    """Get messages from Gmail via IMAP - open access."""
    try:
        if not gmail_imap_service.is_connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not connected to Gmail. Please connect first."
            )
        
        messages = gmail_imap_service.get_messages(
            limit=limit,
            has_attachments=has_attachments
        )
        
        return Response(
            success=True,
            message=f"Retrieved {len(messages)} messages",
            data=messages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/imap/status", response_model=Response)
async def get_imap_status(
    current_user: User = Depends(get_optional_user)
):
    """Get Gmail IMAP connection status - open access."""
    return Response(
        success=True,
        message="IMAP status retrieved",
        data={
            "connected": gmail_imap_service.is_connected,
            "email": gmail_imap_service.email_address if gmail_imap_service.is_connected else None
        }
    )
