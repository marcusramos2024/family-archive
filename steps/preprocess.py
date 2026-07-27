import os

import cv2
import numpy as np

from config import DATASET_DIR, PREPROCESSED
from utils import Progress, cached


def preprocess():
    os.makedirs(PREPROCESSED, exist_ok=True)

    names = sorted(os.listdir(DATASET_DIR))
    todo = [n for n in names if not cached(os.path.join(PREPROCESSED, os.path.splitext(n)[0] + ".png"))]
    print(f"preprocess: {len(todo)} to do, {len(names) - len(todo)} cached")
    progress = Progress(len(todo))

    done = 0
    for name in todo:
        img = cv2.imread(os.path.join(DATASET_DIR, name))

        gray = max(cv2.split(img), key=lambda c: np.percentile(c, 95) - np.percentile(c, 5))

        bg = cv2.GaussianBlur(gray, (0, 0), sigmaX=gray.shape[1] / 20)
        flat = cv2.divide(gray, bg, scale=255)

        small = cv2.resize(flat, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
        mask = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(mask > 0))
        if len(coords) > 100:
            angle = cv2.minAreaRect(coords)[-1]
            if angle > 45:
                angle -= 90
            if 0.5 < abs(angle) < 15:
                h, w = flat.shape
                m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
                flat = cv2.warpAffine(
                    flat, m, (w, h), flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_CONSTANT, borderValue=255,
                )

        lo, hi = np.percentile(flat, 2), np.percentile(flat, 98)
        if hi > lo:
            flat = np.clip((flat.astype(np.float32) - lo) * (255.0 / (hi - lo)), 0, 255).astype("uint8")

        cleaned = cv2.bilateralFilter(flat, 5, 50, 50)

        cv2.imwrite(os.path.join(PREPROCESSED, os.path.splitext(name)[0] + ".png"), cleaned)
        done += 1
        print(f"  {progress.tick()} {name}: done", flush=True)

    print(f"preprocess: {done} done")
    return done
