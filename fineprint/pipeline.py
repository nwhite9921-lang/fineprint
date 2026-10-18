"""End-to-end run: filings in, diffs + ranked candidates + verification out.

Outputs (in --out directory):
  filings.json             which documents were used (source URL, local path, fiscal year)
  sections/<FY>_item1A.txt sections as extracted, with page breaks kept as form feeds
  diff_item1A.json / diff_item7.json
  candidates.md            ranked changed language with signals, quotes and computed pages
  candidates.json          the same, machine-readable, ready for the drafting step
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .edgar import EdgarClient, Filing, local_filing
from .extract import parse_filing, ParsedFiling
from .diff import diff_sections
from .signals import score_items
from .textutil import TextIndex, numbers_only_change


def load_filings(ticker: str | None, local_paths: list[str] | None, cache_dir: str, user_agent: str | None) -> list[Filing]:
    if local_paths:
        fs = [local_filing(p, ticker or "LOCAL") for p in local_paths]
    else:
        client = EdgarClient(user_agent=user_agent) if user_agent else EdgarClient(cache_dir=cache_dir)
        client.cache_dir = Path(cache_dir)
        fs = client.fetch_last_10ks(ticker, 2)
    fs.sort(key=lambda f: f.fiscal_year)      # oldest first
    for i, f in enumerate(fs):               # never let two filings share a key
        if not f.fiscal_year:
            f.report_date = f"FY?{i}"
    return fs


def run(ticker: str | None, out: str, local_paths: list[str] | None = None, cache_dir: str = "cache",
        user_agent: str | None = None, items: tuple[str, ...] = ("1A", "7"), top: int = 40) -> dict:
    outdir = Path(out); (outdir / "sections").mkdir(parents=True, exist_ok=True)
    filings = load_filings(ticker, local_paths, cache_dir, user_agent)
    if len(filings) < 2:
        raise SystemExit("need two filings to diff")
    old_f, new_f = filings[-2], filings[-1]
    (outdir / "filings.json").write_text(json.dumps([asdict(f) for f in filings], indent=2))

    parsed = {}
    for f in (old_f, new_f):
        p = parse_filing(f.local_path, items)
        parsed[f.fiscal_year] = p
        for it, sec in p.sections.items():
            (outdir / "sections" / f"FY{f.fiscal_year}_item{it}.txt").write_text(sec.text)
        missing = [it for it in items if it not in p.sections]
        if missing:
            print(f"[warn] FY{f.fiscal_year}: could not locate Item {', '.join(missing)}")

    summary = {"ticker": ticker, "old": old_f.fiscal_year, "new": new_f.fiscal_year, "sections": {}}
    all_items = []
    for it in items:
        o, n = parsed[old_f.fiscal_year].sections.get(it), parsed[new_f.fiscal_year].sections.get(it)
        if not (o and n):
            continue
        d = diff_sections(o.text, n.text, it, new_full_text=parsed[new_f.fiscal_year].text,
                          old_full_text=parsed[old_f.fiscal_year].text)
        score_items(d.items)
        dd = d.to_dict()
        (outdir / f"diff_item{it}.json").write_text(json.dumps(dd, indent=2))
        summary["sections"][it] = {k: dd[k] for k in ("old_sentences", "new_sentences", "unchanged", "added", "removed", "modified")}
        pm_new, pm_old = parsed[new_f.fiscal_year].page_map, parsed[old_f.fiscal_year].page_map
        idx_new, idx_old = TextIndex(n.text), TextIndex(o.text)
        for x in d.items:
            # page of the quote, computed from the document the quote lives in
            if x.kind in ("added", "modified"):
                off = idx_new.find(x.new); page = pm_new.page_of(n.start + off) if off >= 0 else (0, "")
                src_fy = new_f.fiscal_year
            else:
                off = idx_old.find(x.old); page = pm_old.page_of(o.start + off) if off >= 0 else (0, "")
                src_fy = old_f.fiscal_year
            roll = x.kind == "modified" and numbers_only_change(x.inline)
            if roll:
                x.score = round(x.score * 0.6, 2)
            if x.elsewhere:                 # not really dropped/new: similar language exists in the other filing
                x.score = round(x.score * 0.4, 2)
            all_items.append({"item": it, "source_fy": src_fy, "page_index": page[0], "page_folio": page[1],
                              "numbers_only": roll, **asdict(x)})
    all_items.sort(key=lambda r: (-r["score"], r["item"]))
    ranked = [r for r in all_items if r["score"] > 0][:top]
    (outdir / "candidates.json").write_text(json.dumps(ranked, indent=2))
    (outdir / "candidates.md").write_text(render_candidates(ranked, summary, old_f, new_f))
    summary["candidates"] = len(ranked)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))
    from .report import render
    summary["review_page"] = str(render(outdir))
    return summary


def render_candidates(ranked: list[dict], summary: dict, old_f: Filing, new_f: Filing) -> str:
    lines = [f"# FinePrint candidates: {new_f.ticker} FY{old_f.fiscal_year} -> FY{new_f.fiscal_year}", ""]
    lines.append(f"Old: {old_f.url}  ")
    lines.append(f"New: {new_f.url}", )
    lines.append("")
    for it, s in summary["sections"].items():
        lines.append(f"- Item {it}: {s['old_sentences']} -> {s['new_sentences']} sentences; {s['added']} added, {s['removed']} removed, {s['modified']} modified, {s['unchanged']} unchanged")
    lines.append("")
    lines.append("Each entry quotes the filing verbatim. Page = sequential page computed from the document's page breaks (printed folio in brackets when readable). These are CANDIDATES for a human to read, not findings.")
    lines.append("")
    for i, r in enumerate(ranked, 1):
        pg = f"p.{r['page_index']}" + (f" [{r['page_folio']}]" if r["page_folio"] else "")
        tag = " (numbers roll-forward)" if r.get("numbers_only") else ""
        lines.append(f"## {i}. [{r['kind'].upper()}]{tag} Item {r['item']}, FY{r['source_fy']} 10-K, {pg}  score {r['score']}  signals: {', '.join(r['signals']) or '-'}")
        if r["kind"] == "modified":
            lines.append(f"- Old: \"{r['old']}\"")
            lines.append(f"- New: \"{r['new']}\"")
            lines.append(f"- Diff: {r['inline']}")
        elif r["kind"] == "added":
            lines.append(f"- New language: \"{r['new']}\"")
        else:
            lines.append(f"- Dropped language: \"{r['old']}\"")
        if r.get("elsewhere"):
            which = "new" if r["kind"] == "removed" else "old"
            lines.append(f"- CAUTION: similar language exists elsewhere in the {which} filing (similarity {r['elsewhere_ratio']}): \"{r['elsewhere'][:300]}\"")
        lines.append("")
    return "\n".join(lines)
