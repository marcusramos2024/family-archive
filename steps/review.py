import base64
import json
import os
import time

import anthropic

from config import CLAUDE_MODEL, DRAFTS, PREPROCESSED, REVIEWED
from prompts import REVIEW_PROMPT
from scoring import coverage, score
from utils import Progress, cached, record_usage, run_pool, usage_of


def review_transcription():
    os.makedirs(REVIEWED, exist_ok=True)
    client = anthropic.Anthropic()

    stems = [os.path.splitext(n)[0] for n in sorted(os.listdir(DRAFTS))]
    todo = [s for s in stems if not cached(os.path.join(REVIEWED, s + ".txt"))]
    print(f"review: {len(todo)} to do, {len(stems) - len(todo)} cached")
    if not todo:
        return
    progress = Progress(len(todo))

    def review(stem):
        with open(os.path.join(DRAFTS, stem + ".json")) as f:
            draft = "\n".join(line["text"] for line in json.load(f)["lines"])
        with open(os.path.join(PREPROCESSED, stem + ".png"), "rb") as f:
            page = base64.b64encode(f.read()).decode()

        started = time.monotonic()
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=32000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": "image/png", "data": page,
                }},
                {"type": "text", "text": REVIEW_PROMPT + draft},
            ]}],
        ) as stream:
            reply = stream.get_final_message()

        corrected = "".join(b.text for b in reply.content if b.type == "text").strip()

        before, after = score(draft), score(corrected)
        if after.guesses < before.guesses and after.unknowns >= before.unknowns:
            corrected = draft
            note = f"kept draft (review dropped {before.guesses - after.guesses} readings)"
        else:
            note = "done"

        with open(os.path.join(REVIEWED, stem + ".txt"), "w") as f:
            f.write(corrected + "\n")

        usage = usage_of(reply)
        usage["seconds"] = round(time.monotonic() - started, 1)
        usage["kept_draft"] = note.startswith("kept draft")
        record_usage(stem, "review", dict(usage, model=CLAUDE_MODEL))
        final = score(corrected)
        print(f"  {progress.tick()} {stem}: {note}, {coverage(final)}% read,"
              f" {final.lost} unreadable"
              f"  ({time.monotonic() - started:.0f}s, {usage.get('input', 0):,} in"
              f" / {usage.get('output', 0):,} out)", flush=True)
        return usage

    done = run_pool(todo, review)

    tin = sum(r.get("input", 0) for r in done)
    tout = sum(r.get("output", 0) for r in done)
    print(f"review: {len(done)} done"
          f"  ({tin:,} in / {tout:,} out)")
