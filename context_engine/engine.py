"""High level Context Engine implementation."""
from __future__ import annotations
import uuid
from .store import Store
from .embeddings import HashEmbedder, Embedder
from .models import Turn, DecisionLedger, FSChunk
from . import extractors
from . import reducers
from . import retrieval
from .tokens import len_tokens, cap_to_tokens
import yaml

class ContextEngine:
    def __init__(self, db_path: str = "context.db", index_dir: str = "indexes", embedder: Embedder = None,
                 ac_pairs:int=2, dl_cap_tokens:int=250, es_tokens:int=120, budget_tokens:int=900):
        self.store = Store(db_path)
        self.embedder = embedder or HashEmbedder()
        self.ac_pairs = ac_pairs
        self.dl_cap_tokens = dl_cap_tokens
        self.es_tokens = es_tokens
        self.budget_tokens = budget_tokens

    # -------- Update phase ---------
    def update_memory(self, user_msg: str, assistant_msg: str) -> None:
        # append raw turns
        user_turn = Turn(role="user", text=user_msg)
        assistant_turn = Turn(role="assistant", text=assistant_msg)
        self.store.append_turn(user_turn)
        turn_id = self.store.append_turn(assistant_turn)
        # update AC
        ac = self.store.load_ac()
        ac.extend([user_turn, assistant_turn])
        ac = ac[-self.ac_pairs*2:]
        self.store.save_ac(ac)
        # decision ledger
        dl = self.store.load_ledger()
        delta_user = extractors.extract_dl_signals(user_msg)
        delta_assistant = extractors.extract_dl_signals(assistant_msg)
        for field in ["decisions","constraints","todos","prefs"]:
            setattr(dl, field, getattr(dl, field) + getattr(delta_user, field) + getattr(delta_assistant, field))
        dl.ids.update(delta_user.ids)
        dl.ids.update(delta_assistant.ids)
        # cap DL tokens by trimming lists
        def dl_tokens(d: DecisionLedger) -> int:
            return len_tokens(yaml.dump(d.model_dump()))
        while dl_tokens(dl) > self.dl_cap_tokens:
            trimmed = False
            for field in ["decisions","constraints","todos","prefs"]:
                lst = getattr(dl, field)
                if lst:
                    lst.pop(0)
                    trimmed = True
                    if dl_tokens(dl) <= self.dl_cap_tokens:
                        break
            if not trimmed:
                break
        self.store.save_ledger(dl)
        # summaries
        ext = extractors.make_extractive(user_msg, assistant_msg, self.es_tokens)
        abs_s = extractors.make_abstractive(user_msg, assistant_msg, self.es_tokens)
        vecs = self.embedder.encode([ext, abs_s])
        fs_chunks = self.store.load_fs_chunks()
        for text, typ, vec in zip([ext, abs_s], ["extractive","abstractive"], vecs):
            new_chunk = FSChunk(id=str(uuid.uuid4()), type=typ, tags=[], text=text, src_turn=turn_id, vec=vec)
            duplicate = None
            for ch in fs_chunks:
                if ch.vec is None:
                    continue
                sim = float(ch.vec @ vec)
                if sim > 0.9:
                    duplicate = ch
                    break
            if duplicate:
                merged = reducers.densify(duplicate.text, text, self.es_tokens)
                duplicate.text = merged
                duplicate.vec = (duplicate.vec + vec) / 2
                self.store.upsert_fs_chunk(duplicate)
            else:
                self.store.upsert_fs_chunk(new_chunk)
                fs_chunks.append(new_chunk)

    # -------- Compose phase ---------
    def compose_context(self, next_user_msg: str) -> str:
        ac = self.store.load_ac()
        ac_text_lines = [f"{t.role}: {t.text}" for t in ac]
        ac_text = "\n".join(ac_text_lines)
        ac_text = cap_to_tokens(ac_text, 400)
        dl = self.store.load_ledger()
        dl_yaml = yaml.dump(dl.model_dump())
        dl_yaml = cap_to_tokens(dl_yaml, self.dl_cap_tokens)
        base = ac_text + "\n" + dl_yaml
        used = len_tokens(base)
        remaining = max(0, self.budget_tokens - used)
        fs_chunks = self.store.load_fs_chunks()
        retrieved = retrieval.hybrid_search(next_user_msg, dl, fs_chunks, self.embedder, k=5)
        snippets = [c.text for c in retrieved]
        cond = reducers.condenser(snippets, remaining)
        context = base + "\n" + cond
        if len_tokens(context) > self.budget_tokens:
            context = reducers.final_budget_cut(context, self.budget_tokens)
        return context

    def stats(self) -> dict:
        ac = self.store.load_ac()
        dl = self.store.load_ledger()
        fs_count = self.store.count_fs()
        return {
            "ac_pairs": len(ac)//2,
            "dl_tokens": len_tokens(yaml.dump(dl.model_dump())),
            "fs_chunks": fs_count,
        }
