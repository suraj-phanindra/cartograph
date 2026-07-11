"""Novelty grounding for worklist hypotheses.

A predicted bait->prey edge is tagged known / partially known / novel, grounded
in a REAL literature check, never guessed:

  - known           the edge is a recovered held-out Gordon AP-MS edge, OR it has
                    a cited edge pack (a documented interaction).
  - partially known not documented, but the bait and prey are co-mentioned in the
                    SARS-CoV-2 PubMed literature (>=1 hit) -- some prior exists.
  - novel           not documented and 0 PubMed co-mentions -- a genuinely new
                    proposal for someone to test.

Co-mention counts come from NCBI esearch and are pre-cached to a committed file
so the offline demo never hits the network. Nothing is fabricated: if a pair has
no cached count it is tagged 'unassessed', not guessed.
"""
import json
import time
import urllib.parse
import urllib.request

from backend import config

CACHE = config.EVIDENCE_DIR / "novelty_comention.cached.json"
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# Viral bait names that are ambiguous as bare PubMed terms -> a specific synonym.
# Everything else (Nsp9, Orf6, Orf10, ...) is specific enough quoted verbatim.
BAIT_TERM = {
    "N": '"nucleocapsid"',
    "M": '"membrane glycoprotein"',
    "E": '"envelope protein"',
    "S": '"spike"',
    "Spike": '"spike"',
}


def _term(bait, prey):
    bt = BAIT_TERM.get(bait, f'"{bait}"')
    return f'"{prey}"[tiab] AND ({bt}) AND SARS-CoV-2'


def _fetch_count(bait, prey, timeout=15):
    q = urllib.parse.urlencode({"db": "pubmed", "retmode": "json", "term": _term(bait, prey)})
    with urllib.request.urlopen(f"{ESEARCH}?{q}", timeout=timeout) as r:
        return int(json.load(r)["esearchresult"]["count"])


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {}


def precache(pairs, pause=0.34):
    """Fetch + cache co-mention counts for (bait, prey) pairs. pause respects the
    3 req/s anonymous NCBI limit."""
    cache = load_cache()
    for bait, prey in pairs:
        key = f"{bait}|{prey}"
        if key in cache:
            continue
        try:
            cache[key] = _fetch_count(bait, prey)
        except Exception as e:  # noqa: BLE001 - best-effort; leave uncached, never guess
            print(f"  ! {key}: {e}")
            continue
        print(f"  {key}: {cache[key]}")
        time.sleep(pause)
    CACHE.write_text(json.dumps(cache, indent=2, sort_keys=True))
    return cache


def classify(bait, prey, recovered, has_dossier, cache=None):
    """Return {tag, basis} grounded in ground truth + a real co-mention count."""
    if recovered:
        return {"tag": "known", "basis": "recovered held-out Gordon AP-MS edge"}
    if has_dossier:
        return {"tag": "known", "basis": "documented interaction (cited edge pack)"}
    cache = load_cache() if cache is None else cache
    n = cache.get(f"{bait}|{prey}")
    if n is None:
        return {"tag": "unassessed", "basis": "co-mention count not cached"}
    if n >= 1:
        s = "s" if n != 1 else ""
        return {"tag": "partially known", "basis": f"{n} PubMed co-mention{s} (SARS-CoV-2 context)"}
    return {"tag": "novel", "basis": "0 PubMed co-mentions (SARS-CoV-2 context)"}


if __name__ == "__main__":
    # demo self-check: classifier is monotonic in the real signals
    c = {"Orf6|RAE1": 17, "Nsp9|PCNT": 0}
    assert classify("Orf6", "RAE1", True, False, c)["tag"] == "known"
    assert classify("Orf6", "RAE1", False, False, c)["tag"] == "partially known"
    assert classify("Nsp9", "PCNT", False, False, c)["tag"] == "novel"
    assert classify("X", "Y", False, False, c)["tag"] == "unassessed"
    print("novelty classify ok")
