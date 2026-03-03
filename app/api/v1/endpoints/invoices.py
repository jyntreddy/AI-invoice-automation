from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.security import get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.models.invoice import Invoice as InvoiceModel
from app.schemas.invoice_schema import (
    Invoice,
    InvoiceUpdate,
    InvoiceStats
)
from app.schemas.response_schema import Response, PaginatedResponse
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[Invoice])
async def get_invoices(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get all invoices for the current user with filters."""
    query = db.query(InvoiceModel).filter(True)
    
    # Apply filters
    if category:
        query = query.filter(InvoiceModel.category == category)
    if status:
        query = query.filter(InvoiceModel.status == status)
    if start_date:
        query = query.filter(InvoiceModel.created_at >= start_date)
    if end_date:
        query = query.filter(InvoiceModel.created_at <= end_date)
    
    total = query.count()
    invoices = query.order_by(desc(InvoiceModel.created_at)).offset(skip).limit(limit).all()
    
    return PaginatedResponse(
        success=True,
        message=f"Retrieved {len(invoices)} invoices",
        data=invoices,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get("/stats", response_model=Response[InvoiceStats])
async def get_invoice_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get invoice statistics for the current user."""
    invoices = db.query(InvoiceModel).filter(
        True
    ).all()
    
    total_invoices = len(invoices)
    processed_invoices = sum(1 for inv in invoices if inv.is_processed)
    pending_invoices = total_invoices - processed_invoices
    total_amount = sum(inv.total or 0 for inv in invoices)
    
    # Group by category
    invoices_by_category = {}
    for inv in invoices:
        category = inv.category or "uncategorized"
        invoices_by_category[category] = invoices_by_category.get(category, 0) + 1
    
    # Recent invoices (last 10)
    recent_invoices = db.query(InvoiceModel).filter(
        True
    ).order_by(desc(InvoiceModel.created_at)).limit(10).all()
    
    stats = InvoiceStats(
        total_invoices=total_invoices,
        processed_invoices=processed_invoices,
        pending_invoices=pending_invoices,
        total_amount=total_amount,
        invoices_by_category=invoices_by_category,
        recent_invoices=recent_invoices
    )
    
    return Response(
        success=True,
        message="Statistics retrieved successfully",
        data=stats
    )


@router.get("/{invoice_id}", response_model=Response[Invoice])
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get a specific invoice by ID."""
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        True
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return Response(
        success=True,
        message="Invoice retrieved successfully",
        data=invoice
    )


@router.put("/{invoice_id}", response_model=Response[Invoice])
async def update_invoice(
    invoice_id: int,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Update an invoice."""
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        True
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Update fields
    update_data = invoice_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    
    return Response(
        success=True,
        message="Invoice updated successfully",
        data=invoice
    )


@router.delete("/{invoice_id}", response_model=Response)
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Delete an invoice."""
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        True
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    db.delete(invoice)
    db.commit()
    
    return Response(
        success=True,
        message="Invoice deleted successfully"
    )


@router.post("/{invoice_id}/approve", response_model=Response[Invoice])
async def approve_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Approve an invoice."""
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        True
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    invoice.status = "approved"
    invoice.processed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(invoice)
    
    return Response(
        success=True,
        message="Invoice approved successfully",
        data=invoice
    )


@router.post("/{invoice_id}/reject", response_model=Response[Invoice])
async def reject_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Reject an invoice."""
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        True
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    invoice.status = "rejected"
    invoice.processed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(invoice)
    
    return Response(
        success=True,
        message="Invoice rejected successfully",
        data=invoice
    )
