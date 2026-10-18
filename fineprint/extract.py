"""Turn a 10-K primary document (HTML / inline XBRL) into plain text with
page markers, then locate Item 1A (Risk Factors) and Item 7 (MD&A).

Page numbers are COMPUTED from the document's own page breaks, never guessed:
each page-break element becomes a form-feed character, and the printed folio
(the bare number at the foot of each page) is read when present.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import warnings
from bs4 import BeautifulSoup, NavigableString, Tag, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

PAGE_BREAK = "\f"
BLOCK_TAGS = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "hr", "section", "article"}
CELL_TAGS = {"td", "th"}


# --------------------------------------------------------------------------
# HTML -> text
# --------------------------------------------------------------------------
def _is_page_break(tag: Tag) -> bool:
    if tag.name == "hr":
        return True
    style = (tag.get("style") or "").replace(" ", "").lower()
    return "page-break-before:always" in style or "page-break-after:always" in style or "break-before:page" in style or "break-after:page" in style


def _hidden(tag: Tag) -> bool:
    style = (tag.get("style") or "").replace(" ", "").lower()
    return "display:none" in style


def html_to_text(html: str | bytes) -> str:
    """Flatten HTML to text. Block elements end lines, table cells are joined
    with ' | ', page breaks become form feeds. Hidden iXBRL headers are dropped."""
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "head", "title"]):
        t.decompose()
    for t in soup.find_all(["ix:header"]):
        t.decompose()
    for t in soup.find_all(True):
        if _hidden(t):
            t.decompose()

    out: list[str] = []

    def walk(node):
        if isinstance(node, NavigableString):
            out.append(str(node))
            return
        if not isinstance(node, Tag):
            return
        name = node.name.lower()
        if _is_page_break(node):
            out.append("\n" + PAGE_BREAK + "\n")
            if name == "hr":
                return
        if name in CELL_TAGS:
            out.append(" | ")
        if name in BLOCK_TAGS:
            out.append("\n")
        for child in node.children:
            walk(child)
        if name in BLOCK_TAGS:
            out.append("\n")

    walk(soup.body or soup)
    text = "".join(out)
    text = text.replace("\xa0", " ").replace("​", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------
# Page map
# --------------------------------------------------------------------------
@dataclass
class PageMap:
    break_offsets: list[int]           # char offsets of each form feed
    folios: dict[int, str] = field(default_factory=dict)  # break index -> printed page number found just before it

    def page_of(self, offset: int) -> tuple[int, str]:
        """(sequential page index starting at 1, printed folio or '' if none read)."""
        idx = sum(1 for b in self.break_offsets if b < offset)
        # the folio printed at the foot of page idx+1 sits just before break idx
        return idx + 1, self.folios.get(idx, "")


_FOLIO_RE = re.compile(r"^\s*(?:page\s+)?(\d{1,3}|[ivxlc]{1,6})\s*$", re.I)

# Footers in PDF text extracts, e.g. "14 | 2025 Form 10-K", "2025 Form 10-K | 14", "Page 14 of 120", bare "14"
_TEXT_FOOTER_RE = re.compile(
    r"^\s*(?:(\d{1,3})\s*\|\s*(?:fy)?\s*20\d\d\s+form\s+10-[kq][^\n]{0,20}"
    r"|(?:fy)?\s*20\d\d\s+form\s+10-[kq]\s*\|\s*(\d{1,3})"
    r"|page\s+(\d{1,3})\s+of\s+\d{1,4}"
    r"|[^\n]{0,60}\|\s*(\d{1,3})\s*$"
    r"|(\d{1,3}))\s*$", re.I | re.M)


def add_text_page_breaks(text: str) -> tuple[str, PageMap]:
    """For PDF text extracts (no form feeds): turn each page-footer line into a
    page break and read the printed folio from it. Folios must be increasing
    to count, which filters out stray numbers in tables."""
    pieces, offsets, folios = [], [], {}
    last_folio, pos, k = 0, 0, 0
    for m in _TEXT_FOOTER_RE.finditer(text):
        folio = next(g for g in m.groups() if g)
        try:
            n = int(folio)
        except ValueError:
            continue
        if not (last_folio < n <= last_folio + 3):
            continue
        pieces.append(text[pos:m.start()]); pieces.append("\n" + PAGE_BREAK + "\n")
        offsets.append(sum(len(x) for x in pieces) - 2)
        folios[k] = folio; k += 1
        last_folio, pos = n, m.end()
    pieces.append(text[pos:])
    return "".join(pieces), PageMap(offsets, folios)


def build_page_map(text: str) -> PageMap:
    offsets = [m.start() for m in re.finditer(PAGE_BREAK, text)]
    folios: dict[int, str] = {}
    for i, off in enumerate(offsets):
        tail = text[max(0, off - 300):off]
        lines = [ln.strip() for ln in tail.split("\n") if ln.strip()]
        for ln in reversed(lines[-4:]):
            m = _FOLIO_RE.match(ln)
            if m:
                folios[i] = m.group(1)
                break
    return PageMap(offsets, folios)


# --------------------------------------------------------------------------
# Section location
# --------------------------------------------------------------------------
@dataclass
class Section:
    item: str          # "1A" or "7"
    title: str
    start: int         # char offset in full text
    end: int
    text: str
    page_start: tuple[int, str]
    page_end: tuple[int, str]


SECTION_SPECS = {
    "1A": dict(title="Risk Factors",
               start=r"item\s*1a\s*[\.\:\-–—]?\s*(?:\|\s*)?risk\s+factors",
               end=r"item\s*(?:1b|1c|2)\s*[\.\:\-–—]?\s*(?:\|\s*)?(?:unresolved|cybersecurity|properties)"),
    "7":  dict(title="Management's Discussion and Analysis",
               start=r"item\s*7\s*[\.\:\-–—]?\s*(?:\|\s*)?management[’'`]?s?\s+discussion",
               end=r"item\s*(?:7a|8)\s*[\.\:\-–—]?\s*(?:\|\s*)?(?:quantitative|financial\s+statements)"),
    "1":  dict(title="Business",
               start=r"item\s*1\s*[\.\:\-–—]?\s*(?:\|\s*)?business\b",
               end=r"item\s*1a\s*[\.\:\-–—]?\s*(?:\|\s*)?risk\s+factors"),
    "8":  dict(title="Financial Statements and Supplementary Data",
               start=r"item\s*8\s*[\.\:\-–—]?\s*(?:\|\s*)?financial\s+statements",
               end=r"item\s*9\s*[\.\:\-–—]?\s*(?:\|\s*)?changes\s+in\s+and\s+disagreements"),
}


def _line_start_matches(pattern: str, text: str) -> list[int]:
    """Offsets where the pattern begins a line (so cross-references mid-sentence
    and table-of-contents rows are handled by span length, not by guessing)."""
    rx = re.compile(r"(?im)^[\s\|]*(?:part\s+i+\s*[\|\-–—,]*\s*)?(" + pattern + ")")
    return [m.start(1) for m in rx.finditer(text)]


def find_section(text: str, item: str, page_map: PageMap | None = None) -> Section | None:
    spec = SECTION_SPECS[item]
    starts = _line_start_matches(spec["start"], text)
    ends = _line_start_matches(spec["end"], text)
    if not starts:
        return None
    best: tuple[int, int] | None = None
    for s in starts:
        e = next((x for x in ends if x > s), len(text))
        if best is None or (e - s) > (best[1] - best[0]):
            best = (s, e)
    s, e = best
    body = text[s:e]
    # A table of contents row is short; a real section is thousands of chars.
    if len(body) < 2000:
        return None
    pm = page_map or build_page_map(text)
    return Section(item=item, title=spec["title"], start=s, end=e, text=body,
                   page_start=pm.page_of(s), page_end=pm.page_of(max(s, e - 1)))


# Browser "print to PDF" chrome and EDGAR page furniture that must not leak into quotes
_CHROME_LINE = re.compile(
    r"^[ \t]*(?:https?://\S+[ \t]+\d{1,4}/\d{1,4}"                       # https://www.sec.gov/...htm 97/219
    r"|\d{1,2}/\d{1,2}/\d{2,4},[ \t]+\d{1,2}:\d{2}[ \t]*[AP]M\b.*"        # 10/17/26, 3:31 PM bmy-20241231
    r"|table of contents"
    r"|(?:page[ \t]+)?\d{1,3}(?:[ \t]+of[ \t]+\d{1,4})?"                   # bare folio / Page 12 of 200
    r"|[ivxlc]{1,6}"
    r"|[^\n]{0,60}\|[ \t]*\d{1,3}"                                        # "2025 Form 10-K | 14"
    r"|\d{1,3}[ \t]*\|[^\n]{0,60})[ \t]*$", re.I | re.M)


def blank_page_chrome(text: str, window: int = 4) -> str:
    """Overwrite header/footer lines near each page break with spaces of the same
    length, so offsets (and therefore the page map) stay valid while sentences,
    diffs and quotes never contain URLs, print timestamps or folios."""
    out = list(text)
    bounds = [0] + [m.start() for m in re.finditer(PAGE_BREAK, text)] + [len(text)]
    for b in bounds:
        for side in (-1, 1):
            pos, seen = b, 0
            while seen < window:
                if side < 0:
                    end = text.rfind("\n", 0, max(pos - 1, 0))
                    start, stop = (end + 1 if end >= 0 else 0), max(pos - 1, 0)
                    if stop <= 0:
                        break
                    pos = start
                else:
                    start = text.find("\n", pos)
                    if start < 0:
                        break
                    start += 1
                    stop = text.find("\n", start)
                    stop = len(text) if stop < 0 else stop
                    pos = stop
                line = text[start:stop]
                if not line.strip() or line.strip() == PAGE_BREAK:
                    continue
                seen += 1
                if _CHROME_LINE.match(line):
                    for k in range(start, stop):
                        out[k] = " "
                if side < 0 and start == 0:
                    break
    return "".join(out)


@dataclass
class ParsedFiling:
    path: str
    text: str
    page_map: PageMap
    sections: dict[str, Section]
    index: object = None   # lazily built TextIndex for normalized search


def pdf_to_text(path: str | Path) -> str:
    """PDF -> text with one form feed per page, so page numbers are exact PDF pages.
    The printed folio is still read from each page foot when present. Extraction
    is slow (about a minute for a 200-page 10-K), so the text is cached next to
    the PDF as <name>.fineprint.txt, keyed on the PDF's size and mtime."""
    import logging
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    import pdfplumber
    p = Path(path)
    st = p.stat()
    stamp = f"# fineprint-cache size={st.st_size} mtime={int(st.st_mtime)}\n"
    for side in (p.with_suffix(p.suffix + ".fineprint.txt"), Path("cache") / "pdftext" / (p.name + ".txt")):
        if side.exists():
            cached = side.read_text()
            if cached.startswith(stamp):
                return cached[len(stamp):]
    pages = []
    with pdfplumber.open(str(p)) as pdf:
        for pg in pdf.pages:
            pages.append((pg.extract_text() or "").replace("\xa0", " "))
    text = ("\n" + PAGE_BREAK + "\n").join(pages)
    for side in (p.with_suffix(p.suffix + ".fineprint.txt"), Path("cache") / "pdftext" / (p.name + ".txt")):
        try:
            side.parent.mkdir(parents=True, exist_ok=True)
            side.write_text(stamp + text)
            break
        except OSError:
            continue
    return text


def parse_filing(path: str | Path, items: tuple[str, ...] = ("1A", "7")) -> ParsedFiling:
    raw = Path(path).read_bytes()
    if raw[:5] == b"%PDF-":
        text = pdf_to_text(path)
        pm = build_page_map(text)
    elif raw.lstrip()[:1] == b"<":
        text = html_to_text(raw)
        pm = build_page_map(text)
    else:
        text = raw.decode("utf-8", "replace")
        if PAGE_BREAK in text:
            pm = build_page_map(text)
        else:
            text, pm = add_text_page_breaks(text)
    text = blank_page_chrome(text)
    sections = {}
    for it in items:
        sec = find_section(text, it, pm)
        if sec:
            sections[it] = sec
    return ParsedFiling(path=str(path), text=text, page_map=pm, sections=sections)
