from typing import Dict, Any, List, Optional
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()


class ClassificationService:
    """Service for AI-powered document classification using OpenAI."""
    
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.categories = settings.DOCUMENT_CATEGORIES
    
    def classify_document(self, text: str) -> Dict[str, Any]:
        """Classify document using OpenAI GPT."""
        if not self.client:
            raise Exception("OpenAI API key not configured")
        
        try:
            # Truncate text if too long
            max_chars = 4000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            prompt = f"""Analyze the following document and classify it into one of these categories:
{', '.join(self.categories)}

Document text:
{text}

Respond with a JSON object containing:
- category: the most appropriate category
- confidence: a float between 0 and 1 indicating classification confidence
- reasoning: brief explanation for the classification

Response format:
{{"category": "invoice", "confidence": 0.95, "reasoning": "Document contains invoice number, amounts, and vendor details"}}
"""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a document classification expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON response
            import json
            result = json.loads(result_text)
            
            logger.info(f"Document classified as: {result['category']} (confidence: {result['confidence']})")
            return result
            
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            return {
                "category": "other",
                "confidence": 0.0,
                "reasoning": f"Classification error: {str(e)}"
            }
    
    def extract_invoice_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from invoice using OpenAI."""
        if not self.client:
            raise Exception("OpenAI API key not configured")
        
        try:
            prompt = f"""Extract all relevant information from this invoice document. Return a JSON object with the following fields (use null for missing fields):

- invoice_number: string
- invoice_date: string (YYYY-MM-DD format)
- due_date: string (YYYY-MM-DD format)
- vendor_name: string
- vendor_email: string
- vendor_address: string
- customer_name: string
- customer_email: string
- items: array of objects with (description, quantity, unit_price, total)
- subtotal: float
- tax: float
- total: float
- currency: string (e.g., "USD")

Invoice text:
{text[:4000]}

Respond only with valid JSON.
"""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from invoices. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content
            
            # Parse JSON response
            import json
            extracted_data = json.loads(result_text)
            
            logger.info("Successfully extracted invoice data")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            return {}
    
    def generate_summary(self, text: str, max_words: int = 100) -> str:
        """Generate a concise summary of the document."""
        if not self.client:
            raise Exception("OpenAI API key not configured")
        
        try:
            prompt = f"""Provide a concise summary of this document in {max_words} words or less:

{text[:3000]}

Summary:"""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a document summarization expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info("Generated document summary")
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return "Summary unavailable"
    
    def answer_question(self, document_text: str, question: str) -> str:
        """Answer a question about the document using RAG."""
        if not self.client:
            raise Exception("OpenAI API key not configured")
        
        try:
            prompt = f"""Based on the following document, answer the question.

Document:
{document_text[:3000]}

Question: {question}

Answer:"""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            logger.error(f"Question answering failed: {str(e)}")
            return f"Unable to answer: {str(e)}"
    
    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """Split text into chunks for processing."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        return chunks


# Singleton instance
classification_service = ClassificationService()
