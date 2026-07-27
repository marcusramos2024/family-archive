import cv2
import numpy as np


def columns_of(page):
    ink = cv2.threshold(page, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    profile = (ink > 0).sum(axis=0).astype(np.float32).reshape(1, -1)
    profile = cv2.GaussianBlur(profile, (31, 1), 0).ravel()
    w = len(profile)

    quiet = profile < np.median(profile) * 0.5
    edges = np.diff(np.pad(quiet.astype(np.int8), 1))
    runs = zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))
    gutters = [(a, b) for a, b in runs
               if b - a > w * 0.015 and w * 0.15 < (a + b) / 2 < w * 0.85]

    if not gutters:
        return [(0, w)]
    cuts = [0] + [(a + b) // 2 for a, b in gutters] + [w]
    return [(a, b) for a, b in zip(cuts, cuts[1:]) if b - a > w * 0.1]
