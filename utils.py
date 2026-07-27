import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from config import METRICS, WORKERS


def cached(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def clock(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60:02d}s"
    return f"{seconds // 3600}h {seconds % 3600 // 60:02d}m"


class Progress:
    def __init__(self, total):
        self.total = total
        self.done = 0
        self.started = time.monotonic()
        self.lock = threading.Lock()

    def tick(self):
        with self.lock:
            self.done += 1
            elapsed = time.monotonic() - self.started
            pct = self.done / self.total * 100 if self.total else 100
            remaining = (elapsed / self.done) * (self.total - self.done)
            eta = "done" if self.done == self.total else f"eta {clock(remaining)}"
            return f"[{self.done}/{self.total} {pct:3.0f}% {eta}]"


def usage_of(reply):
    u = getattr(reply, "usage", None)
    if u is None:
        return {}
    details = getattr(u, "output_tokens_details", None)
    return {
        "input": getattr(u, "input_tokens", 0) or 0,
        "output": getattr(u, "output_tokens", 0) or 0,
        "reasoning": (getattr(details, "reasoning_tokens", 0) or 0) if details else 0,
    }


def metrics_path(stem):
    return os.path.join(METRICS, stem + ".json")


def metrics_has(stem, step):
    path = metrics_path(stem)
    if not cached(path):
        return False
    with open(path) as f:
        return step in json.load(f)


def record_usage(stem, step, usage):
    os.makedirs(METRICS, exist_ok=True)
    path = metrics_path(stem)
    data = {}
    if cached(path):
        with open(path) as f:
            data = json.load(f)
    data[step] = usage
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def run_pool(jobs, fn):
    with ThreadPoolExecutor(WORKERS) as pool:
        return list(pool.map(fn, jobs))
