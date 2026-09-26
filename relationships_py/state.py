"""Durable, atomic local state; raw source caches are disposable."""
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import fcntl

ROOT = Path(__file__).resolve().parents[1]

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()

def stable_id(kind, *parts):
    return kind + '-' + digest(parts)[:24]

def read(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if path.exists() and path.read_text(encoding='utf-8') == raw:
        return False
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return True

@contextmanager
def lock(root=ROOT):
    path = Path(root) / '.cache/relationships/operation.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield

TABLES = ('companies', 'sources', 'evidence', 'relationships', 'events')

def load_master(root=ROOT):
    return {name: read(Path(root) / 'relationships_data' / (name + '.json'), []) for name in TABLES}

def save_master(master, root=ROOT):
    # Callers hold the operation lock; export never reads during mutation.
    for name in TABLES:
        write(Path(root) / 'relationships_data' / (name + '.json'), master[name])
