"""Sentence splitting and normalization shared by diff and verify."""
from __future__ import annotations

import re
import unicodedata

_ABBREVS = {"u.s", "u.k", "inc", "ltd", "corp", "co", "no", "nos", "vs", "approx", "al", "dr", "mr", "mrs", "ms",
            "jr", "sr", "st", "fig", "e.g", "i.e", "dept", "ex", "sec", "u.s.a"}
_BOUNDARY = re.compile(r"[\.\?\!][\"\u201d\)]*\s+(?=[A-Z\(\"\u201c])")


def _split_text(s: str) -> list[str]:
    out, start = [], 0
    for m in _BOUNDARY.finditer(s):
        end = m.end()
        before = s[start:m.start() + 1]
        last = before.rstrip(".?!").split()
        tok = last[-1].lower().strip("()\"'") if last else ""
        if tok in _ABBREVS or re.fullmatch(r"[a-z]", tok) or re.fullmatch(r"\d+", tok) and len(tok) <= 2:
            continue
        out.append(s[start:end].strip()); start = end
    tail = s[start:].strip()
    if tail:
        out.append(tail)
    return out


QUOTE_MAP = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-",
    " ": " ", "…": "...",
}


def normalize(s: str) -> str:
    """Whitespace, quote and dash normalization. Lowercases. Keeps digits and
    punctuation that carry meaning (%, $, decimal points)."""
    s = unicodedata.normalize("NFKC", s)
    s = "".join(QUOTE_MAP.get(ch, ch) for ch in s)
    s = s.replace("\f", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def split_sentences(text: str) -> list[str]:
    """Split a section into sentences, treating table rows and short lines as
    their own units so numbers in tables stay quotable."""
    sents: list[str] = []
    text = join_page_breaks(text)
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        lines = [ln.strip() for ln in para.split("\n") if ln.strip()]
        # table-ish block: rows with cell separators
        if sum("|" in ln for ln in lines) >= max(2, len(lines) // 2):
            sents.extend(lines)
            continue
        joined = " ".join(lines)
        for s in _split_text(joined):
            s = s.strip()
            if len(s) >= 3:
                sents.append(s)
    return sents


_PB = re.compile(r"[ \t]*\n*[ \t]*\f[ \t]*\n*[ \t]*")


def join_page_breaks(text: str) -> str:
    """A sentence that straddles a page break must stay one sentence. If the text
    before the break does not end with sentence punctuation, the break (and the
    blank lines around it) collapses to a single space; otherwise it becomes a
    paragraph break. Page lookup is unaffected because it uses normalized search."""
    def repl(m):
        before = text[:m.start()].rstrip()
        return "\n\n" if (not before or before[-1] in ".?!:") else " "
    return _PB.sub(repl, text)


def word_diff(a: str, b: str) -> str:
    """Inline word-level diff: [-removed-] {+added+}."""
    import difflib
    aw, bw = a.split(), b.split()
    sm = difflib.SequenceMatcher(None, aw, bw, autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out.append(" ".join(aw[i1:i2]))
        elif op == "delete":
            out.append("[-" + " ".join(aw[i1:i2]) + "-]")
        elif op == "insert":
            out.append("{+" + " ".join(bw[j1:j2]) + "+}")
        else:
            out.append("[-" + " ".join(aw[i1:i2]) + "-] {+" + " ".join(bw[j1:j2]) + "+}")
    return " ".join(out)


class TextIndex:
    """Normalized view of a text with a map back to raw offsets, so a sentence
    that was re-joined across line breaks can still be located in the source."""

    def __init__(self, text: str):
        out, back = [], []
        prev_space = False
        for i, ch in enumerate(text):
            if ch.isspace() or ch == "\f":
                n = " "
            else:
                n = normalize(ch) or ch.lower()
            if n == " ":
                if prev_space:
                    continue
                prev_space = True
            else:
                prev_space = False
            for c in n:
                out.append(c); back.append(i)
        self.ntext = "".join(out)
        self.back = back
        self.raw = text

    def find(self, needle: str, start: int = 0) -> int:
        """Raw offset of the first normalized occurrence of needle, or -1."""
        nn = normalize(needle)
        if not nn:
            return -1
        j = self.ntext.find(nn, start)
        return self.back[j] if j >= 0 else -1

    def find_all(self, needle: str) -> list[int]:
        nn = normalize(needle)
        out, j = [], 0
        while nn:
            j = self.ntext.find(nn, j)
            if j < 0:
                break
            out.append(self.back[j]); j += 1
        return out

    def find_parts(self, parts: list[str], max_gap: int = 2000) -> int:
        """Ordered ellipsis search: every part must appear, in order, within max_gap of the previous one."""
        pos, first = 0, -1
        for k, p in enumerate(parts):
            nn = normalize(p)
            j = self.ntext.find(nn, pos)
            if j < 0 or (k > 0 and j - pos > max_gap):
                return -1
            if k == 0:
                first = j
            pos = j + len(nn)
        return self.back[first] if first >= 0 else -1


NUM_TOKEN = re.compile(r"[\d\$\(\),\.%]+")


def numbers_only_change(inline: str) -> bool:
    """True if every removed/added token in a word diff carries a digit or is a
    year-roll word (a routine roll-forward of the same sentence)."""
    changed = re.findall(r"\[-(.*?)-\]|\{\+(.*?)\+\}", inline)
    toks = [t for pair in changed for t in " ".join(pair).split()]
    if not toks:
        return False
    return all(re.search(r"\d", t) or t.strip(",.;") in {"and", "in", "to", "$", "million", "billion"} for t in toks)
