import base64
import json
import os

from band_reader import band_text
from config import BANDS, CONSENSUS_MIN, CONSENSUS_MODELS, DRAFTS, OUTPUT_DIR
from utils import Progress, cached, metrics_has, record_usage, run_pool
from vote import vote


def consensus(only=None):
    stems = sorted(os.listdir(BANDS))
    if only:
        stems = [s for s in stems if s in set(only)]
    todo = [s for s in stems
            if not metrics_has(s, "consensus") and cached(os.path.join(DRAFTS, s + ".json"))]
    print(f"consensus: {len(todo)} to do, {len(stems) - len(todo)} cached", flush=True)
    if not todo:
        return

    jobs = [(stem, b) for stem in todo
            for b in sorted(os.listdir(os.path.join(BANDS, stem)))]
    n_extra = len(CONSENSUS_MODELS) - 1
    print(f"  {len(jobs)} bands x {n_extra} corroborating reads "
          f"({', '.join(CONSENSUS_MODELS[1:])})", flush=True)
    progress = Progress(len(jobs))

    def settle(job):
        stem, band = job
        with open(os.path.join(BANDS, stem, band), "rb") as f:
            image = base64.b64encode(f.read()).decode()
        with open(os.path.join(DRAFTS, stem + ".json")) as f:
            primary = next((l["text"] for l in json.load(f)["lines"]
                            if l["file"] == band), "")

        reads, usage = [primary], []
        for model in CONSENSUS_MODELS[1:]:
            text, u = band_text(image, vendor="anthropic", model=model)
            reads.append(text.strip())
            usage.append(u)

        text, kept, total = vote(reads, CONSENSUS_MIN)
        pct = round(kept / total * 100) if total else 0
        print(f"  {progress.tick()} {stem}/{band}: {kept}/{total} words corroborated ({pct}%)",
              flush=True)
        return stem, band, text, kept, total, usage

    done = run_pool(jobs, settle)

    os.makedirs(f"{OUTPUT_DIR}/drafts_single", exist_ok=True)
    for stem in todo:
        got = sorted((b, t) for s, b, t, _, _, _ in done if s == stem)

        src = os.path.join(DRAFTS, stem + ".json")
        with open(src) as f:
            single = f.read()
        with open(f"{OUTPUT_DIR}/drafts_single/{stem}.json", "w") as f:
            f.write(single)
        with open(src, "w") as f:
            json.dump({"lines": [{"file": b, "text": t} for b, t in got]},
                      f, ensure_ascii=False, indent=2)

        kept = sum(k for s, _, _, k, _, _ in done if s == stem)
        total = sum(t for s, _, _, _, t, _ in done if s == stem)
        tokens = sum(u.get("input", 0) + u.get("output", 0)
                     for s, _, _, _, _, us in done if s == stem for u in us)
        record_usage(stem, "consensus", {
            "corroborated": kept, "words": total,
            "corroborated_pct": round(kept / total * 100) if total else 0,
            "models": CONSENSUS_MODELS, "min_votes": CONSENSUS_MIN, "tokens": tokens})

    k = sum(k for _, _, _, k, _, _ in done)
    t = sum(t for _, _, _, _, t, _ in done)
    print(f"consensus: {len(done)} bands | {k}/{t} words corroborated "
          f"({round(k / t * 100) if t else 0}%)", flush=True)
