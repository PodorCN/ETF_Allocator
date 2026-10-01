import os
import pickle
import re

import pandas as pd

# Saved results of the slow calculations, so the app can load them instead of
# recomputing. precompute.py writes them all; cached() also saves anything it
# had to compute. Delete cache/results/ (or re-run precompute.py) to refresh.

DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "results")


def _path(name: str) -> str:
    return os.path.join(DIR, re.sub(r"[^A-Za-z0-9_.-]+", "_", name) + ".pkl")


def save(name: str, obj) -> None:
    os.makedirs(DIR, exist_ok=True)
    with open(_path(name), "wb") as f:
        pickle.dump({"computed_at": pd.Timestamp.now(), "result": obj}, f)


def load(name: str):
    """The saved result, or None if there is none (or it can't be read)."""
    try:
        with open(_path(name), "rb") as f:
            return pickle.load(f)["result"]
    except Exception:
        return None


def computed_at(name: str) -> pd.Timestamp | None:
    try:
        with open(_path(name), "rb") as f:
            return pickle.load(f)["computed_at"]
    except Exception:
        return None


def cached(name: str, compute):
    """Load the saved result `name`; if there is none, compute it and save it."""
    result = load(name)
    if result is None:
        result = compute()
        save(name, result)
    return result
