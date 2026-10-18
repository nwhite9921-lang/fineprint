"""CLI.

  python -m fineprint run ABBV --out runs/ABBV            # fetch last two 10-Ks from EDGAR and diff
  python -m fineprint run --local old.htm new.htm --out runs/X --ticker X
  python -m fineprint verify --filing new.htm --quote "..."
  python -m fineprint verify --filing new.htm --findings findings.json --log verification_log.json
  python -m fineprint seed-test --filing new.htm --quote "..."   # show the gate rejecting planted errors
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .extract import parse_filing
from .verify import verify_quote, seed_errors


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fineprint")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="fetch (or load) two 10-Ks, extract Items 1A and 7, diff, rank candidates")
    r.add_argument("ticker", nargs="?")
    r.add_argument("--local", nargs="+", help="two already-downloaded primary documents (old new)")
    r.add_argument("--out", required=True)
    r.add_argument("--ticker", dest="ticker_opt", help="label for --local runs")
    r.add_argument("--cache", default="cache")
    r.add_argument("--user-agent", default=None, help="SEC requires 'Name contact@email' in the User-Agent")
    r.add_argument("--items", default="1A,7")
    r.add_argument("--top", type=int, default=40)

    v = sub.add_parser("verify", help="check quotes against a filing; exit 1 if any fail")
    v.add_argument("--filing", required=True)
    v.add_argument("--quote", action="append", default=[])
    v.add_argument("--findings", help="JSON list of {finding, quote, ...}")
    v.add_argument("--log", default=None, help="append results to this JSON log")

    s = sub.add_parser("seed-test", help="plant errors in a correct quote and show the gate catching them")
    s.add_argument("--filing", required=True)
    s.add_argument("--quote", required=True)

    d = sub.add_parser("draft", help="AI-draft findings from a run's candidates, then verify every quote")
    d.add_argument("--run", required=True, help="output dir of a previous `run`")
    d.add_argument("--filing", help="new-year filing to verify quotes against")
    d.add_argument("--old-filing", help="old-year filing, for quotes of dropped language")
    d.add_argument("--out", help="findings.json path (default: <run>/findings.json)")
    d.add_argument("--top", type=int, default=40)
    d.add_argument("--errors-log", help="markdown errors log to append rejections to")
    d.add_argument("--prompt-only", action="store_true", help="write the prompt pack and stop (no API call)")

    rp = sub.add_parser("report", help="render the reviewer page (review.html) for a run")
    rp.add_argument("--run", required=True)
    rp.add_argument("--out")

    x = sub.add_parser("sections", help="extract and print section locations for a filing")
    x.add_argument("filing")

    a = ap.parse_args(argv)

    if a.cmd == "run":
        from .pipeline import run
        a.ticker = a.ticker or a.ticker_opt
        if not a.ticker and not a.local:
            ap.error("give a ticker or --local old.htm new.htm")
        items = tuple(i.strip().upper() for i in a.items.split(","))
        summ = run(a.ticker, a.out, a.local, a.cache, a.user_agent, items, a.top)
        print(json.dumps(summ, indent=2))
        print(f"\nCandidates written to {Path(a.out) / 'candidates.md'}")
        return 0

    if a.cmd == "draft":
        from .draft import run_draft
        print(json.dumps(run_draft(a.run, a.filing, a.old_filing, a.out, a.prompt_only, a.top, a.errors_log), indent=2))
        return 0

    if a.cmd == "report":
        from .report import render
        print("wrote", render(a.run, a.out))
        return 0

    if a.cmd == "sections":
        p = parse_filing(a.filing, ("1", "1A", "7", "8"))
        print(f"{len(p.text):,} chars, {len(p.page_map.break_offsets)} page breaks, folios read on {len(p.page_map.folios)} pages")
        for it, sec in p.sections.items():
            print(f"Item {it:<3} {sec.title:<45} chars {sec.start:>9,}-{sec.end:<9,} pages {sec.page_start} -> {sec.page_end}")
        return 0

    if a.cmd == "verify":
        p = parse_filing(a.filing)
        findings = [{"quote": q} for q in a.quote]
        if a.findings:
            findings += json.loads(Path(a.findings).read_text())
        results, bad = [], 0
        for f in findings:
            res = verify_quote(f["quote"], p)
            row = {**{k: v for k, v in f.items() if k != "quote"}, **res.to_dict(), "filing": a.filing}
            results.append(row)
            bad += not res.passed
            tag = "PASS" if res.passed else "REJECT"
            where = f"Item {res.section or '?'} p.{res.page_index}" + (f" [{res.page_folio}]" if res.page_folio else "")
            print(f"{tag:<6} {res.status:<10} {where:<22} {f['quote'][:90]!r}")
            if not res.passed and res.candidate:
                print(f"       closest ({res.score}): {res.candidate[:160]!r}")
        if a.log:
            lp = Path(a.log)
            old = json.loads(lp.read_text()) if lp.exists() else []
            lp.write_text(json.dumps(old + results, indent=2))
        print(f"\n{len(results) - bad} passed, {bad} rejected")
        return 1 if bad else 0

    if a.cmd == "seed-test":
        p = parse_filing(a.filing)
        base = verify_quote(a.quote, p)
        print(f"original : {'PASS' if base.passed else 'REJECT'} ({base.status})")
        for name, bad in seed_errors(a.quote).items():
            res = verify_quote(bad, p)
            print(f"{name:<24}: {'PASS' if res.passed else 'REJECT'} ({res.status}, {res.score})  {bad[:100]!r}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
