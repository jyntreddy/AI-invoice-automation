#!/usr/bin/env python3
"""
Cron job script to sync Gmail attachments periodically.
Run this script using cron or a task scheduler.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.gmail_service import gmail_service
from app.services.document_parser import document_parser
from app.services.classification_service import classification_service
from app.services.embedding_service import embedding_service
from app.services.pinecone_service import pinecone_service
from app.db.session import SessionLocal
from app.models.user import User
from app.models.invoice import Invoice
from app.core.config import settings
from app.core.logging import get_logger
from datetime import datetime

logger = get_logger()


def sync_gmail_for_user(user_id: int, max_messages: int = 20):
    """Sync Gmail attachments for a specific user."""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.gmail_connected:
            logger.warning(f"User {user_id} not found or Gmail not connected")
            return
        
        logger.info(f"Starting Gmail sync for user: {user.email}")
        
        # Authenticate Gmail
        if not gmail_service.service:
            gmail_service.authenticate()
        
        # Get messages with attachments
        messages = gmail_service.get_messages_with_attachments(
            file_types=settings.ALLOWED_EXTENSIONS
        )[:max_messages]
        
        processed_count = 0
        upload_dir = os.path.join(settings.UPLOAD_DIR, str(user.id), "gmail")
        
        for message in messages:
            # Check if already processed
            existing = db.query(Invoice).filter(
                Invoice.gmail_message_id == message['id']
            ).first()
            
            if existing:
                continue
            
            # Process attachments
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
                    # Parse and process
                    parsed_data = document_parser.parse_document(file_path)
                    text_content = parsed_data.get('text', '')
                    
                    classification = classification_service.classify_document(text_content)
                    extracted_data = classification_service.extract_invoice_data(text_content)
                    ai_summary = classification_service.generate_summary(text_content)
                    embedding = embedding_service.generate_embedding(text_content)
                    
                    # Create invoice record
                    invoice = Invoice(
                        owner_id=user.id,
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
                            'user_id': user.id,
                            'file_name': filename,
                            'category': classification['category']
                        }
                    )
                    
                    processed_count += 1
                    logger.info(f"Processed: {filename}")
                    
                    # Mark as read
                    gmail_service.mark_as_read(message['id'])
                    
                except Exception as e:
                    logger.error(f"Error processing {filename}: {str(e)}")
                    continue
        
        logger.info(f"Gmail sync completed. Processed {processed_count} documents.")
        
    except Exception as e:
        logger.error(f"Gmail sync failed: {str(e)}")
    finally:
        db.close()


def sync_all_users():
    """Sync Gmail for all users with Gmail connected."""
    db = SessionLocal()
    
    try:
        users = db.query(User).filter(User.gmail_connected == True).all()
        logger.info(f"Found {len(users)} users with Gmail connected")
        
        for user in users:
            sync_gmail_for_user(user.id)
            
    except Exception as e:
        logger.error(f"Error syncing all users: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting Gmail sync cron job")
    sync_all_users()
    logger.info("Gmail sync cron job completed")
