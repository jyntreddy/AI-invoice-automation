from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.models.invoice import Invoice as InvoiceModel
from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.schemas.invoice_schema import InvoiceSearchQuery, Invoice
from app.schemas.response_schema import Response

router = APIRouter()


@router.post("/semantic", response_model=Response[List[Invoice]])
async def semantic_search(
    search_query: InvoiceSearchQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Perform semantic search on invoices using Pinecone."""
    try:
        # Generate embedding for query
        query_embedding = embedding_service.generate_embedding(search_query.query)
        
        # Search in Pinecone
        results = pinecone_service.search(
            query_embedding=query_embedding,
            top_k=search_query.top_k,
            filter_dict={'user_id': 1},
            include_metadata=True
        )
        
        # Filter by minimum score
        filtered_results = [
            r for r in results 
            if r['score'] >= search_query.min_score
        ]
        
        # Get invoice details from database
        invoice_ids = [r['metadata']['invoice_id'] for r in filtered_results]
        invoices = db.query(InvoiceModel).filter(
            InvoiceModel.id.in_(invoice_ids),
            True
        ).all()
        
        # Sort by relevance score
        invoice_map = {inv.id: inv for inv in invoices}
        sorted_invoices = []
        for result in filtered_results:
            inv_id = result['metadata']['invoice_id']
            if inv_id in invoice_map:
                sorted_invoices.append(invoice_map[inv_id])
        
        return Response(
            success=True,
            message=f"Found {len(sorted_invoices)} matching invoices",
            data=sorted_invoices
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/keyword", response_model=Response[List[Invoice]])
async def keyword_search(
    q: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Perform keyword-based search on invoices."""
    from sqlalchemy import or_
    
    search_term = f"%{q}%"
    
    invoices = db.query(InvoiceModel).filter(
        True,
        or_(
            InvoiceModel.invoice_number.ilike(search_term),
            InvoiceModel.vendor_name.ilike(search_term),
            InvoiceModel.raw_text.ilike(search_term),
            InvoiceModel.subject.ilike(search_term)
        )
    ).offset(skip).limit(limit).all()
    
    return Response(
        success=True,
        message=f"Found {len(invoices)} matching invoices",
        data=invoices
    )


@router.post("/similar/{invoice_id}", response_model=Response[List[Invoice]])
async def find_similar_invoices(
    invoice_id: int,
    top_k: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Find similar invoices based on content."""
    # Get the source invoice
    source_invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        True
    ).first()
    
    if not source_invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    try:
        # Generate embedding for the source invoice
        query_embedding = embedding_service.generate_embedding(
            source_invoice.raw_text or ""
        )
        
        # Search for similar documents
        results = pinecone_service.search(
            query_embedding=query_embedding,
            top_k=top_k + 1,  # +1 to exclude self
            filter_dict={'user_id': 1},
            include_metadata=True
        )
        
        # Filter out the source invoice
        filtered_results = [
            r for r in results 
            if r['metadata'].get('invoice_id') != invoice_id
        ][:top_k]
        
        # Get invoice details
        invoice_ids = [r['metadata']['invoice_id'] for r in filtered_results]
        similar_invoices = db.query(InvoiceModel).filter(
            InvoiceModel.id.in_(invoice_ids)
        ).all()
        
        return Response(
            success=True,
            message=f"Found {len(similar_invoices)} similar invoices",
            data=similar_invoices
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similar search failed: {str(e)}"
        )


@router.get("/suggestions", response_model=Response[List[str]])
async def get_search_suggestions(
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get search suggestions based on existing data."""
    from sqlalchemy import func, distinct
    
    suggestions = []
    
    # Get vendor name suggestions
    vendors = db.query(distinct(InvoiceModel.vendor_name)).filter(
        True,
        InvoiceModel.vendor_name.ilike(f"%{q}%")
    ).limit(limit).all()
    
    suggestions.extend([v[0] for v in vendors if v[0]])
    
    # Get invoice number suggestions
    if len(suggestions) < limit:
        invoice_nums = db.query(distinct(InvoiceModel.invoice_number)).filter(
            True,
            InvoiceModel.invoice_number.ilike(f"%{q}%")
        ).limit(limit - len(suggestions)).all()
        
        suggestions.extend([i[0] for i in invoice_nums if i[0]])
    
    return Response(
        success=True,
        message=f"Found {len(suggestions)} suggestions",
        data=suggestions[:limit]
    )
