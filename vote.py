from difflib import SequenceMatcher

from scoring import PUNCT


def _key(tokens):
    return [t.strip(PUNCT).lower().replace("[[", "").replace("]]", "") for t in tokens]


def vote(reads, min_votes):
    primary = reads[0]
    lines = primary.split("\n")
    tokens, line_of = [], []
    for i, line in enumerate(lines):
        for t in line.split():
            tokens.append(t)
            line_of.append(i)
    key = _key(tokens)

    votes = [0] * len(tokens)
    for other in reads[1:]:
        okey = _key(other.split())
        for block in SequenceMatcher(None, key, okey).get_matching_blocks():
            for i in range(block.a, block.a + block.size):
                votes[i] += 1

    out, kept, total = [[] for _ in lines], 0, 0
    for tok, v, li in zip(tokens, votes, line_of):
        bare = tok.replace("[[", "").replace("]]", "")
        if bare.strip(PUNCT).lower() in ("", "?"):
            out[li].append(tok)
            continue
        total += 1
        if v >= min_votes - 1:
            out[li].append(bare)
            kept += 1
        else:
            out[li].append(f"[[{bare}]]")
    return "\n".join(" ".join(l) for l in out), kept, total
