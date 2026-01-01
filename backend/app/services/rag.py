"""RAG (Retrieval-Augmented Generation) operations for LAQ search and chat."""

import json
import math
from typing import Dict, List, Optional, Tuple

import ollama

from app.services.config import Config
from app.services.database import LAQDatabase
from app.services.embeddings import EmbeddingService


class RAGError(Exception):
    """Raised when RAG operations fail."""

    pass


class RAGService:
    """Handles search and chat operations for the LAQ RAG system."""

    def __init__(
        self, config: Config, database: LAQDatabase, embedding_service: EmbeddingService
    ):
        """Initialize the RAG service.

        Args:
            config: Application configuration
            database: Database instance
            embedding_service: Embedding service instance
        """
        self.config = config
        self.db = database
        self.embeddings = embedding_service

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        apply_threshold: bool = True,
    ) -> List[Dict]:
        """Search for relevant LAQs.

        Args:
            query: Search query text
            top_k: Number of results to return (uses config default if None)
            apply_threshold: Whether to filter by similarity threshold

        Returns:
            List of search result dictionaries with metadata and scores

        Raises:
            RAGError: If search fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Format query to match the enhanced embedding format used during storage
            # This improves semantic matching by using the same format
            formatted_query = f"Question: {query}\nAnswer: "

            # Generate query embedding
            query_embedding = self.embeddings.embed_text(formatted_query)

            # Search database
            results = self.db.search(query_embedding, n_results=top_k)

            # Filter by relevance if requested
            if apply_threshold:
                ids, distances, metadatas, documents = self.db.filter_by_relevance(
                    results
                )
            else:
                if not results["ids"] or not results["ids"][0]:
                    return []
                ids = results["ids"][0]
                distances = results["distances"][0]
                metadatas = results["metadatas"][0]
                documents = results.get("documents", [[]])[0]

            # Format results
            formatted_results = []
            for i, doc_id in enumerate(ids):
                distance = distances[i]
                # ChromaDB with "cosine" metric returns squared L2 distance on normalized vectors
                # which is equivalent to: 2 * (1 - cosine_similarity)
                # So: cosine_similarity = 1 - (distance / 2)
                # Convert to percentage: similarity = (1 - distance/2) * 100
                cosine_similarity = 1 - (distance / 2)
                similarity = max(0, min(100, cosine_similarity * 100))

                # Determine match quality
                if similarity >= 80:
                    match_quality = "STRONG MATCH"
                    match_color = "🟢"
                elif similarity >= 60:
                    match_quality = "MODERATE MATCH"
                    match_color = "🟡"
                else:
                    match_quality = "WEAK MATCH"
                    match_color = "🔴"

                meta = metadatas[i]
                doc = documents[i] if i < len(documents) else ""

                # Attach annexure content (preview + full) to metadata for UI display
                # First, collect referenced annexures
                annexure_data = self._collect_annexure_content(
                    laq_num=meta.get("laq_num", ""),
                    referenced_raw=meta.get("referenced_annexures", "[]"),
                    preview_chars=800,
                )
                
                # Also collect ALL available annexures for this LAQ
                all_annexure_data = self._collect_all_annexures(
                    laq_num=meta.get("laq_num", ""),
                    preview_chars=800,
                )
                
                if annexure_data["preview"] or annexure_data["full"] or all_annexure_data["preview"]:
                    meta = dict(meta)
                    meta["annexure_content_preview"] = annexure_data["preview"]
                    meta["annexure_content_full"] = annexure_data["full"]
                    meta["all_annexure_content_preview"] = all_annexure_data["preview"]
                    meta["all_annexure_content_full"] = all_annexure_data["full"]

                formatted_results.append(
                    {
                        "id": doc_id,
                        "similarity": round(similarity, 2),
                        "match_quality": match_quality,
                        "match_color": match_color,
                        "metadata": meta,
                        "document": doc,
                    }
                )

            return formatted_results

        except Exception as e:
            raise RAGError(f"Search failed: {e}") from e

    def chat(self, query: str, top_k: Optional[int] = None) -> Tuple[str, List[Dict]]:
        """Generate a conversational response based on retrieved LAQs.

        Args:
            query: User question
            top_k: Number of LAQs to retrieve for context (uses config default if None)

        Returns:
            Tuple of (response_text, source_laqs)

        Raises:
            RAGError: If chat generation fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Retrieve relevant LAQs
            if top_k is None:
                top_k = self.config.chat_top_k

            results = self.search(query, top_k=top_k, apply_threshold=True)

            if not results:
                return (
                    "I couldn't find any relevant LAQs to answer your question. "
                    "Please try rephrasing your query or upload more documents.",
                    [],
                )

            # Build context from retrieved LAQs
            context = self._build_context(results)

            # Generate response with improved prompt
            prompt = self._build_chat_prompt(context, query)

            response = ollama.generate(
                model=self.config.llm_model,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": self.config.llm_temperature,
                    "top_p": self.config.llm_top_p,
                },
            )

            return response["response"], results

        except Exception as e:
            raise RAGError(f"Chat generation failed: {e}") from e

    def _build_context(self, search_results: List[Dict]) -> str:
        """Build formatted context string from search results.

        Args:
            search_results: List of search result dictionaries

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, result in enumerate(search_results, 1):
            meta = result["metadata"]

            # Parse attachments
            try:
                attachments = json.loads(meta.get("attachments", "[]"))
            except Exception:
                attachments = []

            annexure_content = self._collect_annexure_content(
                laq_num=meta.get("laq_num", ""),
                referenced_raw=meta.get("referenced_annexures", "[]"),
                preview_chars=1000,
            )["preview"]

            attachments_text = (
                f"\nAttachments: {', '.join(attachments)}" if attachments else ""
            )
            annexures_text_block = (
                f"\n\nIncluded Annexure Content:\n" + "\n\n".join(annexure_content)
                if annexure_content
                else ""
            )

            part = f"""
LAQ #{meta.get('laq_num', 'N/A')} ({meta.get('type', 'N/A')}) - {meta.get('date', 'N/A')}
Minister: {meta.get('minister', 'N/A')}
Tabled by: {meta.get('tabled_by', 'N/A')}
Question: {meta.get('question', 'N/A')}
Answer: {meta.get('answer', 'N/A')}{attachments_text}{annexures_text_block}
"""
            context_parts.append(part.strip())

        return "\n\n---\n\n".join(context_parts)

    def _build_chat_prompt(self, context: str, query: str) -> str:
        """Build an improved prompt for chat generation.

        Args:
            context: Formatted context from retrieved LAQs
            query: User question

        Returns:
            Complete prompt for LLM
        """
        prompt = f"""You are an expert assistant for Legislative Assembly Questions (LAQs). Your role is to provide accurate, factual answers based on the LAQ database.

Below are the most relevant LAQs from the database:

{context}

---

INSTRUCTIONS:
1. Answer the user's question based ONLY on the information provided in the LAQs above
2. If the LAQs don't contain sufficient information to answer the question, explicitly state what information is missing
3. Always cite specific LAQ numbers when referencing facts (e.g., "According to LAQ #324...")
4. Be precise, concise, and factual - do not add interpretations or speculation
5. If multiple LAQs contain relevant information, synthesize them coherently
6. If attachments are mentioned (like Annexure-I), reference them in your answer
7. Maintain a professional and helpful tone

USER QUESTION: {query}

ANSWER:"""

        return prompt

    def _collect_annexure_content(
        self,
        laq_num: str,
        referenced_raw: Optional[object],
        preview_chars: int = 800,
    ) -> Dict[str, List[str]]:
        """Fetch annexure content for referenced labels.

        Returns a dict with preview (truncated) and full content lists.
        """
        try:
            if referenced_raw is None:
                return {"preview": [], "full": []}
            if isinstance(referenced_raw, str):
                referenced = json.loads(referenced_raw)
            else:
                referenced = referenced_raw
        except Exception:
            referenced = []

        if not referenced:
            return {"preview": [], "full": []}

        try:
            annexures = self.db.get_annexures_for_laq(laq_num)
        except Exception:
            return {"preview": [], "full": []}

        def _norm(label: str) -> str:
            # Normalize labels like "Annexure-I", "Annexure I", "I", "II" to a comparable key
            if not label:
                return ""
            cleaned = label.lower().replace("annexure", "")
            for ch in ["-", "_", ":", ";", ",", "."]:
                cleaned = cleaned.replace(ch, " ")
            cleaned = "".join(cleaned.split())
            return cleaned

        # Map normalized label -> document text (keep original too)
        label_docs = {}
        for idx, meta in enumerate(annexures.get("metadatas", [])):
            if meta.get("type") == "annexure":
                label = meta.get("annexure_label", "")
                doc_text = annexures.get("documents", [[]])[idx]
                if label:
                    label_docs[_norm(label)] = doc_text
                    label_docs[label] = doc_text

        preview: List[str] = []
        full: List[str] = []
        for label in referenced:
            key = _norm(label)
            # Try normalized match first, then raw
            doc_text = label_docs.get(key) or label_docs.get(label)
            if doc_text:
                preview.append(f"Annexure {label}:\n{doc_text[:preview_chars]}")
                full.append(f"Annexure {label}:\n{doc_text}")
        return {"preview": preview, "full": full}

    def _collect_all_annexures(
        self,
        laq_num: str,
        preview_chars: int = 800,
    ) -> Dict[str, List[str]]:
        """Fetch ALL available annexure content for a LAQ (not just referenced).

        Returns a dict with preview (truncated) and full content lists.
        """
        try:
            annexures = self.db.get_annexures_for_laq(laq_num)
        except Exception:
            return {"preview": [], "full": []}

        preview: List[str] = []
        full: List[str] = []
        
        for idx, meta in enumerate(annexures.get("metadatas", [])):
            if meta.get("type") == "annexure":
                label = meta.get("annexure_label", "")
                doc_text = annexures.get("documents", [[]])[idx]
                if label and doc_text:
                    preview.append(f"Annexure {label}:\n{doc_text[:preview_chars]}")
                    full.append(f"Annexure {label}:\n{doc_text}")
        
        return {"preview": preview, "full": full}

    def get_match_quality_stats(self, results: List[Dict]) -> Dict[str, int]:
        """Get statistics about match quality distribution.

        Args:
            results: List of search results

        Returns:
            Dictionary with counts for each quality level
        """
        stats = {"strong": 0, "moderate": 0, "weak": 0}

        for result in results:
            similarity = result["similarity"]
            if similarity >= 80:
                stats["strong"] += 1
            elif similarity >= 60:
                stats["moderate"] += 1
            else:
                stats["weak"] += 1

        return stats
