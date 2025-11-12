from typing import List
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings


class EmbeddingService:
    """
    Service for generating text embeddings.
    Uses Ollama embeddings by default, but can be extended.
    """
    
    def __init__(
        self,
        model_name: str = "embeddinggemma",
        base_url: str = "http://localhost:11434"
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: Ollama embedding model name
                       (embeddinggemma is a good default for embeddings)
            base_url: Ollama API base URL
        """
        self.model_name = model_name
        self.base_url = base_url
        self._embeddings: Optional[Embeddings] = None
    
    @property
    def embeddings(self) -> Embeddings:
        """
        Get LangChain embeddings instance (lazy initialization).
        
        Returns:
            LangChain Embeddings instance
        """
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                model=self.model_name,
                base_url=self.base_url
            )
        return self._embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)
