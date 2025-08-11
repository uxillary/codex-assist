from context_engine.embeddings import HashEmbedder
from context_engine.models import FSChunk, DecisionLedger
from context_engine import retrieval


def make_chunk(id, text):
    emb = HashEmbedder().encode([text])[0]
    return FSChunk(id=id, type="extractive", tags=[], text=text, src_turn=0, vec=emb)

def test_hybrid_search_mmr():
    chunks = [
        make_chunk("1", "Use Astro for the new site"),
        make_chunk("2", "Add loader with progress bar"),
        make_chunk("3", "Fix authentication bug"),
    ]
    dl = DecisionLedger()
    embed = HashEmbedder()
    res = retrieval.hybrid_search("Astro loader", dl, chunks, embedder=embed, k=2)
    assert len(res) == 2
    ids = {c.id for c in res}
    assert ids <= {"1", "2", "3"}
