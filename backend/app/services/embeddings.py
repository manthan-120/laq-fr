"""Embedding generation using Ollama for the LAQ RAG system."""

from typing import List

import ollama

from app.services.config import Config


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""

    pass


class OllamaConnectionError(EmbeddingError):
    """Raised when cannot connect to Ollama."""

    pass


class OllamaModelNotFoundError(EmbeddingError):
    """Raised when the embedding model is not found."""

    pass


class EmbeddingService:
    """Handles embedding generation using Ollama."""

    def __init__(self, config: Config):
        """Initialize the embedding service.

        Args:
            config: Application configuration
        """
        self.config = config
        self._verify_ollama_connection()

    def _verify_ollama_connection(self) -> None:
        """Verify that Ollama is accessible and the model is available.

        Raises:
            OllamaConnectionError: If cannot connect to Ollama
            OllamaModelNotFoundError: If embedding model not found
        """
        try:
            # Try to list models to verify connection
            ollama.list()
        except Exception as e:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.config.ollama_host}.\n"
                f"Please ensure:\n"
                f"  1. Ollama is installed: https://ollama.ai\n"
                f"  2. Ollama is running: 'ollama serve'\n"
                f"Error: {e}"
            ) from e

    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit within embedding model context.

        The nomic-embed-text model has limited context (~256 tokens).
        Approximate 4 characters per token.
        """
        if not text:
            return text
        # Use max_embedding_tokens (default 256 tokens = ~1024 chars)
        max_chars = max(128, self.config.max_embedding_tokens * 4)
        if len(text) <= max_chars:
            return text
        # Just keep the first part (most important for embeddings)
        return text[:max_chars]

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            ValueError: If text is empty
            EmbeddingError: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Ensure we stay within model context
        text = self._truncate_text(text)

        try:
            response = ollama.embeddings(model=self.config.embedding_model, prompt=text)
            return response["embedding"]
        except KeyError as e:
            raise OllamaModelNotFoundError(
                f"Model '{self.config.embedding_model}' not found.\n"
                f"Run: ollama pull {self.config.embedding_model}"
            ) from e
        except ConnectionError as e:
            raise OllamaConnectionError(
                f"Lost connection to Ollama.\n"
                f"Ensure Ollama is running: 'ollama serve'"
            ) from e
        except Exception as e:
            raise EmbeddingError(f"Unexpected embedding error: {e}") from e

    def embed_batch(
        self, texts: List[str], use_batch_api: bool = True
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts with optimized processing.

        Args:
            texts: List of texts to embed
            use_batch_api: Reserved for future batch API support (currently uses sequential)

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If texts list is empty
            EmbeddingError: If embedding generation fails
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")

        # Note: ollama Python library doesn't support batch embeddings yet
        # Process sequentially but keep parameter for future compatibility
        embeddings = []
        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
            except EmbeddingError as e:
                print(f"⚠️ Failed to embed text {i+1}/{len(texts)}: {e}")
                # Return empty embedding as placeholder
                embeddings.append([])

        return embeddings

    def embed_qa_pairs(
        self,
        qa_pairs: List[dict],
        laq_metadata: dict = None,
        use_enhanced_context: bool = True,
    ) -> List[List[float]]:
        """Generate embeddings for Q&A pairs with optional context enhancement.

        Args:
            qa_pairs: List of dictionaries with 'question' and 'answer' keys
            laq_metadata: Optional metadata (minister, date, laq_type, etc.) to enrich context
            use_enhanced_context: Whether to include metadata in embedding for better quality

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If qa_pairs list is empty
        """
        if not qa_pairs:
            raise ValueError("Q&A pairs list cannot be empty")

        texts = []
        for qa in qa_pairs:
            question = qa.get("question", "")
            answer = qa.get("answer", "")

            if use_enhanced_context and laq_metadata:
                # Enhanced format with context for better semantic search
                context_parts = []
                if laq_metadata.get("laq_type"):
                    context_parts.append(f"Type: {laq_metadata['laq_type']}")
                if laq_metadata.get("minister"):
                    context_parts.append(f"Minister: {laq_metadata['minister']}")
                if laq_metadata.get("date"):
                    context_parts.append(f"Date: {laq_metadata['date']}")

                context = " | ".join(context_parts)
                text = f"[{context}]\nQuestion: {question}\nAnswer: {answer}"
            else:
                # Simple format (backward compatible)
                text = f"Q: {question}\nA: {answer}"

            texts.append(text)

        return self.embed_batch(texts)
