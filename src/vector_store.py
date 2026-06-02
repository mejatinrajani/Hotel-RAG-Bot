import json
import os
import copy
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional

# Constants for file paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
KB_FILE = os.path.join(DATA_DIR, "hotel_kb.json")
FAISS_INDEX_FILE = os.path.join(DATA_DIR, "faiss_index.bin")
CHUNK_MAPPING_FILE = os.path.join(DATA_DIR, "chunk_mapping.json")

class HotelVectorStore:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initializes the local embedding model and FAISS index using Cosine Similarity.
        """
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        
        # Use IndexFlatIP (Inner Product) for Cosine Similarity. 
        # Requires vectors to be L2-normalized before insertion and searching.
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        self.chunk_mapping = {}

    def _format_for_embedding(self, chunk: Dict) -> str:
        """
        Embeds metadata alongside the text to dramatically improve retrieval accuracy.
        """
        text = chunk.get("text", "")
        category = chunk.get("category", "")
        intent = chunk.get("intent", "")
        keywords = ", ".join(chunk.get("keywords", [])) if "keywords" in chunk else ""
        
        parts = []
        if intent:
            parts.append(f"Intent: {intent}")
        if category:
            parts.append(f"Category: {category}")
        if keywords:
            parts.append(f"Keywords: {keywords}")
        parts.append(f"Content: {text}")
        
        return " | ".join(parts)

    def build_index(self):
        """Reads the KB JSON, embeds chunks + negative knowledge, and builds the FAISS index."""
        print(f"Reading Knowledge Base from {KB_FILE}...")
        with open(KB_FILE, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)

        retrieval_chunks = kb_data.get("retrieval_chunks", [])
        negative_knowledge = kb_data.get("negative_knowledge", [])
        
        all_chunks = retrieval_chunks + negative_knowledge

        if not all_chunks:
            raise ValueError("No retrieval chunks or negative knowledge found in the JSON file.")

        texts_to_embed = []
        
        for i, chunk in enumerate(all_chunks):
            # Map the FAISS internal ID (i) to the full chunk data
            self.chunk_mapping[str(i)] = chunk
            # Embed the enriched text (Metadata + Raw Text)
            texts_to_embed.append(self._format_for_embedding(chunk))

        print(f"Embedding {len(texts_to_embed)} chunks (including negative knowledge)...")
        embeddings = self.model.encode(texts_to_embed, convert_to_numpy=True)
        
        # L2-Normalize the embeddings so Inner Product equates to Cosine Similarity
        faiss.normalize_L2(embeddings)

        print("Adding normalized embeddings to FAISS IndexFlatIP...")
        self.index.add(embeddings)

        self._save_to_disk()
        print("Vector store built and saved successfully!")

    def _save_to_disk(self):
        """Saves the FAISS index and the chunk dictionary for retrieval."""
        faiss.write_index(self.index, FAISS_INDEX_FILE)
        with open(CHUNK_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.chunk_mapping, f, indent=4)
        print(f"Index saved to {FAISS_INDEX_FILE}")
        print(f"Mapping saved to {CHUNK_MAPPING_FILE}")

    def load_index(self):
        """Loads the pre-built index and mapping from disk for the live application."""
        if not os.path.exists(FAISS_INDEX_FILE) or not os.path.exists(CHUNK_MAPPING_FILE):
            raise FileNotFoundError("Index files not found. Run build_index() first.")
        
        self.index = faiss.read_index(FAISS_INDEX_FILE)
        with open(CHUNK_MAPPING_FILE, 'r', encoding='utf-8') as f:
            self.chunk_mapping = json.load(f)

    def search(
        self, 
        query: str, 
        top_k: int = 5, 
        similarity_threshold: float = 0.70,
        user_intent: Optional[str] = None
    ) -> List[Dict]:
        """
        Embeds a user query, searches the FAISS index, applies thresholding, 
        and optionally reranks based on user intent.
        """
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Must normalize the query vector for Cosine Similarity
        faiss.normalize_L2(query_embedding)
        
        similarities, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue
                
            sim_score = float(similarities[0][i])
            
            # 1. Similarity Threshold Filter
            if sim_score < similarity_threshold:
                continue
                
            # 2. Prevent Mutation Bugs using deepcopy
            chunk_data = copy.deepcopy(self.chunk_mapping[str(idx)])
            chunk_data["similarity_score"] = sim_score
            
            # 3. Intent-Aware Reranking (Boost score if intents match)
            if user_intent and chunk_data.get("intent") == user_intent:
                # Add a small algorithmic boost (e.g., 0.05) to push exact intent matches to the top
                chunk_data["reranked_score"] = min(1.0, sim_score + 0.05)
            else:
                chunk_data["reranked_score"] = sim_score
                
            results.append(chunk_data)
            
        # Sort final results by the reranked score in descending order
        results = sorted(results, key=lambda x: x["reranked_score"], reverse=True)
                
        return results

if __name__ == "__main__":
    store = HotelVectorStore()
    store.build_index()