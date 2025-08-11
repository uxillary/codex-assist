import context_engine.reducers as R
import context_engine.tokens as T

def test_densify_and_condenser():
    existing = "- a\n- b"
    incoming = "- b\n- c"
    merged = R.densify(existing, incoming, max_tokens=20)
    assert "a" in merged and "b" in merged and "c" in merged
    chunks = ["word" * 10, "second chunk"]
    condensed = R.condenser(chunks, target_tokens=5)
    assert T.len_tokens(condensed) <= 5
    final = R.final_budget_cut(condensed + " more words", target_tokens=5)
    assert T.len_tokens(final) <= 5
