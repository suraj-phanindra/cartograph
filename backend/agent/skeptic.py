"""Stage 3 — SKEPTIC (adversarial). A deterministic core applies the AP-MS
frequent-flyer / CRAPome patterns from evidence/cartograph_domain.json (via the
existing skeptic_review) and flags spurious/absent co-mention evidence. An optional
Claude pass runs targeted disconfirming reasoning over the retrieved corpus and may
only make the verdict MORE skeptical (pass -> downgrade -> veto), never less. A veto
blocks the dossier. Injectable for tests.
"""
from __future__ import annotations

from backend.agent import llm
from backend.reason.hypothesis import skeptic_review

_ORDER = {"pass": 0, "downgrade": 1, "veto": 2}
_INV = {v: k for k, v in _ORDER.items()}

_SYSTEM = (
    "You are the Skeptic in a protein-interaction pipeline. Judge the evidence for the "
    "interaction from the retrieved abstracts, calibrated and fair — do NOT reject a "
    "plausible interaction merely because the abstracts don't fully spell out the "
    "mechanism. Default to 'pass'. Use 'downgrade' when the evidence is thin, indirect, "
    "or co-complex rather than direct. Use 'veto' ONLY when there is a CONCRETE reason "
    "the interaction is likely an artifact: a known AP-MS contaminant / frequent flyer, "
    "or a clearly spurious co-mention (both proteins merely listed together in one large "
    "review with no interaction claim), or abstracts that actively contradict a physical "
    "interaction. A veto blocks the dossier, so it must be justified by positive "
    "disconfirming evidence, never by absence of confirmation. Respond with ONLY JSON: "
    '{"verdict": "pass|downgrade|veto", "reason": str}.'
)


def _spurious_comention(corpus):
    n = len(corpus["records"])
    if corpus.get("comention_count", 0) == 0 or n == 0:
        return "no co-mention literature retrieved for this pair"
    return None


def _default_skeptic(corpus, resolved, skeptic_fn=None):
    prey = corpus["prey"]
    struct = corpus.get("structure")
    has_exp = bool(struct and struct.get("kind") == "experimental")
    base = skeptic_review(prey, has_structure=has_exp, literature_count=len(corpus["records"]))
    verdict, reason = base["verdict"], base["reason"]

    spurious = _spurious_comention(corpus)
    if spurious and _ORDER["downgrade"] > _ORDER[verdict]:
        verdict, reason = "downgrade", spurious

    if llm.available():
        try:
            papers = "\n\n".join(f"PMID {p} — {r['title']}\n{(r['abstract'] or '')[:900]}"
                                 for p, r in list(corpus["records"].items())[:12])
            out = llm.call_json(_SYSTEM, f"Pair: {corpus['bait']} + {prey}.\nABSTRACTS:\n{papers or '(none)'}")
            if out and out.get("verdict") in _ORDER and _ORDER[out["verdict"]] > _ORDER[verdict]:
                verdict, reason = out["verdict"], out.get("reason", reason)  # only ratchets up
        except Exception:  # noqa: BLE001 - skeptic failure never loosens the base verdict
            pass
    return {"verdict": verdict, "reason": reason, "caveat": base.get("caveat")}


def review(corpus, resolved, skeptic_fn=None):
    return (skeptic_fn or _default_skeptic)(corpus, resolved)
