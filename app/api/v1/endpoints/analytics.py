from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from app.core.security import get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.models.invoice import Invoice as InvoiceModel
from app.schemas.response_schema import Response

router = APIRouter()


@router.get("/overview", response_model=Response[Dict[str, Any]])
async def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get overall analytics overview."""
    # Total invoices
    total_invoices = db.query(func.count(InvoiceModel.id)).filter(
        True
    ).scalar()
    
    # Total amount
    total_amount = db.query(func.sum(InvoiceModel.total)).filter(
        True
    ).scalar() or 0
    
    # By status
    status_counts = db.query(
        InvoiceModel.status,
        func.count(InvoiceModel.id)
    ).filter(
        True
    ).group_by(InvoiceModel.status).all()
    
    # By category
    category_counts = db.query(
        InvoiceModel.category,
        func.count(InvoiceModel.id)
    ).filter(
        True
    ).group_by(InvoiceModel.category).all()
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_count = db.query(func.count(InvoiceModel.id)).filter(
        True,
        InvoiceModel.created_at >= thirty_days_ago
    ).scalar()
    
    # Average processing time
    avg_processing_time = db.query(
        func.avg(
            func.extract('epoch', InvoiceModel.processed_at - InvoiceModel.created_at)
        )
    ).filter(
        True,
        InvoiceModel.processed_at.isnot(None)
    ).scalar()
    
    return Response(
        success=True,
        message="Analytics overview retrieved",
        data={
            'total_invoices': total_invoices,
            'total_amount': float(total_amount),
            'by_status': dict(status_counts),
            'by_category': dict(category_counts),
            'recent_invoices_30d': recent_count,
            'avg_processing_time_seconds': float(avg_processing_time) if avg_processing_time else 0
        }
    )


@router.get("/trends", response_model=Response[Dict[str, Any]])
async def get_trends(
    period: str = "month",  # day, week, month, year
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get trend data for invoices over time."""
    # Determine grouping based on period
    if period == "day":
        time_format = func.date_trunc('day', InvoiceModel.created_at)
    elif period == "week":
        time_format = func.date_trunc('week', InvoiceModel.created_at)
    elif period == "month":
        time_format = func.date_trunc('month', InvoiceModel.created_at)
    else:
        time_format = func.date_trunc('year', InvoiceModel.created_at)
    
    # Count by period
    trends = db.query(
        time_format.label('period'),
        func.count(InvoiceModel.id).label('count'),
        func.sum(InvoiceModel.total).label('total_amount')
    ).filter(
        True
    ).group_by('period').order_by('period').all()
    
    formatted_trends = [
        {
            'period': t.period.isoformat() if t.period else None,
            'count': t.count,
            'total_amount': float(t.total_amount) if t.total_amount else 0
        }
        for t in trends
    ]
    
    return Response(
        success=True,
        message="Trend data retrieved",
        data={
            'period': period,
            'trends': formatted_trends
        }
    )


@router.get("/top-vendors", response_model=Response[List[Dict[str, Any]]])
async def get_top_vendors(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get top vendors by transaction count and amount."""
    vendors = db.query(
        InvoiceModel.vendor_name,
        func.count(InvoiceModel.id).label('transaction_count'),
        func.sum(InvoiceModel.total).label('total_amount'),
        func.avg(InvoiceModel.total).label('avg_amount')
    ).filter(
        True,
        InvoiceModel.vendor_name.isnot(None)
    ).group_by(InvoiceModel.vendor_name).order_by(
        func.sum(InvoiceModel.total).desc()
    ).limit(limit).all()
    
    formatted_vendors = [
        {
            'vendor_name': v.vendor_name,
            'transaction_count': v.transaction_count,
            'total_amount': float(v.total_amount) if v.total_amount else 0,
            'avg_amount': float(v.avg_amount) if v.avg_amount else 0
        }
        for v in vendors
    ]
    
    return Response(
        success=True,
        message=f"Retrieved top {len(formatted_vendors)} vendors",
        data=formatted_vendors
    )


@router.get("/classification-accuracy", response_model=Response[Dict[str, Any]])
async def get_classification_accuracy(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get classification accuracy metrics."""
    # Average confidence
    avg_confidence = db.query(
        func.avg(InvoiceModel.classification_confidence)
    ).filter(
        True,
        InvoiceModel.classification_confidence.isnot(None)
    ).scalar()
    
    # Confidence distribution
    high_confidence = db.query(func.count(InvoiceModel.id)).filter(
        True,
        InvoiceModel.classification_confidence >= 0.9
    ).scalar()
    
    medium_confidence = db.query(func.count(InvoiceModel.id)).filter(
        True,
        InvoiceModel.classification_confidence >= 0.7,
        InvoiceModel.classification_confidence < 0.9
    ).scalar()
    
    low_confidence = db.query(func.count(InvoiceModel.id)).filter(
        True,
        InvoiceModel.classification_confidence < 0.7
    ).scalar()
    
    return Response(
        success=True,
        message="Classification accuracy metrics retrieved",
        data={
            'average_confidence': float(avg_confidence) if avg_confidence else 0,
            'high_confidence_count': high_confidence,
            'medium_confidence_count': medium_confidence,
            'low_confidence_count': low_confidence
        }
    )


@router.get("/monthly-report", response_model=Response[Dict[str, Any]])
async def get_monthly_report(
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get detailed monthly report."""
    if not year:
        year = datetime.utcnow().year
    if not month:
        month = datetime.utcnow().month
    
    invoices = db.query(InvoiceModel).filter(
        True,
        extract('year', InvoiceModel.created_at) == year,
        extract('month', InvoiceModel.created_at) == month
    ).all()
    
    total_count = len(invoices)
    total_amount = sum(inv.total or 0 for inv in invoices)
    processed_count = sum(1 for inv in invoices if inv.is_processed)
    
    # By category
    by_category = {}
    for inv in invoices:
        cat = inv.category or 'uncategorized'
        if cat not in by_category:
            by_category[cat] = {'count': 0, 'amount': 0}
        by_category[cat]['count'] += 1
        by_category[cat]['amount'] += inv.total or 0
    
    return Response(
        success=True,
        message=f"Monthly report for {year}-{month:02d}",
        data={
            'year': year,
            'month': month,
            'total_invoices': total_count,
            'total_amount': total_amount,
            'processed_invoices': processed_count,
            'by_category': by_category
        }
    )
