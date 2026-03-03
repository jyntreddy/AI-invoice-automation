from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from app.core.security import get_optional_user
from app.models.user import User
from app.services.classification_service import classification_service
from app.schemas.response_schema import Response

router = APIRouter()


class ClassifyRequest(BaseModel):
    text: str


class ExtractRequest(BaseModel):
    text: str


class SummaryRequest(BaseModel):
    text: str
    max_words: int = 100


class QuestionRequest(BaseModel):
    document_text: str
    question: str


@router.post("/classify", response_model=Response[Dict[str, Any]])
async def classify_text(
    request: ClassifyRequest,
    current_user: User = Depends(get_optional_user)
):
    """Classify document text into categories."""
    try:
        result = classification_service.classify_document(request.text)
        return Response(
            success=True,
            message="Document classified successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )


@router.post("/extract", response_model=Response[Dict[str, Any]])
async def extract_data(
    request: ExtractRequest,
    current_user: User = Depends(get_optional_user)
):
    """Extract structured data from invoice text."""
    try:
        result = classification_service.extract_invoice_data(request.text)
        return Response(
            success=True,
            message="Data extracted successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


@router.post("/summarize", response_model=Response[str])
async def summarize_text(
    request: SummaryRequest,
    current_user: User = Depends(get_optional_user)
):
    """Generate summary of document text."""
    try:
        summary = classification_service.generate_summary(
            request.text,
            max_words=request.max_words
        )
        return Response(
            success=True,
            message="Summary generated successfully",
            data=summary
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Summarization failed: {str(e)}"
        )


@router.post("/question", response_model=Response[str])
async def answer_question(
    request: QuestionRequest,
    current_user: User = Depends(get_optional_user)
):
    """Answer a question about a document."""
    try:
        answer = classification_service.answer_question(
            request.document_text,
            request.question
        )
        return Response(
            success=True,
            message="Question answered successfully",
            data=answer
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed: {str(e)}"
        )
