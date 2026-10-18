"""AI drafting step: turn ranked diff candidates into draft findings, then push
every draft through the verification gate. The model never gets the last word:
a finding whose quote does not string-match the filing is rejected and logged.

Usage
  python -m fineprint draft --run runs/ABBV --filing new.pdf --out runs/ABBV/findings.json
  python -m fineprint draft --run runs/ABBV --prompt-only      # write the prompt pack, no API call

Needs ANTHROPIC_API_KEY (or an `ant auth login` profile) and `pip install anthropic`.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

MODEL = os.environ.get("FINEPRINT_MODEL", "claude-opus-5-5")

SYSTEM = """You are a forensic equity analyst reading year-over-year changes in a company's annual report.
You will receive ranked excerpts of changed language (added, removed, modified sentences) from Item 1A
Risk Factors and Item 7 MD&A, each with a computed page number. Draft candidate findings.

Rules, all of them hard:
- Every finding must carry ONE verbatim quote copied character for character from the NEW or OLD text
  shown in the excerpt. Do not paraphrase, shorten, merge, or fix typos inside a quote. A quote that is
  not an exact copy will be rejected automatically and counted as an error.
- Do not invent numbers, page numbers, or facts not in the excerpts. The page number is given to you;
  copy it. If an impact cannot be computed from the excerpt, write what WOULD need to be known.
- Prefer dropped language and softened or hardened verbs over routine number roll-forwards.
- Say why a change matters in one sentence, in plain language, as a hypothesis for a human to check.
- Confidence: high only when the quote itself states the fact; medium when inference is needed; low when speculative."""

SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "finding": {"type": "string", "description": "One sentence."},
                    "why_it_matters": {"type": "string"},
                    "quote": {"type": "string", "description": "Verbatim from the excerpt."},
                    "quote_source": {"type": "string", "enum": ["new", "old"]},
                    "item": {"type": "string"},
                    "page": {"type": "string"},
                    "candidate_number": {"type": "integer"},
                    "impact_hypothesis": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["finding", "why_it_matters", "quote", "quote_source", "item", "page",
                             "candidate_number", "impact_hypothesis", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["findings"],
    "additionalProperties": False,
}


def build_prompt(run_dir: Path, top: int = 40) -> str:
    cands = json.loads((run_dir / "candidates.json").read_text())[:top]
    summ = json.loads((run_dir / "summary.json").read_text())
    lines = [f"Company: {summ.get('ticker')}. Old filing FY{summ['old']}, new filing FY{summ['new']}.",
             "Ranked changed-language excerpts follow. 'page' is the printed page in the filing the sentence comes from.", ""]
    for i, c in enumerate(cands, 1):
        pg = c["page_folio"] or str(c["page_index"])
        lines.append(f"### Candidate {i} | {c['kind'].upper()} | Item {c['item']} | FY{c['source_fy']} filing | page {pg} | signals: {', '.join(c['signals']) or '-'}")
        if c["kind"] == "modified":
            lines.append(f"OLD: {c['old']}")
            lines.append(f"NEW: {c['new']}")
        elif c["kind"] == "added":
            lines.append(f"NEW: {c['new']}")
        else:
            lines.append(f"OLD (dropped in the new filing): {c['old']}")
        lines.append("")
    lines.append(f"Draft up to 12 findings. Rank by materiality to revenue, operating income or EPS.")
    return "\n".join(lines)


def call_model(prompt: str) -> dict:
    import anthropic  # optional dependency
    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise SystemExit("model declined the request (stop_reason=refusal)")
    text = next(b.text for b in msg.content if b.type == "text")
    data = json.loads(text)
    data["_meta"] = {"model": msg.model, "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens,
                     "at": datetime.now().isoformat(timespec="seconds")}
    return data


def gate(findings: list[dict], filing_new, filing_old, errors_log: Path | None) -> list[dict]:
    """Verify every quote against the filing it claims to come from; annotate; log rejections."""
    from .verify import verify_quote
    out, rejected = [], []
    for f in findings:
        filing = filing_old if (f.get("quote_source") == "old" and filing_old) else filing_new
        r = verify_quote(f["quote"], filing)
        f["verification"] = r.to_dict()
        f["status"] = "verified" if r.passed else "REJECTED"
        if r.passed:
            f["page_computed"] = r.page_folio or str(r.page_index)
            f["page_mismatch"] = bool(f.get("page")) and f["page"] != f["page_computed"]
        else:
            rejected.append(f)
        out.append(f)
    if errors_log and rejected:
        with errors_log.open("a") as fh:
            for f in rejected:
                v = f["verification"]
                fh.write(f"| auto | {datetime.now().strftime('%b %d, %I:%M %p')} | FinePrint draft gate | "
                         f"Model quoted: \"{f['quote'][:140]}\" | {('Closest real sentence: ' + v['candidate'][:140]) if v['candidate'] else 'No such sentence in the filing'} "
                         f"| Verification gate ({v['status']}, {v['score']}) | Finding rejected: {f['finding'][:100]} |\n")
    return out


def run_draft(run_dir: str, filing_new: str | None, filing_old: str | None, out: str | None,
              prompt_only: bool, top: int, errors_log: str | None) -> dict:
    rd = Path(run_dir)
    prompt = build_prompt(rd, top)
    (rd / "draft_prompt.md").write_text(SYSTEM + "\n\n---\n\n" + prompt)
    if prompt_only:
        return {"prompt": str(rd / "draft_prompt.md"), "note": "no API call made"}
    data = call_model(prompt)
    findings = data["findings"]
    if filing_new:
        from .extract import parse_filing
        fn = parse_filing(filing_new)
        fo = parse_filing(filing_old) if filing_old else None
        findings = gate(findings, fn, fo, Path(errors_log) if errors_log else None)
    dest = Path(out) if out else rd / "findings.json"
    dest.write_text(json.dumps({"findings": findings, "_meta": data.get("_meta", {})}, indent=2))
    n_ok = sum(f.get("status") == "verified" for f in findings)
    return {"findings": len(findings), "verified": n_ok, "rejected": len(findings) - n_ok, "out": str(dest),
            "model": data.get("_meta", {}).get("model")}
