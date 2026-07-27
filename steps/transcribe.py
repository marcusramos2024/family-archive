import base64
import json
import os
import time

from band_reader import band_text
from config import BANDS, DRAFTS, GPT_MODEL, WORKERS
from scoring import coverage, score
from utils import Progress, cached, record_usage, run_pool


def transcribe(only=None):
    os.makedirs(DRAFTS, exist_ok=True)
    stems = sorted(os.listdir(BANDS))
    if only:
        stems = [s for s in stems if s in set(only)]
    todo = [s for s in stems if not cached(os.path.join(DRAFTS, s + ".json"))]
    print(f"transcribe: {len(todo)} to do, {len(stems) - len(todo)} cached", flush=True)
    if not todo:
        return

    jobs = [(stem, b) for stem in todo for b in sorted(os.listdir(os.path.join(BANDS, stem)))]
    print(f"  {len(jobs)} bands across {len(todo)} pages, {WORKERS} at a time", flush=True)
    progress = Progress(len(jobs))

    def read_band(job):
        stem, band = job
        path = os.path.join(BANDS, stem, band)
        with open(path, "rb") as f:
            image = base64.b64encode(f.read()).decode()

        started = time.monotonic()
        text, usage = band_text(image)

        text = text.strip()
        usage["seconds"] = round(time.monotonic() - started, 1)
        s = score(text)
        pct = coverage(s)
        print(f"  {progress.tick()} {stem}/{band}: {s.lines} lines, {pct}% read,"
              f" {s.lost} unreadable"
              f"  ({usage['seconds']:.0f}s, {usage.get('output', 0):,} out)", flush=True)
        return stem, band, text, usage

    done = run_pool(jobs, read_band)

    results = []
    for stem in todo:
        got = sorted((b, t, u) for s, b, t, u in done if s == stem)

        with open(os.path.join(DRAFTS, stem + ".json"), "w") as f:
            json.dump({"lines": [{"file": b, "text": t} for b, t, _ in got]},
                      f, ensure_ascii=False, indent=2)

        merged = {
            "input": sum(u.get("input", 0) for _, _, u in got),
            "output": sum(u.get("output", 0) for _, _, u in got),
            "reasoning": sum(u.get("reasoning", 0) for _, _, u in got),
            "seconds": round(sum(u.get("seconds", 0) for _, _, u in got), 1),
            "bands": len(got),
        }
        record_usage(stem, "transcribe", dict(merged, model=GPT_MODEL))
        results.append(merged)

    tin = sum(r["input"] for r in results)
    tout = sum(r["output"] for r in results)
    print(f"transcribe: {len(results)} pages done"
          f"  ({tin:,} in / {tout:,} out)", flush=True)
