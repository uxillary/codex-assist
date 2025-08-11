from __future__ import annotations
import sqlite3
import json
import numpy as np
from typing import List
from .models import Turn, FSChunk, DecisionLedger
import yaml

class Store:
    def __init__(self, db_path: str = "context.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _init_db(self) -> None:
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS transcripts(
                    turn_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT, text TEXT, ts TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS fs_chunks(
                    id TEXT PRIMARY KEY,
                    type TEXT, tags TEXT, text TEXT, src_turn INTEGER, vec BLOB)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ledger(
                    id INTEGER PRIMARY KEY, yaml TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS meta(
                    key TEXT PRIMARY KEY, value TEXT)""")
        # ensure ledger row
        c.execute("INSERT OR IGNORE INTO ledger(id, yaml) VALUES(1, ?)" , (yaml.dump(DecisionLedger().model_dump()),))
        c.execute("INSERT OR IGNORE INTO meta(key, value) VALUES('ac', '[]')")
        self.conn.commit()

    # transcripts
    def append_turn(self, turn: Turn) -> int:
        c = self.conn.cursor()
        c.execute("INSERT INTO transcripts(role,text,ts) VALUES(?,?,?)", (turn.role, turn.text, turn.ts.isoformat()))
        self.conn.commit()
        return c.lastrowid

    def last_turns(self, n: int) -> List[Turn]:
        c = self.conn.cursor()
        rows = c.execute("SELECT role,text,ts FROM transcripts ORDER BY turn_id DESC LIMIT ?", (n,)).fetchall()
        rows.reverse()
        return [Turn(role=r[0], text=r[1], ts=r[2]) for r in rows]

    # ledger
    def load_ledger(self) -> DecisionLedger:
        c = self.conn.cursor()
        (yaml_txt,) = c.execute("SELECT yaml FROM ledger WHERE id=1").fetchone()
        data = yaml.safe_load(yaml_txt) or {}
        return DecisionLedger(**data)

    def save_ledger(self, dl: DecisionLedger) -> None:
        c = self.conn.cursor()
        c.execute("UPDATE ledger SET yaml=? WHERE id=1", (yaml.dump(dl.model_dump()),))
        self.conn.commit()

    # meta AC
    def load_ac(self) -> List[Turn]:
        c = self.conn.cursor()
        (txt,) = c.execute("SELECT value FROM meta WHERE key='ac'").fetchone()
        data = json.loads(txt)
        return [Turn(**t) for t in data]

    def save_ac(self, turns: List[Turn]) -> None:
        c = self.conn.cursor()
        serial = json.dumps([t.model_dump(mode="json") for t in turns])
        c.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('ac', ?)" , (serial,))
        self.conn.commit()

    # FS chunks
    def upsert_fs_chunk(self, chunk: FSChunk) -> None:
        vec_blob = None
        if chunk.vec is not None:
            vec_blob = chunk.vec.astype(np.float32).tobytes()
        tags_txt = ",".join(chunk.tags)
        c = self.conn.cursor()
        c.execute("REPLACE INTO fs_chunks(id,type,tags,text,src_turn,vec) VALUES(?,?,?,?,?,?)",
                  (chunk.id, chunk.type, tags_txt, chunk.text, chunk.src_turn, vec_blob))
        self.conn.commit()

    def load_fs_chunks(self) -> List[FSChunk]:
        c = self.conn.cursor()
        rows = c.execute("SELECT id,type,tags,text,src_turn,vec FROM fs_chunks").fetchall()
        chunks = []
        for r in rows:
            vec = None
            if r[5] is not None:
                arr = np.frombuffer(r[5], dtype=np.float32)
                vec = arr
            tags = r[2].split(',') if r[2] else []
            chunks.append(FSChunk(id=r[0], type=r[1], tags=tags, text=r[3], src_turn=r[4], vec=vec))
        return chunks

    def count_fs(self) -> int:
        c = self.conn.cursor()
        (n,) = c.execute("SELECT COUNT(*) FROM fs_chunks").fetchone()
        return n
