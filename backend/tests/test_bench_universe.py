"""The candidate universe. Every metric in the bench layer is computed over this set,
so its definition is pinned here rather than derived at each call site."""
from backend.bench import universe
from backend.eval.evaluator import build_training_graph
from backend.eval.freeze_split import load_frozen


def _train():
    return build_training_graph(load_frozen())


def test_universe_is_every_untested_bait_human_pair():
    u = universe.candidate_universe(_train())
    # 26 viral baits x 332 human preys = 8632, minus the 275 bait-prey edges that
    # survive in the training graph (332 known minus the 57 held out).
    assert len(u) == 8357


def test_universe_contains_every_held_out_edge():
    u = universe.candidate_universe(_train())
    held = {tuple(e) for e in load_frozen()["held_out"]}
    assert held <= u, "held-out edges are untested pairs and must be candidates"


def test_universe_excludes_edges_the_predictor_can_see():
    train = _train()
    u = universe.candidate_universe(train)
    assert not any(train.has_edge(b, p) for b, p in u)


def test_universe_pairs_are_viral_bait_to_human_prey():
    train = _train()
    for bait, prey in universe.candidate_universe(train):
        assert train.nodes[bait]["type"] == "viral"
        assert train.nodes[prey]["type"] == "human"


def test_prevalence_is_positives_over_universe():
    assert universe.prevalence(57, 8357) == 57 / 8357


def test_open_world_universe_scales_by_background_proteome():
    # 26 baits against a pinned reviewed-proteome background
    assert universe.open_world_size(n_baits=26, n_background=20400) == 26 * 20400
