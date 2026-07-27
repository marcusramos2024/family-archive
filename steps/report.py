import json
import os

from config import DRAFTS, METRICS, REVIEWED, TRANSLATED, VERIFY_AGREE, VERIFY_BANDS
from scoring import breakdown, coverage, score, words
from utils import cached


def report():
    def read(path):
        with open(path) as f:
            return f.read()

    rows = []
    for name in sorted(os.listdir(DRAFTS)):
        stem = os.path.splitext(name)[0]
        with open(os.path.join(DRAFTS, name)) as f:
            draft = score("\n".join(l["text"] for l in json.load(f)["lines"]))

        reviewed_path = os.path.join(REVIEWED, stem + ".txt")
        final = score(read(reviewed_path)) if cached(reviewed_path) else draft
        pending = not cached(reviewed_path)

        english_path = os.path.join(TRANSLATED, stem + ".txt")
        english = read(english_path) if cached(english_path) else ""

        usage = {}
        page_metrics_path = os.path.join(METRICS, stem + ".json")
        if cached(page_metrics_path):
            usage = json.loads(read(page_metrics_path))
        tr, rv = usage.get("transcribe", {}), usage.get("review", {})
        tl, vf = usage.get("translate", {}), usage.get("verify", {})

        cert_pct, unsure_pct, none_pct = breakdown(final)
        rows.append({
            "document": stem + ("*" if pending else ""),
            "lines": final.lines,
            "full": final.solid,
            "partial": final.lines - final.solid - final.lost,
            "none": final.lost,
            "read": final.read,
            "missing": final.missing,
            "guesses": final.guesses,
            "certain": final.certain,
            "unsure": final.unsure,
            "cert_pct": cert_pct,
            "unsure_pct": unsure_pct,
            "none_pct": none_pct,
            "agree": round(vf.get("agreement", 0) * 100) if vf else None,
            "pct": coverage(final),
            "draft_pct": coverage(draft),
            "kept_draft": rv.get("kept_draft", False),
            "words": words(english) if english else 0,
            "gpt": (tr.get("input", 0) or 0) + (tr.get("output", 0) or 0),
            "claude": (rv.get("input", 0) or 0) + (rv.get("output", 0) or 0),
            "t_sec": tr.get("seconds", 0) or 0,
            "r_sec": rv.get("seconds", 0) or 0,
            "x_sec": tl.get("seconds", 0) or 0,
        })

    if not rows:
        print("report: nothing to report")
        return

    rows.sort(key=lambda r: r["pct"])

    def bar(pct, width=10):
        filled = round(pct / 100 * width)
        return "█" * filled + "░" * (width - filled)

    def tok(n):
        return f"{n / 1000:.1f}k" if n >= 1000 else (str(n) if n else "-")

    wide = max(len(r["document"]) for r in rows + [{"document": "document"}])
    head = (f"     {'document':<{wide}}  {'TRANSCRIBE':<18} {'REVIEW':<20} {'TRANSLATE':<12}"
            f" {'extracted':<16} {'confident/unsure/none':<22} {'agree':>6} {'tokens':>8}")
    rule = "  " + "─" * (len(head) - 2)

    print(f"\nreport: {len(rows)} documents, least transcribed first")
    print(head)
    print(rule)
    for r in rows:
        step_t = f"{r['lines']}L {r['draft_pct']}% {r['t_sec']:.0f}s"
        move = r["pct"] - r["draft_pct"]
        flag = " kept-draft" if r["kept_draft"] else ""
        step_r = f"{r['pct']}% ({move:+d}) {r['r_sec']:.0f}s{flag}"
        step_x = f"{r['words']:,}w {r['x_sec']:.0f}s" if r["words"] else "-"
        meter = f"{bar(r['pct'])} {r['pct']:>3}%"
        certainty = f"{r['cert_pct']:>3}/{r['unsure_pct']:>3}/{r['none_pct']:>3}%"
        agree = f"{r['agree']}%" if r["agree"] is not None else "-"
        hit = "OK " if r["pct"] >= 90 and (r["agree"] or 0) >= VERIFY_AGREE else "   "
        print(f"  {hit}{r['document']:<{wide}}  {step_t:<18} {step_r:<20} {step_x:<12}"
              f" {meter:<16} {certainty:<22} {agree:>6} {tok(r['gpt'] + r['claude']):>8}")
    print(rule)

    read_total = sum(r["read"] for r in rows)
    missing = sum(r["missing"] for r in rows)
    certain = sum(r["certain"] for r in rows)
    unsure = sum(r["unsure"] for r in rows)
    total = read_total + missing
    hitting = sum(1 for r in rows if r["pct"] >= 90 and (r["agree"] or 0) >= VERIFY_AGREE)
    cert_pct_all = round(certain / total * 100) if total else 0
    unsure_pct_all = round(unsure / total * 100) if total else 0
    none_pct_all = 100 - cert_pct_all - unsure_pct_all if total else 0
    print(f"  {len(rows)} docs, {total:,} German words:")
    print(f"    extracted (read at all, confident or not):  {round(read_total / total * 100) if total else 0}%"
          f"  ({read_total:,} words)")
    print(f"    confident (clean reading, no markers):      {cert_pct_all}%  ({certain:,} words)")
    print(f"    not confident (marked [[unsure]]):          {unsure_pct_all}%  ({unsure:,} words)")
    print(f"    not confident at all ([[?]]):                {none_pct_all}%  ({missing:,} words)"
          f"   <- confident + unsure + this = 100%")
    print(f"  GOAL 4/5 docs at >=90% coverage AND >={VERIFY_AGREE}% agreement:  "
          f"{hitting}/{len(rows)} documents"
          f"   |   {sum(r['words'] for r in rows):,} English words out")
    print(f"  time: transcribe {sum(r['t_sec'] for r in rows):.0f}s, "
          f"review {sum(r['r_sec'] for r in rows):.0f}s, translate {sum(r['x_sec'] for r in rows):.0f}s"
          f"   |   tokens: {tok(sum(r['gpt'] for r in rows))} gpt + "
          f"{tok(sum(r['claude'] for r in rows))} claude")
    print("  extracted = share of words transcribed (certain or [[unsure]]) vs lost to [[?]]")
    print("  confident/unsure/none = per-document breakdown of the same three buckets, always summing to 100%")
    sampled = f"{VERIFY_BANDS} sampled band" + ("s" if VERIFY_BANDS != 1 else "")
    print(f"  agree = word overlap between two independent reads of {sampled} per page;"
          " a fabricated reading does not reproduce")
    if any(r["document"].endswith("*") for r in rows):
        print("  * review has not run on this document yet")
