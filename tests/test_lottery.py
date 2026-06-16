import pathlib
import random
import sys
from collections import Counter

import pandas as pd

APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from app import _weighted_sample_without_replacement  # noqa: E402

N_TRIALS = 1_000_000
TOLERANCE = 0.01


def test_single_draw_distribution_is_proportional_to_score():
    data = pd.read_excel(APP_DIR / "dummy_applicants.xlsx")
    names = data["Name"].tolist()
    weights = data["Score"].tolist()
    total_weight = sum(weights)

    random.seed(42)
    counts = Counter(
        _weighted_sample_without_replacement(names, weights, 1)[0]
        for _ in range(N_TRIALS)
    )

    for name, weight in zip(names, weights):
        expected_share = weight / total_weight
        observed_share = counts[name] / N_TRIALS
        assert abs(observed_share - expected_share) < TOLERANCE, (
            f"{name}: expected ~{expected_share:.4f}, observed {observed_share:.4f}"
        )
