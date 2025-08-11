"""Embedding interfaces."""
from __future__ import annotations
from typing import List
import numpy as np
import hashlib
import os

class Embedder:
    def encode(self, texts: List[str]) -> np.ndarray:  # pragma: no cover - interface
        raise NotImplementedError

class HashEmbedder(Embedder):
    """Deterministic hash-based embeddings for tests."""
    def __init__(self, dim: int = 64):
        self.dim = dim

    def encode(self, texts: List[str]) -> np.ndarray:
        vecs = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            # repeat to fill dim
            arr = np.frombuffer(h, dtype=np.uint8).astype(float)
            if len(arr) < self.dim:
                arr = np.tile(arr, int(np.ceil(self.dim / len(arr))))
            vecs.append(arr[: self.dim])
        mat = np.vstack(vecs)
        # normalize
        norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9
        return mat / norms

class OpenAIEmbedder(Embedder):
    """Adapter for OpenAI embeddings API (not used in tests)."""
    def __init__(self, model: str = "text-embedding-3-large"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

    def encode(self, texts: List[str]) -> np.ndarray:  # pragma: no cover - network
        import requests, json
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"input": texts, "model": self.model}
        resp = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=data)
        resp.raise_for_status()
        emb = [d["embedding"] for d in resp.json()["data"]]
        return np.array(emb, dtype=float)
