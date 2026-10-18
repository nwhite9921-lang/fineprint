"""'Where findings hide' signal scanner. Flags diff items whose text touches the
places the case tells analysts to look. Company-agnostic keyword families; the
reviewer decides what matters. Scores are a ranking aid, not a finding."""
from __future__ import annotations

import re

SIGNALS: dict[str, list[str]] = {
    "gross_to_net":        [r"gross[- ]to[- ]net", r"\brebates?\b", r"chargebacks?", r"discounts? and allowances", r"net price", r"price erosion", r"wholesaler", r"340b", r"part d redesign", r"manufacturer discount program", r"coverage gap"],
    "medicare_negotiation":[r"inflation reduction act", r"\bira\b", r"drug price negotiation", r"maximum fair price", r"\bmfp\b", r"negotiated price", r"selected drug", r"price applicability year", r"\bcms\b"],
    "mfn_tariff":          [r"most[- ]favou?red[- ]nation", r"\bmfn\b", r"tariffs?", r"section 232", r"trade polic"],
    "working_capital":     [r"inventor(y|ies)", r"receivables?", r"days sales outstanding", r"\bdso\b", r"allowance for (doubtful|credit)"],
    "contingent_consideration": [r"contingent consideration", r"fair value (re)?measurement", r"milestone payments?", r"earn[- ]out"],
    "royalty_profit_share":[r"royalt(y|ies)", r"profit[- ]shar", r"collaboration revenue", r"co[- ]promotion"],
    "litigation":          [r"litigation", r"lawsuits?", r"class action", r"settlement", r"antitrust", r"qui tam", r"subpoena", r"investigation by"],
    "tax":                 [r"effective tax rate", r"\bpillar two\b", r"tax reform", r"transfer pricing", r"\birs\b", r"uncertain tax"],
    "patent_exclusivity":  [r"loss of exclusivity", r"\bloe\b", r"patent expir", r"biosimilars?", r"generic competition", r"paragraph iv", r"composition of matter"],
    "label_safety":        [r"boxed warning", r"black box", r"safety signal", r"label (change|update|restriction)", r"\bfda\b.*(warn|restrict|limit)"],
    "segment_reclass":     [r"reclassif", r"restat", r"change in (presentation|segment)", r"no longer (report|disclos)", r"prior period"],
    "guidance_language":   [r"we (no longer|do not) expect", r"lower than (previously )?expected", r"deceler", r"slow(er|ing)", r"headwind", r"pressure on", r"uncertaint"],
    "impairment":          [r"impairment", r"write[- ]?down", r"write[- ]?off"],
    "pipeline_dependency": [r"depend(s|ent|ence) on", r"substantial portion of (our|the company'?s) (revenue|net revenues)", r"significant portion"],
}

_COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in SIGNALS.items()}

KIND_WEIGHT = {"added": 1.0, "modified": 1.2, "removed": 1.1}   # dropped language is the classic tell
NUMERIC = re.compile(r"\$?\d[\d,\.]*\s*(?:%|percent|million|billion)?")


def scan(text: str) -> list[str]:
    hits = []
    for name, rxs in _COMPILED.items():
        if any(rx.search(text) for rx in rxs):
            hits.append(name)
    return hits


def score_items(items) -> None:
    for it in items:
        txt = (it.old + " " + it.new)
        it.signals = scan(txt)
        base = len(it.signals) * KIND_WEIGHT[it.kind]
        if NUMERIC.search(txt):
            base += 0.5
        if it.kind == "modified" and it.ratio < 0.9:
            base += 0.3
        it.score = round(base, 2)
