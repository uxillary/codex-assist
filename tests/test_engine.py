from context_engine.engine import ContextEngine
from context_engine.embeddings import HashEmbedder
from context_engine.tokens import len_tokens


def test_engine_update_and_compose(tmp_path):
    db = tmp_path / "ctx.db"
    eng = ContextEngine(db_path=str(db), embedder=HashEmbedder(), dl_cap_tokens=50, budget_tokens=200, es_tokens=40)
    eng.update_memory("decide: use Astro\nWe chose Astro; add loader", "Done; todo: add confetti")
    eng.update_memory("decide: use Astro\nWe chose Astro; add loader", "Done; todo: add confetti")
    stats = eng.stats()
    assert stats["dl_tokens"] <= 50
    # AC window size
    ac = eng.store.load_ac()
    assert len(ac) == 4
    # FS dedupe -> only two chunks
    fs_chunks = eng.store.load_fs_chunks()
    assert len(fs_chunks) == 2
    # compose context under budget
    ctx = eng.compose_context("Improve loader feedback")
    assert len_tokens(ctx) <= 200
