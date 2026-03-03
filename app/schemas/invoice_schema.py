from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class InvoiceBase(BaseModel):
    document_type: Optional[str] = None
    file_name: str
    file_type: str
    category: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    amount: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    currency: str = "USD"
    vendor_name: Optional[str] = None
    vendor_email: Optional[EmailStr] = None
    customer_name: Optional[str] = None
    status: str = "pending"


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    document_type: Optional[str] = None
    category: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    amount: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    vendor_name: Optional[str] = None
    vendor_email: Optional[EmailStr] = None
    customer_name: Optional[str] = None
    status: Optional[str] = None


class Invoice(InvoiceBase):
    id: int
    file_path: str
    file_size: Optional[int] = None
    classification_confidence: Optional[float] = None
    raw_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    embedding_id: Optional[str] = None
    gmail_message_id: Optional[str] = None
    from_email: Optional[str] = None
    subject: Optional[str] = None
    is_processed: bool
    ai_summary: Optional[str] = None
    ai_confidence: Optional[float] = None
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InvoiceSearchQuery(BaseModel):
    query: str = Field(..., description="Semantic search query")
    top_k: int = Field(default=10, description="Number of results to return")
    min_score: float = Field(default=0.5, description="Minimum similarity score")


class InvoiceStats(BaseModel):
    total_invoices: int
    processed_invoices: int
    pending_invoices: int
    total_amount: float
    invoices_by_category: Dict[str, int]
    recent_invoices: List[Invoice]


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_superuser: bool
    gmail_connected: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
