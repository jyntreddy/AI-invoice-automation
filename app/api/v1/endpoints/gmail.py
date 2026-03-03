from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_optional_user
from app.db.session import get_db
from app.models.user import User
from app.models.invoice import Invoice as InvoiceModel
from app.services.gmail_service import gmail_service
from app.services.document_parser import document_parser
from app.services.classification_service import classification_service
from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.schemas.response_schema import Response
from app.schemas.invoice_schema import Invoice
from app.core.config import settings
from datetime import datetime
import os

router = APIRouter()


@router.post("/connect", response_model=Response)
async def connect_gmail(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Connect Gmail account using OAuth2."""
    try:
        success = gmail_service.authenticate()
        
        if success:
            db.commit()
            
            return Response(
                success=True,
                message="Gmail connected successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to connect Gmail"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gmail connection failed: {str(e)}"
        )


@router.post("/disconnect", response_model=Response)
async def disconnect_gmail(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Disconnect Gmail account."""
    db.commit()
    
    return Response(
        success=True,
        message="Gmail disconnected successfully"
    )


@router.get("/messages", response_model=Response[List[Dict[str, Any]]])
async def get_gmail_messages(
    max_results: int = 50,
    query: str = "has:attachment",
    current_user: User = Depends(get_optional_user)
):
    """Get Gmail messages with attachments - open access."""
    try:
        if not gmail_service.service:
            gmail_service.authenticate()
        
        messages = gmail_service.get_messages(query=query, max_results=max_results)
        detailed_messages = []
        
        for msg in messages[:10]:  # Limit detailed fetch
            details = gmail_service.get_message_details(msg['id'])
            if details:
                detailed_messages.append(details)
        
        return Response(
            success=True,
            message=f"Retrieved {len(detailed_messages)} messages",
            data=detailed_messages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )


@router.post("/sync", response_model=Response[List[Invoice]])
async def sync_gmail_attachments(
    max_messages: int = 20,
    file_types: List[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Sync Gmail attachments and process them - open access."""
    try:
        if not gmail_service.service:
            gmail_service.authenticate()
        
        # Get messages with attachments
        file_types = file_types or settings.ALLOWED_EXTENSIONS
        messages = gmail_service.get_messages_with_attachments(
            file_types=file_types
        )[:max_messages]
        
        processed_invoices = []
        
        for message in messages:
            # Check if already processed
            existing = db.query(InvoiceModel).filter(
                InvoiceModel.gmail_message_id == message['id']
            ).first()
            
            if existing:
                continue
            
            # Download and process attachments
            for attachment in message['attachments']:
                filename = attachment['filename']
                file_ext = os.path.splitext(filename)[1].lower().replace('.', '')
                
                if file_ext not in settings.ALLOWED_EXTENSIONS:
                    continue
                
                # Download attachment
                file_path = gmail_service.download_attachment(
                    message_id=message['id'],
                    attachment_id=attachment['attachment_id'],
                    filename=filename,
                    output_dir=upload_dir
                )
                
                if not file_path:
                    continue
                
                try:
                    # Parse and process document
                    parsed_data = document_parser.parse_document(file_path)
                    text_content = parsed_data.get('text', '')
                    
                    # Classify and extract
                    classification = classification_service.classify_document(text_content)
                    extracted_data = classification_service.extract_invoice_data(text_content)
                    ai_summary = classification_service.generate_summary(text_content)
                    
                    # Generate embedding
                    embedding = embedding_service.generate_embedding(text_content)
                    
                    # Create invoice record
                    invoice = InvoiceModel(
                        owner_id=1,
                        file_name=filename,
                        file_path=file_path,
                        file_type=file_ext,
                        file_size=attachment['size'],
                        raw_text=text_content[:10000],
                        document_type=classification['category'],
                        category=classification['category'],
                        classification_confidence=classification['confidence'],
                        gmail_message_id=message['id'],
                        gmail_thread_id=message['thread_id'],
                        from_email=message['from'],
                        subject=message['subject'],
                        invoice_number=extracted_data.get('invoice_number'),
                        vendor_name=extracted_data.get('vendor_name'),
                        vendor_email=extracted_data.get('vendor_email'),
                        total=extracted_data.get('total'),
                        extracted_data=extracted_data,
                        ai_summary=ai_summary,
                        ai_confidence=classification['confidence'],
                        is_processed=True,
                        status="pending",
                        processed_at=datetime.utcnow(),
                        embedding_id=f"gmail_{message['id']}_{attachment['attachment_id']}"
                    )
                    
                    db.add(invoice)
                    db.commit()
                    db.refresh(invoice)
                    
                    # Store in Pinecone
                    pinecone_service.upsert_vector(
                        vector_id=invoice.embedding_id,
                        embedding=embedding,
                        metadata={
                            'invoice_id': invoice.id,
                            'user_id': 1,
                            'file_name': filename,
                            'category': classification['category'],
                            'from_email': message['from']
                        }
                    )
                    
                    processed_invoices.append(invoice)
                    
                    # Mark email as read
                    gmail_service.mark_as_read(message['id'])
                    
                except Exception as e:
                    # Log error but continue processing
                    print(f"Error processing attachment {filename}: {str(e)}")
                    continue
        
        return Response(
            success=True,
            message=f"Processed {len(processed_invoices)} attachments from Gmail",
            data=processed_invoices
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gmail sync failed: {str(e)}"
        )


@router.get("/status", response_model=Response[Dict[str, Any]])
async def get_gmail_status(
    current_user: User = Depends(get_optional_user)
):
    """Get Gmail connection status."""
    return Response(
        success=True,
        message="Gmail status retrieved",
        data={
            'connected': gmail_service.service is not None,
            'email': 'public-access@example.com'
        }
    )
