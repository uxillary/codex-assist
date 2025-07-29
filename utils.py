import hashlib


def approx_tokens(text: str) -> int:
    """Rough token estimator (1 token ~4 chars)."""
    return max(1, len(text) // 4)


def file_hash(path: str) -> str:
    """Return md5 hash of a file's contents."""
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

