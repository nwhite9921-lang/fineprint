"""Sentence-level year-over-year diff of a section.

Alignment uses difflib on normalized sentences, then pairs sentences inside
each 'replace' block by similarity so an edited sentence shows as one
MODIFIED item with a word-level diff, not as one removed plus one added.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, asdict, field

from .textutil import normalize, split_sentences, word_diff

PAIR_THRESHOLD = 0.55   # below this, an old/new pair is reported as removed + added


@dataclass
class DiffItem:
    kind: str                 # added | removed | modified
    old: str = ""
    new: str = ""
    ratio: float = 0.0        # similarity old vs new (modified only)
    inline: str = ""          # word-level diff (modified only)
    old_index: int = -1       # sentence index in old section
    new_index: int = -1
    signals: list[str] = field(default_factory=list)
    score: float = 0.0
    elsewhere: str = ""       # similar sentence found in the other year's filing outside the aligned block
    elsewhere_ratio: float = 0.0


@dataclass
class SectionDiff:
    item: str
    old_sentences: int
    new_sentences: int
    unchanged: int
    items: list[DiffItem]

    def to_dict(self) -> dict:
        return {"item": self.item, "old_sentences": self.old_sentences, "new_sentences": self.new_sentences,
                "unchanged": self.unchanged, "added": sum(i.kind == "added" for i in self.items),
                "removed": sum(i.kind == "removed" for i in self.items),
                "modified": sum(i.kind == "modified" for i in self.items),
                "items": [asdict(i) for i in self.items]}


def _pair_block(old: list[str], new: list[str], oi: int, ni: int) -> list[DiffItem]:
    """Greedy best-match pairing inside a replace block."""
    items: list[DiffItem] = []
    used_new: set[int] = set()
    cands = []
    for a, o in enumerate(old):
        for b, n in enumerate(new):
            r = difflib.SequenceMatcher(None, normalize(o), normalize(n), autojunk=False).ratio()
            cands.append((r, a, b))
    cands.sort(reverse=True)
    used_old: set[int] = set()
    for r, a, b in cands:
        if r < PAIR_THRESHOLD:
            break
        if a in used_old or b in used_new:
            continue
        used_old.add(a); used_new.add(b)
        items.append(DiffItem("modified", old=old[a], new=new[b], ratio=round(r, 3),
                              inline=word_diff(old[a], new[b]), old_index=oi + a, new_index=ni + b))
    for a, o in enumerate(old):
        if a not in used_old:
            items.append(DiffItem("removed", old=o, old_index=oi + a))
    for b, n in enumerate(new):
        if b not in used_new:
            items.append(DiffItem("added", new=n, new_index=ni + b))
    items.sort(key=lambda it: (it.new_index if it.new_index >= 0 else it.old_index))
    return items


def diff_sections(old_text: str, new_text: str, item: str = "", new_full_text: str | None = None,
                  old_full_text: str | None = None) -> SectionDiff:
    old_s, new_s = split_sentences(old_text), split_sentences(new_text)
    old_n, new_n = [normalize(s) for s in old_s], [normalize(s) for s in new_s]
    sm = difflib.SequenceMatcher(None, old_n, new_n, autojunk=False)
    items: list[DiffItem] = []
    unchanged = 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            unchanged += i2 - i1
        elif op == "delete":
            items.extend(DiffItem("removed", old=old_s[k], old_index=k) for k in range(i1, i2))
        elif op == "insert":
            items.extend(DiffItem("added", new=new_s[k], new_index=k) for k in range(j1, j2))
        else:
            # cap pathological blocks to keep pairing quadratic-but-small
            if (i2 - i1) * (j2 - j1) > 40000:
                items.extend(DiffItem("removed", old=old_s[k], old_index=k) for k in range(i1, i2))
                items.extend(DiffItem("added", new=new_s[k], new_index=k) for k in range(j1, j2))
            else:
                items.extend(_pair_block(old_s[i1:i2], new_s[j1:j2], i1, j1))
    _rescue_moved(items, old_s, new_s, old_n, new_n)
    if new_full_text:
        _flag_elsewhere(items, "removed", old_n, new_full_text)
    if old_full_text:
        _flag_elsewhere(items, "added", new_n, old_full_text)
    return SectionDiff(item=item, old_sentences=len(old_s), new_sentences=len(new_s), unchanged=unchanged, items=items)


MOVED_THRESHOLD = 0.60


def _rescue_moved(items: list[DiffItem], old_s, new_s, old_n, new_n) -> None:
    """Dropped language is the classic tell, so a false 'removed' is the costliest
    false positive this tool can emit. Before reporting one, search the whole
    new section (not just the aligned block) for a sentence that resembles it;
    if found, report it as MODIFIED with the match. Symmetric for 'added'."""
    used_new = {it.new_index for it in items if it.kind == "modified"}
    used_old = {it.old_index for it in items if it.kind == "modified"}
    added = {it.new_index: it for it in items if it.kind == "added"}
    new_w = [_words(b) for b in new_n]
    for it in items:
        if it.kind != "removed":
            continue
        a = old_n[it.old_index]
        pool_n = [b if j not in used_new else "" for j, b in enumerate(new_n)]
        pool_w = [w if j not in used_new else set() for j, w in enumerate(new_w)]
        best, best_j, _ = _best_match(a, pool_n, pool_w, MOVED_THRESHOLD)
        if best_j >= 0:
            it.kind, it.new, it.new_index, it.ratio = "modified", new_s[best_j], best_j, round(best, 3)
            it.inline = word_diff(it.old, it.new)
            used_new.add(best_j)
            if best_j in added:            # the counterpart 'added' item is now explained
                added[best_j].kind = "explained"
    items[:] = [it for it in items if it.kind != "explained"]


_WORD = re.compile(r"[a-z][a-z\-']{3,}|\d[\d,\.]*")


def _words(n: str) -> set[str]:
    return set(_WORD.findall(n))


def _best_match(a: str, pool_n: list[str], pool_w: list[set[str]], threshold: float) -> tuple[float, int, float]:
    """(ratio, index, containment). Token-overlap prefilter keeps this linear in
    practice; SequenceMatcher runs only on the handful of plausible sentences."""
    aw = _words(a)
    if not aw:
        return 0.0, -1, 0.0
    best, best_j, best_c = 0.0, -1, 0.0
    cands = []
    for j, bw in enumerate(pool_w):
        if not bw:
            continue
        c = len(aw & bw) / len(aw)
        if c >= 0.5:
            cands.append((c, j))
    cands.sort(reverse=True)
    for c, j in cands[:25]:
        b = pool_n[j]
        if len(b) < 0.4 * len(a):
            continue
        r = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
        # a short sentence folded into a longer one: containment counts, ratio does not
        score = max(r, c if c >= 0.85 and len(b) > len(a) else 0.0)
        if score > best:
            best, best_j, best_c = score, j, c
    if best >= threshold:
        return best, best_j, best_c
    return 0.0, -1, 0.0


def _flag_elsewhere(items: list[DiffItem], kind: str, norm: list[str], other_full_text: str) -> None:
    """Gate rule: language reported as removed (or added) must also be absent from
    the WHOLE other-year filing. If a similar sentence exists elsewhere (another
    Item, a footnote, or folded into a longer sentence), the item is kept but
    tagged so it is not read as 'dropped'."""
    pool_s = split_sentences(other_full_text)
    pool_n = [normalize(x) for x in pool_s]
    pool_w = [_words(x) for x in pool_n]
    for it in items:
        if it.kind != kind:
            continue
        a = norm[it.old_index] if kind == "removed" else norm[it.new_index]
        r, j, c = _best_match(a, pool_n, pool_w, MOVED_THRESHOLD)
        if j >= 0:
            it.elsewhere = pool_s[j]
            it.elsewhere_ratio = round(r, 3)
