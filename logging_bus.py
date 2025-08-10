import queue, threading, time, json
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Any, List, Optional


@dataclass
class LogEvent:
    ts: float
    level: str   # "INFO","WARN","ERROR"
    kind: str    # "BUILD","NETWORK","STREAM","COST","SYSTEM"
    msg: str
    meta: Dict[str, Any]


_listeners: List[Callable[["LogEvent"], None]] = []
_q: "queue.Queue[LogEvent]" = queue.Queue()
_verbose = True
_level_filter: Dict[str, bool] = {"INFO": True, "WARN": True, "ERROR": True}
_kind_filter: Dict[str, bool] = {
    "BUILD": True,
    "NETWORK": True,
    "STREAM": True,
    "COST": True,
    "SYSTEM": True,
}
_ring: List[LogEvent] = []
_ring_limit = 2000

_file_path: Optional[str] = None
_file_q: "queue.Queue[LogEvent]" = queue.Queue()


def emit(level: str, kind: str, msg: str, **meta: Any) -> None:
    if level not in _level_filter:
        _level_filter[level] = True
    if kind not in _kind_filter:
        _kind_filter[kind] = True
    if not _level_filter.get(level, True):
        return
    if not _kind_filter.get(kind, True):
        return
    if not _verbose and level == "INFO" and kind != "SYSTEM":
        return
    evt = LogEvent(time.time(), level, kind, msg, meta)
    _q.put(evt)


def subscribe(callback: Callable[[LogEvent], None]) -> None:
    _listeners.append(callback)


def start_dispatcher() -> None:
    def loop() -> None:
        while True:
            evt = _q.get()
            _ring.append(evt)
            if len(_ring) > _ring_limit:
                del _ring[0 : len(_ring) - _ring_limit]
            for cb in list(_listeners):
                try:
                    cb(evt)
                except Exception:
                    pass
            if _file_path:
                _file_q.put(evt)

    threading.Thread(target=loop, daemon=True).start()

    def file_loop() -> None:
        fp = None
        while True:
            evt = _file_q.get()
            try:
                if _file_path:
                    if fp is None:
                        fp = open(_file_path, "a", encoding="utf-8")
                    fp.write(json.dumps(asdict(evt), ensure_ascii=False) + "\n")
                    fp.flush()
                else:
                    if fp:
                        fp.close()
                        fp = None
            except Exception:
                pass

    threading.Thread(target=file_loop, daemon=True).start()


def set_verbose(v: bool) -> None:
    global _verbose
    _verbose = v


def get_verbose() -> bool:
    return _verbose


def set_log_level_filter(levels: Dict[str, bool]) -> None:
    _level_filter.update(levels)


def set_kind_filter(kinds: Dict[str, bool]) -> None:
    _kind_filter.update(kinds)


def set_ring_limit(n: int) -> None:
    global _ring_limit
    _ring_limit = max(200, int(n))


def set_file_logger(path: Optional[str]) -> None:
    global _file_path
    _file_path = path


def snapshot() -> List[LogEvent]:
    return list(_ring)
