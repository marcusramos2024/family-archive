import re
from collections import namedtuple

GUESS_RE = re.compile(r"\[\[(?!\?\]\])[^\]]+\]\]")
PUNCT = ".,;:!?\"'()-–—"

Score = namedtuple("Score", "lines lost unknowns guesses solid read missing certain unsure")


def text_lines(text):
    return [l for l in text.split("\n") if l.strip()]


def score(text):
    lines = text_lines(text)
    missing = text.count("[[?]]")
    guesses = GUESS_RE.findall(text)
    certain = len(GUESS_RE.sub(" ", text.replace("[[?]]", " ")).split())
    unsure = sum(len(m.split()) for m in guesses)
    return Score(
        lines=len(lines),
        lost=sum(1 for l in lines if l.strip() == "[[?]]"),
        solid=sum(1 for l in lines if "[[" not in l),
        unknowns=missing,
        guesses=len(guesses),
        read=certain + unsure,
        missing=missing,
        certain=certain,
        unsure=unsure,
    )


def coverage(s):
    total = s.read + s.missing
    return round(s.read / total * 100) if total else 0


def breakdown(s):
    total = s.read + s.missing
    if not total:
        return 0, 0, 0
    certain_pct = round(s.certain / total * 100)
    unsure_pct = round(s.unsure / total * 100)
    return certain_pct, unsure_pct, 100 - certain_pct - unsure_pct


def words(text):
    return len(text.replace("[[?]]", " ").replace("[[", "").replace("]]", "").split())


def confident_only(text):
    stripped = GUESS_RE.sub(" ", text.replace("[[?]]", " "))
    return [w for w in (t.strip(PUNCT).lower() for t in stripped.split()) if w]


def normalise(text):
    text = text.replace("[[?]]", " ").replace("[[", "").replace("]]", "")
    return [w for w in (t.strip(PUNCT).lower() for t in text.split()) if w]
