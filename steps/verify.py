import base64
import json
import os
from difflib import SequenceMatcher

from openai import OpenAI

from config import BANDS, DRAFTS, GPT_MODEL, GPT_REASONING, TRANSCRIBE_TIMEOUT, VERIFY_BANDS
from prompts import TRANSCRIBE_PROMPT
from scoring import normalise
from utils import Progress, metrics_has, record_usage, run_pool, usage_of


def verify():
    client = OpenAI(timeout=TRANSCRIBE_TIMEOUT, max_retries=1)

    stems = [os.path.splitext(n)[0] for n in sorted(os.listdir(DRAFTS))]
    todo = [s for s in stems if not metrics_has(s, "verify")]
    print(f"verify: {len(todo)} to do, {len(stems) - len(todo)} cached", flush=True)
    if not todo:
        return

    jobs = []
    for stem in todo:
        with open(os.path.join(DRAFTS, stem + ".json")) as f:
            bands = json.load(f)["lines"]
        k = min(VERIFY_BANDS, len(bands))
        picks = [bands[int((i + 0.5) * len(bands) / k)] for i in range(k)]
        jobs += [(stem, b["file"], b["text"]) for b in picks]

    print(f"  re-reading {len(jobs)} bands across {len(todo)} pages", flush=True)
    progress = Progress(len(jobs))

    def reread(job):
        stem, band, original = job
        with open(os.path.join(BANDS, stem, band), "rb") as f:
            image = base64.b64encode(f.read()).decode()
        reply = client.responses.create(
            model=GPT_MODEL, reasoning=GPT_REASONING,
            input=[{"role": "user", "content": [
                {"type": "input_text", "text": TRANSCRIBE_PROMPT},
                {"type": "input_image", "image_url": f"data:image/png;base64,{image}"},
            ]}],
        )

        a, b = normalise(original), normalise(reply.output_text)
        agree = SequenceMatcher(None, a, b).ratio() if a and b else 0.0
        usage = usage_of(reply)
        print(f"  {progress.tick()} {stem}/{band}: {agree * 100:.0f}% agreement "
              f"({len(a)} vs {len(b)} words, {usage.get('output', 0):,} out)", flush=True)
        return stem, agree, usage

    done = run_pool(jobs, reread)

    for stem in todo:
        scores = [a for s, a, _ in done if s == stem]
        if not scores:
            continue
        tokens = sum(u.get("input", 0) + u.get("output", 0) for s, _, u in done if s == stem)
        record_usage(stem, "verify", {"agreement": round(sum(scores) / len(scores), 3),
                                      "bands": len(scores), "tokens": tokens})

    overall = [a for _, a, _ in done]
    print(f"verify: {len(done)} bands re-read, mean agreement "
          f"{sum(overall) / len(overall) * 100:.0f}%" if overall else "verify: nothing re-read",
          flush=True)
