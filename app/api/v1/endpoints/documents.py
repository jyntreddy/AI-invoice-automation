import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.core.security import get_optional_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.invoice import Invoice as InvoiceModel
from app.services.document_parser import document_parser
from app.services.classification_service import classification_service
from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.schemas.response_schema import Response
from app.schemas.invoice_schema import Invoice
from datetime import datetime
import aiofiles

router = APIRouter()


@router.post("/upload", response_model=Response[Invoice])
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Upload and process a document."""
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, 'public')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    try:
        # Parse document
        parsed_data = document_parser.parse_document(file_path)
        text_content = parsed_data.get('text', '')
        
        # Extract basic fields
        extracted_fields = document_parser.extract_invoice_fields(text_content)
        
        # Classify document
        classification = classification_service.classify_document(text_content)
        
        # Extract detailed data using AI
        extracted_data = classification_service.extract_invoice_data(text_content)
        
        # Generate summary
        ai_summary = classification_service.generate_summary(text_content)
        
        # Generate embedding
        embedding = embedding_service.generate_embedding(text_content)
        
        # Create invoice record
        invoice = InvoiceModel(
            owner_id=1,
            file_name=file.filename,
            file_path=file_path,
            file_type=file_ext,
            file_size=file_size,
            raw_text=text_content[:10000],  # Store first 10k chars
            document_type=classification['category'],
            category=classification['category'],
            classification_confidence=classification['confidence'],
            invoice_number=extracted_data.get('invoice_number') or extracted_fields.get('invoice_number'),
            vendor_name=extracted_data.get('vendor_name') or extracted_fields.get('vendor_name'),
            vendor_email=extracted_data.get('vendor_email') or extracted_fields.get('vendor_email'),
            total=extracted_data.get('total') or extracted_fields.get('total'),
            tax=extracted_data.get('tax'),
            amount=extracted_data.get('subtotal'),
            currency=extracted_data.get('currency', 'USD'),
            extracted_data=extracted_data,
            ai_summary=ai_summary,
            ai_confidence=classification['confidence'],
            is_processed=True,
            status="pending",
            processed_at=datetime.utcnow(),
            embedding_id=f"invoice_{file_id}"
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        # Store embedding in Pinecone
        pinecone_service.upsert_vector(
            vector_id=invoice.embedding_id,
            embedding=embedding,
            metadata={
                'invoice_id': invoice.id,
                'user_id': 1,
                'file_name': file.filename,
                'category': classification['category'],
                'invoice_number': invoice.invoice_number,
                'vendor_name': invoice.vendor_name,
                'total': invoice.total,
                'text': text_content[:1000]  # Store first 1000 chars
            }
        )
        
        return Response(
            success=True,
            message="Document uploaded and processed successfully",
            data=invoice
        )
        
    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@router.post("/upload-batch", response_model=Response[List[Invoice]])
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Upload and process multiple documents."""
    results = []
    errors = []
    
    for file in files:
        try:
            # Process each file (reuse logic from single upload)
            result = await upload_document(file, db, current_user)
            results.append(result.data)
        except Exception as e:
            errors.append({
                'filename': file.filename,
                'error': str(e)
            })
    
    return Response(
        success=True,
        message=f"Processed {len(results)} documents successfully. {len(errors)} errors.",
        data=results
    )


@router.get("/{invoice_id}/download")
async def download_document(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Download original document."""
    from fastapi.responses import FileResponse
    
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        True
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if not os.path.exists(invoice.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(
        path=invoice.file_path,
        filename=invoice.file_name,
        media_type="application/octet-stream"
    )


@router.post("/{invoice_id}/reprocess", response_model=Response[Invoice])
async def reprocess_document(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Reprocess a document (re-extract and re-classify)."""
    invoice = db.query(InvoiceModel).filter(
        InvoiceModel.id == invoice_id,
        True
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if not os.path.exists(invoice.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original file not found"
        )
    
    try:
        # Re-parse document
        parsed_data = document_parser.parse_document(invoice.file_path)
        text_content = parsed_data.get('text', '')
        
        # Re-classify
        classification = classification_service.classify_document(text_content)
        
        # Re-extract data
        extracted_data = classification_service.extract_invoice_data(text_content)
        
        # Update invoice
        invoice.raw_text = text_content[:10000]
        invoice.category = classification['category']
        invoice.classification_confidence = classification['confidence']
        invoice.extracted_data = extracted_data
        invoice.invoice_number = extracted_data.get('invoice_number')
        invoice.vendor_name = extracted_data.get('vendor_name')
        invoice.total = extracted_data.get('total')
        invoice.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(invoice)
        
        return Response(
            success=True,
            message="Document reprocessed successfully",
            data=invoice
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reprocessing failed: {str(e)}"
        )
