import os
import time

from deep_translator import GoogleTranslator

from config import REVIEWED, TRANSLATED
from scoring import GUESS_RE, words
from utils import Progress, cached, record_usage


def translate():
    os.makedirs(TRANSLATED, exist_ok=True)
    translator = GoogleTranslator(source="de", target="en")

    names = sorted(os.listdir(REVIEWED))
    todo = [n for n in names if not cached(os.path.join(TRANSLATED, n))]
    print(f"translate: {len(todo)} to do, {len(names) - len(todo)} cached")
    progress = Progress(len(todo))

    done = 0
    for name in todo:
        started = time.monotonic()
        with open(os.path.join(REVIEWED, name)) as f:
            german = f.read().strip()

        german = GUESS_RE.sub(lambda m: m.group(0)[2:-2], german.replace("[[?]]", "[...]"))

        chunks, current = [], ""
        for line in german.split("\n"):
            if current and len(current) + len(line) > 4500:
                chunks.append(current)
                current = ""
            current += ("\n" if current else "") + line
        chunks.append(current)

        english = "\n".join(translator.translate(c) for c in chunks)

        with open(os.path.join(TRANSLATED, name), "w") as f:
            f.write(english + "\n")
        done += 1
        record_usage(os.path.splitext(name)[0], "translate",
                     {"words": words(english), "chunks": len(chunks),
                      "seconds": round(time.monotonic() - started, 1)})
        chunk_note = f", {len(chunks)} chunks" if len(chunks) > 1 else ""
        print(f"  {progress.tick()} {name}: {words(english):,} words{chunk_note}", flush=True)

    print(f"translate: {done} done")
