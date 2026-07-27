import base64
import json
import os
import time
from difflib import SequenceMatcher

from band_reader import band_text
from config import BANDS, CROSS_BANDS, CROSS_MODEL, DRAFTS, SECOND_OPINION
from scoring import confident_only, normalise
from utils import Progress, metrics_has, record_usage, run_pool


def cross_verify(only=None):
    stems = [os.path.splitext(n)[0] for n in sorted(os.listdir(DRAFTS))]
    if only:
        stems = [s for s in stems if s in set(only)]
    todo = [s for s in stems if not metrics_has(s, "cross_verify")]
    print(f"cross_verify: {len(todo)} to do, {len(stems) - len(todo)} cached", flush=True)
    if not todo:
        return

    jobs = []
    for stem in todo:
        with open(os.path.join(DRAFTS, stem + ".json")) as f:
            bands = json.load(f)["lines"]
        k = min(CROSS_BANDS, len(bands))
        picks = [bands[int((i + 0.5) * len(bands) / k)] for i in range(k)]
        jobs += [(stem, b["file"], b["text"]) for b in picks]

    print(f"  {len(jobs)} bands re-read by {CROSS_MODEL} across {len(todo)} pages", flush=True)
    progress = Progress(len(jobs))

    def reread(job):
        stem, band, gpt_text = job
        with open(os.path.join(BANDS, stem, band), "rb") as f:
            image = base64.b64encode(f.read()).decode()
        started = time.monotonic()
        claude_text, usage = band_text(image, vendor="anthropic", model=CROSS_MODEL)

        claude_text = claude_text.strip()
        seconds_dir = os.path.join(SECOND_OPINION, stem)
        os.makedirs(seconds_dir, exist_ok=True)
        with open(os.path.join(seconds_dir, band + ".txt"), "w") as f:
            f.write(claude_text + "\n")

        a, b = normalise(gpt_text), normalise(claude_text)
        agree = SequenceMatcher(None, a, b).ratio() if a and b else 0.0
        ca, cb = confident_only(gpt_text), confident_only(claude_text)
        agree_conf = SequenceMatcher(None, ca, cb).ratio() if ca and cb else 0.0
        print(f"  {progress.tick()} {stem}/{band}: {agree * 100:.0f}% all-words / "
              f"{agree_conf * 100:.0f}% confident-only agreement "
              f"({len(a)} vs {len(b)} words, {len(ca)} vs {len(cb)} confident, "
              f"{time.monotonic() - started:.0f}s)", flush=True)
        return stem, agree, agree_conf, usage

    done = run_pool(jobs, reread)

    for stem in todo:
        rows = [(a, c) for s, a, c, _ in done if s == stem]
        if not rows:
            continue
        tokens = sum(u.get("input", 0) + u.get("output", 0) for s, _, _, u in done if s == stem)
        record_usage(stem, "cross_verify", {
            "agreement": round(sum(a for a, _ in rows) / len(rows), 3),
            "agreement_confident": round(sum(c for _, c in rows) / len(rows), 3),
            "bands": len(rows), "tokens": tokens, "model": CROSS_MODEL})

    if done:
        allw = sum(a for _, a, _, _ in done) / len(done) * 100
        conf = sum(c for _, _, c, _ in done) / len(done) * 100
        print(f"cross_verify: {len(done)} bands | mean agreement {allw:.0f}% over all read words, "
              f"{conf:.0f}% over confident words only", flush=True)
