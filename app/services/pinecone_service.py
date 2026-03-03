from typing import List, Dict, Any, Optional
import time

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not available - semantic search will be disabled")


class PineconeService:
    """Service for vector storage and semantic search using Pinecone."""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Pinecone client and index."""
        try:
            if not PINECONE_AVAILABLE:
                logger.warning("Pinecone SDK not installed")
                return
                
            if not settings.PINECONE_API_KEY:
                logger.warning("Pinecone API key not configured")
                return
            
            # Initialize Pinecone
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists, create if not
            index_name = settings.PINECONE_INDEX_NAME
            existing_indexes = self.pc.list_indexes()
            
            if index_name not in [idx.name for idx in existing_indexes]:
                logger.info(f"Creating Pinecone index: {index_name}")
                self.pc.create_index(
                    name=index_name,
                    dimension=settings.PINECONE_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )
                # Wait for index to be ready
                time.sleep(1)
            
            # Connect to index
            self.index = self.pc.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            # Don't raise - allow app to continue without Pinecone
            self.pc = None
            self.index = None
    
    def upsert_vector(
        self,
        vector_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """Insert or update a vector in the index."""
        if not self.index:
            raise Exception("Pinecone index not initialized")
        
        try:
            self.index.upsert(
                vectors=[
                    {
                        "id": vector_id,
                        "values": embedding,
                        "metadata": metadata
                    }
                ]
            )
            logger.info(f"Upserted vector: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert vector: {str(e)}")
            return False
    
    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]]
    ) -> bool:
        """Batch insert or update vectors."""
        if not self.index:
            raise Exception("Pinecone index not initialized")
        
        try:
            formatted_vectors = [
                {
                    "id": v["id"],
                    "values": v["embedding"],
                    "metadata": v.get("metadata", {})
                }
                for v in vectors
            ]
            
            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(formatted_vectors), batch_size):
                batch = formatted_vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            logger.info(f"Upserted {len(vectors)} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {str(e)}")
            return False
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if not self.index:
            raise Exception("Pinecone index not initialized")
        
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=include_metadata
            )
            
            # Format results
            matches = []
            for match in results.get('matches', []):
                matches.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {})
                })
            
            logger.info(f"Found {len(matches)} matches")
            return matches
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector by ID."""
        if not self.index:
            raise Exception("Pinecone index not initialized")
        
        try:
            self.index.delete(ids=[vector_id])
            logger.info(f"Deleted vector: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vector: {str(e)}")
            return False
    
    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """Delete multiple vectors by IDs."""
        if not self.index:
            raise Exception("Pinecone index not initialized")
        
        try:
            self.index.delete(ids=vector_ids)
            logger.info(f"Deleted {len(vector_ids)} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        if not self.index:
            raise Exception("Pinecone index not initialized")
        
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.get('total_vector_count', 0),
                'dimension': stats.get('dimension', 0),
                'index_fullness': stats.get('index_fullness', 0),
                'namespaces': stats.get('namespaces', {})
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            return {}


# Singleton instance
pinecone_service = PineconeService()
