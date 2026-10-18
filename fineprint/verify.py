"""Verification gate. A finding is only as good as its quote, and the quote is
only accepted if it string-matches the source document.

Statuses
  exact       quote found verbatim in the source
  normalized  found after whitespace / quote-mark / dash normalization (reported as a pass)
  near        best candidate sentence is >= NEAR_THRESHOLD similar; REJECTED, candidate shown so a human can fix the quote
  fail        nothing close in the source; REJECTED
Every verification, pass or fail, is appended to the verification log; every
rejection is an AI-error-log entry waiting to happen.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, asdict

from .extract import ParsedFiling
from .textutil import normalize, split_sentences, TextIndex

NEAR_THRESHOLD = 0.80


@dataclass
class VerifyResult:
    status: str                 # exact | normalized | near | fail
    passed: bool
    score: float
    quote: str
    section: str = ""           # item the quote was found in, if any
    page_index: int = 0         # sequential page from the document's page breaks
    page_folio: str = ""        # printed page number read from the page foot, if any
    offset: int = -1
    candidate: str = ""         # closest source sentence (near/fail)
    context: str = ""           # +/- 150 chars around the match
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _ellipsis_parts(q: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\s*(?:\.\.\.|…|\[\.\.\.\]|\[…\])\s*", q) if p.strip()]
    return parts or [q]


def verify_quote(quote: str, filing: ParsedFiling, max_gap: int = 2000) -> VerifyResult:
    q = quote.strip().strip('"“”').strip()
    if len(q) < 12:
        return VerifyResult("fail", False, 0.0, quote, note="quote too short to verify (min 12 chars)")

    # 1. exact, every occurrence
    offs = [m.start() for m in re.finditer(re.escape(q), filing.text)]
    status = "exact"
    # 2. normalized (handles smart quotes, dashes, line wraps, page breaks mid-quote)
    if not offs:
        idx = filing.index if getattr(filing, "index", None) else TextIndex(filing.text)
        filing.index = idx
        parts = _ellipsis_parts(q)
        offs = idx.find_all(q) if len(parts) == 1 else [o for o in [idx.find_parts(parts, max_gap)] if o >= 0]
        status = "normalized"
    if offs:
        # prefer an occurrence inside an extracted section (the cover/Business text often repeats Item 1A sentences)
        in_sec = [o for o in offs if _section_at(filing, o)]
        off = (in_sec or offs)[0]
        sec = _section_at(filing, off)
        pi, folio = filing.page_map.page_of(off)
        note = f"{len(offs)} occurrences in the filing" if len(offs) > 1 else ""
        return VerifyResult(status, True, 1.0, quote, section=sec or "outside extracted items", page_index=pi,
                            page_folio=folio, offset=off, context=_ctx(filing.text, off, len(q)), note=note)

    # 3. nearest sentence, for the reviewer
    best, best_r, best_sec = "", 0.0, ""
    nq = normalize(_ellipsis_parts(q)[0])
    pool = filing.sections.values() or []
    for sec in pool:
        for s in split_sentences(sec.text):
            ns = normalize(s)
            if abs(len(ns) - len(nq)) > max(60, len(nq)):
                continue
            r = difflib.SequenceMatcher(None, nq, ns, autojunk=False).quick_ratio()
            if r > best_r:
                r = difflib.SequenceMatcher(None, nq, ns, autojunk=False).ratio()
                if r > best_r:
                    best, best_r, best_sec = s, r, sec.item
    if best_r >= NEAR_THRESHOLD:
        return VerifyResult("near", False, round(best_r, 3), quote, section=best_sec, candidate=best,
                            note="close but not verbatim; fix the quote to the candidate or reject the finding")
    return VerifyResult("fail", False, round(best_r, 3), quote, section=best_sec, candidate=best,
                        note="not found in source")


def _section_at(filing: ParsedFiling, off: int) -> str:
    for it, sec in filing.sections.items():
        if sec.start <= off < sec.end:
            return it
    return ""


def _ctx(text: str, off: int, n: int, pad: int = 150) -> str:
    return text[max(0, off - pad): off + n + pad].replace("\f", " ").replace("\n", " ")


# --------------------------------------------------------------------------
# Seeded-error test: prove the gate catches what a model would get wrong
# --------------------------------------------------------------------------
def seed_errors(quote: str) -> dict[str, str]:
    """Return plausible wrong versions of a correct quote: a changed number, a
    softened verb, a dropped qualifier. Used for the demo and the test suite."""
    variants = {}
    m = re.search(r"\d+(?:\.\d+)?", quote)
    if m:
        num = m.group(0)
        new = str(int(float(num)) + 1) if "." not in num else f"{float(num) + 0.1:.1f}"
        variants["changed_number"] = quote[:m.start()] + new + quote[m.end():]
    for a, b in [("may", "will"), ("could", "will"), ("decrease", "increase"), ("adversely", "materially"), ("not", "")]:
        if re.search(rf"\b{a}\b", quote):
            variants[f"swapped_{a}_{b or 'dropped'}"] = re.sub(rf"\b{a}\b", b, quote, count=1).replace("  ", " ")
            break
    variants["fabricated_tail"] = quote.rstrip(".") + ", as management confirmed on the call."
    return variants
