import os
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from ..config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class RAGService:
    def __init__(self):
        self.collection = None
        if CHROMA_AVAILABLE:
            self._init_chroma()
        else:
            print("ChromaDB not available. RAG features disabled.")

    def _init_chroma(self):
        try:
            os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
            client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = client.get_or_create_collection(
                name="retail_products",
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            print(f"ChromaDB init failed: {e}. RAG will use fallback search.")
            self.collection = None

    def _make_document(self, product) -> str:
        import json
        aliases = ""
        if product.aliases:
            try:
                alias_list = json.loads(product.aliases)
                aliases = "Aliases: " + ", ".join(alias_list) + ". "
            except (json.JSONDecodeError, TypeError):
                aliases = f"Known as: {product.aliases}. "
        keywords = f"Keywords: {product.search_keywords}. " if product.search_keywords else ""
        return (
            f"Product: {product.name}. "
            f"{aliases}"
            f"{keywords}"
            f"Category: {product.category or 'General'}. "
            f"Supplier: {product.supplier or 'Unknown'}. "
            f"Wholesale Price: {product.wholesale_price}. "
            f"Quantity in Package: {product.quantity_in_package}. "
            f"Unit Type: {product.unit_type or 'piece'}. "
            f"Retail Price: {product.retail_price or 'Calculated on request'}. "
            f"Profit Per Item: {product.profit_per_item or 'Default margin'}."
        )

    def index_product(self, product):
        if self.collection is None:
            return
        try:
            doc = self._make_document(product)
            self.collection.upsert(
                ids=[str(product.id)],
                documents=[doc],
                metadatas=[{
                    "product_id": product.id,
                    "name": product.name,
                    "category": product.category or "",
                    "supplier": product.supplier or "",
                }],
            )
        except Exception as e:
            print(f"Failed to index product {product.id}: {e}")

    def remove_product(self, product_id: int):
        if self.collection is None:
            return
        try:
            self.collection.delete(ids=[str(product_id)])
        except Exception:
            pass

    def semantic_search(self, query: str, n_results: int = 5) -> List[dict]:
        if self.collection is None:
            return []
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            matches = []
            if results["metadatas"] and results["metadatas"][0]:
                for i, meta in enumerate(results["metadatas"][0]):
                    matches.append({
                        "product_id": meta.get("product_id"),
                        "name": meta.get("name", ""),
                        "category": meta.get("category", ""),
                        "supplier": meta.get("supplier", ""),
                        "score": results["distances"][0][i] if results["distances"] else 0,
                    })
            return matches
        except Exception as e:
            print(f"Semantic search failed: {e}")
            return []

    def fuzzy_find(self, query: str, products: list) -> list:
        query_lower = query.lower().strip()
        scored = []

        for p in products:
            name_lower = p.name.lower()
            score = 0

            if query_lower == name_lower:
                score = 100
            elif name_lower.startswith(query_lower):
                score = 90
            elif query_lower in name_lower:
                score = 80
            else:
                query_words = query_lower.split()
                name_words = name_lower.split()
                matches = sum(1 for qw in query_words if qw in name_lower)
                if matches > 0:
                    score = 60 + (matches / len(query_words)) * 20
                else:
                    partial = sum(1 for qw in query_words for nw in name_words if qw in nw or nw in qw)
                    if partial > 0:
                        score = 40 + (partial / (len(query_words) + len(name_words))) * 20

            if score > 0:
                scored.append((p, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, s in scored]


rag_service = RAGService()
