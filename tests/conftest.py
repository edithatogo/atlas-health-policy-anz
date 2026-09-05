"""Deterministic Hypothesis settings shared by every governed pytest lane."""

import os
from datetime import timedelta

from hypothesis import settings

settings.register_profile(
    "ci",
    max_examples=200,
    deadline=timedelta(milliseconds=500),
    derandomize=True,
    database=None,
    print_blob=True,
)
settings.register_profile(
    "stress",
    max_examples=1000,
    deadline=timedelta(seconds=1),
    derandomize=True,
    database=None,
    print_blob=True,
)
settings.load_profile(os.environ.get("ATLAS_HYPOTHESIS_PROFILE", "ci"))
