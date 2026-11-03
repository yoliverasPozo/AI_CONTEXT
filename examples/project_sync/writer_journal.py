"""Exclusive local operation journals. No remote I/O or automatic lock recovery."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path

MAX_BYTES = 32 * 1024 * 1024


class JournalError(ValueError):
    """Receipt integrity or exclusive ownership could not be established."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("utf-8")


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


class Journal:
    def __init__(self, path):
        self.path = Path(path)

    @classmethod
    def create(cls, path, proposal):
        obj = cls(path)
        obj.path.mkdir(mode=0o700)  # Refuse reuse, including an empty directory.
        with obj.lock():
            obj.append("prepared", {"proposal": proposal})
        return obj

    @classmethod
    def open(cls, path):
        obj = cls(path)
        obj.events()
        return obj

    @contextmanager
    def lock(self):
        path = self.path / "active.lock"
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise JournalError("operation locked; no automatic stale-lock removal") from None
        try:
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            os.fsync(descriptor)
            yield
        finally:
            os.close(descriptor)
            path.unlink()

    def events(self):
        path = self.path / "journal.jsonl"
        if not path.exists():
            raise JournalError("operation journal missing")
        if path.stat().st_size > MAX_BYTES:
            raise JournalError("operation journal exceeds bound")
        events, previous = [], "0" * 64
        try:
            for line in path.read_bytes().splitlines(keepends=True):
                if not line.endswith(b"\n"):
                    raise JournalError("incomplete operation journal")
                event = json.loads(line)
                body = {key: event[key] for key in ("index", "previous", "kind", "data")}
                if (event["index"] != len(events) or event["previous"] != previous
                        or sha(body) != event["sha256"]):
                    raise JournalError("operation journal integrity mismatch")
                previous = event["sha256"]
                events.append(event)
        except (ValueError, KeyError, TypeError):
            raise JournalError("invalid operation journal") from None
        if not events or events[0]["kind"] != "prepared":
            raise JournalError("prepared receipt missing")
        return events

    def append(self, kind, data):
        # Caller holds the operation lock; reopening and checking the entire
        # bounded chain avoids trusting stale process-local receipt state.
        path = self.path / "journal.jsonl"
        events = self.events() if path.exists() else []
        if not events and kind != "prepared":
            raise JournalError("prepared receipt required")
        body = {"index": len(events), "previous": events[-1]["sha256"] if events else "0" * 64,
                "kind": kind, "data": data}
        record = canonical(dict(body, sha256=sha(body))) + b"\n"
        if (path.stat().st_size if path.exists() else 0) + len(record) > MAX_BYTES:
            raise JournalError("operation journal capacity reached; existing receipts preserved")
        with path.open("ab", buffering=0) as stream:
            if stream.write(record) != len(record):
                raise JournalError("incomplete journal write")
            os.fsync(stream.fileno())
