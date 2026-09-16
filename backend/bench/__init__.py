"""The benchmark harness.

This layer exists because the locked evaluator in backend/eval/ scores only the pairs
the predictor happens to reach, which is a restricted-negative setting. Nothing here
edits backend/eval/. The harness imports it read-only, reconstructs the full candidate
universe, and reports every metric with its denominator attached.

The harness is predictor-agnostic and dataset-agnostic by construction: it consumes a
mapping of pair to score, so a new scorer or a new interactome needs no change here.
"""
