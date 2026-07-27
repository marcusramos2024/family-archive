import os

import cv2
import numpy as np

from columns import columns_of
from config import BANDS, BAND_HEIGHT, BAND_UPSCALE, PREPROCESSED
from utils import Progress


def split():
    os.makedirs(BANDS, exist_ok=True)

    names = sorted(os.listdir(PREPROCESSED))
    todo = [n for n in names if not os.path.isdir(os.path.join(BANDS, os.path.splitext(n)[0]))]
    print(f"split: {len(todo)} to do, {len(names) - len(todo)} cached", flush=True)
    progress = Progress(len(todo))

    total = 0
    for name in todo:
        stem = os.path.splitext(name)[0]
        page = cv2.imread(os.path.join(PREPROCESSED, name), cv2.IMREAD_GRAYSCALE)

        page_dir = os.path.join(BANDS, stem)
        os.makedirs(page_dir, exist_ok=True)

        cols = columns_of(page)
        n = 0
        for c, (left, right) in enumerate(cols, 1):
            block = page[:, left:right]
            h = block.shape[0]
            bands = max(1, round(h / BAND_HEIGHT))

            ink = cv2.threshold(block, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            profile = (ink > 0).sum(axis=1).astype(np.float32).reshape(-1, 1)
            profile = cv2.GaussianBlur(profile, (1, 15), 0).ravel()

            cuts = [0]
            for k in range(1, bands):
                target = h * k // bands
                lo, hi = max(0, target - 60), min(h, target + 60)
                cuts.append(lo + int(np.argmin(profile[lo:hi])))
            cuts.append(h)

            for j, (top, bottom) in enumerate(zip(cuts, cuts[1:]), 1):
                band = block[top:bottom]
                if BAND_UPSCALE != 1:
                    band = cv2.resize(band, None, fx=BAND_UPSCALE, fy=BAND_UPSCALE,
                                      interpolation=cv2.INTER_CUBIC)
                cv2.imwrite(os.path.join(page_dir, f"c{c}_b{j:02d}.png"), band)
            n += bands

        total += n
        cols_note = f"{len(cols)} columns, " if len(cols) > 1 else ""
        print(f"  {progress.tick()} {name}: {cols_note}{n} bands", flush=True)

    print(f"split: {total} bands from {len(todo)} pages", flush=True)
