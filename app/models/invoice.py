from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Document information
    document_type = Column(String, index=True)  # invoice, receipt, purchase_order, etc.
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, csv, docx
    file_size = Column(Integer)  # in bytes
    
    # Classification
    category = Column(String, index=True)
    classification_confidence = Column(Float)
    
    # Invoice details
    invoice_number = Column(String, index=True, nullable=True)
    invoice_date = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Financial information
    amount = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    
    # Parties
    vendor_name = Column(String, nullable=True)
    vendor_email = Column(String, nullable=True)
    vendor_address = Column(Text, nullable=True)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    
    # Extracted content
    raw_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)  # All extracted fields as JSON
    
    # Embedding
    embedding_id = Column(String, nullable=True, index=True)  # Pinecone vector ID
    
    # Gmail metadata
    gmail_message_id = Column(String, nullable=True, index=True)
    gmail_thread_id = Column(String, nullable=True)
    from_email = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="pending")  # pending, processed, approved, rejected
    is_processed = Column(Boolean, default=False)
    
    # AI metadata
    ai_summary = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)
    
    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="invoices")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Invoice {self.invoice_number} - {self.document_type}>"
