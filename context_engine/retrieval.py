"""Hybrid retrieval and MMR."""
from __future__ import annotations
from typing import List
import numpy as np
from rank_bm25 import BM25Okapi
from .models import DecisionLedger, FSChunk


def _tokenize(text: str) -> List[str]:
    return text.lower().split()

def hybrid_search(query: str, dl: DecisionLedger, fs_chunks: List[FSChunk], embedder, k: int = 8, mmr_lambda: float = 0.7) -> List[FSChunk]:
    if not fs_chunks:
        return []
    # build corpus
    corpus = [f"{c.text} {' '.join(c.tags)}" for c in fs_chunks]
    tokenized_corpus = [_tokenize(c) for c in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    q_extra = " ".join(list(dl.ids.values()) + dl.decisions + dl.todos + dl.constraints)
    full_query = f"{query} {q_extra}".strip()
    bm25_scores = bm25.get_scores(_tokenize(full_query))
    # embeddings
    texts = [c.text for c in fs_chunks]
    chunk_vecs = np.vstack([c.vec for c in fs_chunks]) if fs_chunks[0].vec is not None else embedder.encode(texts)
    for c, v in zip(fs_chunks, chunk_vecs):
        c.vec = v
    q_vec = embedder.encode([full_query])[0]
    cos_scores = chunk_vecs @ q_vec
    # ranks
    bm25_rank = np.argsort(np.argsort(-bm25_scores))
    cos_rank = np.argsort(np.argsort(-cos_scores))
    rrf = 1/(60 + bm25_rank) + 1/(60 + cos_rank)
    order = np.argsort(-rrf)
    # apply MMR
    selected = []
    selected_vecs = []
    for idx in order:
        candidate = fs_chunks[idx]
        cand_vec = chunk_vecs[idx]
        if not selected:
            selected.append(candidate)
            selected_vecs.append(cand_vec)
        else:
            sims = [cand_vec @ v for v in selected_vecs]
            max_sim = max(sims)
            mmr_score = mmr_lambda * (cand_vec @ q_vec) - (1 - mmr_lambda) * max_sim
            if mmr_score <= 0:
                continue
            selected.append(candidate)
            selected_vecs.append(cand_vec)
        if len(selected) >= k:
            break
    return selected
