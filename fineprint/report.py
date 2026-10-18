"""Reviewer page: one self-contained, accessible HTML file per run.

Shows ranked candidates (and drafted findings when present) with the verbatim
quote, computed page, word-level diff and gate status. The reviewer approves or
rejects each item with a keyboard or mouse; decisions are kept in the browser
(localStorage) and exported as JSON for the errors log and the findings table.
No framework, no network, no tracking; works from a file:// URL.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#555;--line:#d8d8d8;--add:#0b6b2e;--addbg:#e6f6ea;--del:#9b1c1c;--delbg:#fbe9e9;--warn:#7a5a00;--warnbg:#fff6d6;--ok:#0b6b2e;--card:#fafafa;--focus:#1a56db}
@media (prefers-color-scheme: dark){:root{--bg:#121212;--fg:#ededed;--muted:#b5b5b5;--line:#3a3a3a;--add:#8fe3a8;--addbg:#10301b;--del:#ff9d9d;--delbg:#3a1414;--warn:#ffd166;--warnbg:#3a2f0b;--ok:#8fe3a8;--card:#1c1c1c;--focus:#8ab4f8}}
*{box-sizing:border-box}body{margin:0;font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:16px 20px;border-bottom:1px solid var(--line)}h1{font-size:1.35rem;margin:0 0 4px}h2{font-size:1.05rem;margin:0}
main{max-width:1100px;margin:0 auto;padding:16px 20px}
.summary{display:flex;gap:16px;flex-wrap:wrap;color:var(--muted);font-size:.95rem}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:12px 0}
button{font:inherit;padding:6px 12px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);cursor:pointer}
button:focus-visible,[tabindex]:focus-visible,a:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.card{border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:12px 0;background:var(--card)}
.card[data-decision=approved]{border-left:6px solid var(--ok)}.card[data-decision=rejected]{border-left:6px solid var(--del);opacity:.75}
.meta{display:flex;gap:10px;flex-wrap:wrap;font-size:.9rem;color:var(--muted)}
.tag{border:1px solid var(--line);border-radius:999px;padding:0 8px}
.kind-added{color:var(--add)}.kind-removed{color:var(--del)}.kind-modified{color:var(--warn)}
blockquote{margin:10px 0;padding:8px 12px;border-left:3px solid var(--line);background:var(--bg)}
ins{background:var(--addbg);color:var(--add);text-decoration:none}del{background:var(--delbg);color:var(--del)}
.caution{background:var(--warnbg);color:var(--warn);padding:6px 10px;border-radius:6px;margin-top:8px}
.gate-pass{color:var(--ok);font-weight:600}.gate-fail{color:var(--del);font-weight:600}
.decide{display:flex;gap:8px;align-items:center;margin-top:10px}.decide textarea{flex:1;min-height:34px;font:inherit;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
.sr{position:absolute;left:-9999px}kbd{border:1px solid var(--line);border-radius:4px;padding:0 4px;font-size:.85em}
footer{color:var(--muted);font-size:.9rem;padding:20px;border-top:1px solid var(--line);margin-top:24px}
"""

JS = """
const KEY='fineprint:'+document.body.dataset.run;
let state={}; try{state=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){state={}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){}}
function apply(){document.querySelectorAll('.card').forEach(c=>{const d=state[c.dataset.id]||{};c.dataset.decision=d.decision||'';const t=c.querySelector('textarea');if(t&&d.note!=null)t.value=d.note;const live=c.querySelector('.status');if(live)live.textContent=d.decision?('Marked '+d.decision):'';});
 const n=Object.values(state);document.getElementById('tally').textContent=n.filter(x=>x.decision==='approved').length+' approved, '+n.filter(x=>x.decision==='rejected').length+' rejected';}
function decide(id,decision){state[id]=Object.assign({},state[id]||{},{decision,at:new Date().toISOString()});save();apply();}
function note(id,v){state[id]=Object.assign({},state[id]||{},{note:v});save();}
function exportJSON(){const out=[];document.querySelectorAll('.card').forEach(c=>{const d=state[c.dataset.id];if(!d||!d.decision)return;out.push(Object.assign({id:c.dataset.id,kind:c.dataset.kind,item:c.dataset.item,page:c.dataset.page,quote:c.dataset.quote},d));});
 const blob=new Blob([JSON.stringify({run:document.body.dataset.run,exported:new Date().toISOString(),decisions:out},null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='decisions_'+document.body.dataset.run+'.json';a.click();}
function filter(){const q=document.getElementById('q').value.toLowerCase();const k=document.getElementById('kind').value;const hide=document.getElementById('hidecaution').checked;
 document.querySelectorAll('.card').forEach(c=>{const ok=(!q||c.textContent.toLowerCase().includes(q))&&(!k||c.dataset.kind===k)&&(!hide||!c.dataset.caution);c.hidden=!ok;});}
document.addEventListener('keydown',e=>{const c=document.activeElement.closest&&document.activeElement.closest('.card');if(!c||e.target.tagName==='TEXTAREA'||e.target.tagName==='INPUT')return;if(e.key==='a'){decide(c.dataset.id,'approved')}if(e.key==='r'){decide(c.dataset.id,'rejected')}if(e.key==='u'){delete state[c.dataset.id];save();apply();}});
apply();
"""


def _inline_to_html(inline: str) -> str:
    out = html.escape(inline)
    out = out.replace("[-", "<del>").replace("-]", "</del>").replace("{+", "<ins>").replace("+}", "</ins>")
    return out


def _card(i: int, r: dict, source: str) -> str:
    kind = r["kind"]
    pg = f"p. {r['page_folio']}" if r.get("page_folio") else f"page {r.get('page_index', '?')} (sequential)"
    quote = r["new"] if kind in ("added", "modified") else r["old"]
    tags = "".join(f'<span class="tag">{html.escape(s)}</span>' for s in r.get("signals", []))
    body = ""
    if kind == "modified":
        body = (f'<p><span class="sr">Old text:</span><blockquote>{html.escape(r["old"])}</blockquote>'
                f'<span class="sr">New text:</span><blockquote>{html.escape(r["new"])}</blockquote>'
                f'<p><strong>Word-level change</strong> (<del>removed</del>, <ins>added</ins>): {_inline_to_html(r["inline"])}</p>')
        if r.get("numbers_only"):
            body += '<p class="meta">Numbers roll-forward: only figures and years changed.</p>'
    elif kind == "added":
        body = f'<p><strong>New language</strong></p><blockquote>{html.escape(r["new"])}</blockquote>'
    else:
        body = f'<p><strong>Dropped language</strong> (present in the older filing only)</p><blockquote>{html.escape(r["old"])}</blockquote>'
    caution = ""
    if r.get("elsewhere"):
        which = "newer" if kind == "removed" else "older"
        caution = (f'<div class="caution" role="note">Caution: similar language exists elsewhere in the {which} filing '
                   f'(similarity {r["elsewhere_ratio"]}): <q>{html.escape(r["elsewhere"][:400])}</q></div>')
    cid = f"c{i}"
    return f'''
<article class="card" id="{cid}" tabindex="0" data-id="{cid}" data-kind="{kind}" data-item="{r['item']}" data-page="{html.escape(str(r.get('page_folio') or r.get('page_index')))}" data-quote="{html.escape(quote)}" {'data-caution="1"' if caution else ''} aria-labelledby="{cid}-h">
  <h2 id="{cid}-h"><span class="kind-{kind}">{i}. {kind.upper()}</span> &middot; Item {html.escape(r['item'])} &middot; FY{r['source_fy']} {html.escape(source)} &middot; {pg} &middot; score {r['score']}</h2>
  <div class="meta">{tags or '<span class="tag">no signal</span>'}</div>
  {body}{caution}
  <div class="decide">
    <button type="button" onclick="decide('{cid}','approved')" aria-label="Approve candidate {i}">Approve <kbd>a</kbd></button>
    <button type="button" onclick="decide('{cid}','rejected')" aria-label="Reject candidate {i}">Reject <kbd>r</kbd></button>
    <label class="sr" for="{cid}-n">Reviewer note</label>
    <textarea id="{cid}-n" placeholder="Reviewer note (why approved or rejected)" oninput="note('{cid}',this.value)"></textarea>
    <span class="status" aria-live="polite"></span>
  </div>
</article>'''


def _finding_card(i: int, f: dict) -> str:
    v = f.get("verification", {})
    ok = f.get("status") == "verified"
    gate = (f'<span class="gate-pass">GATE PASS</span> ({v.get("status")}, Item {v.get("section") or "?"}, p. {f.get("page_computed")})'
            if ok else f'<span class="gate-fail">GATE REJECT</span> ({v.get("status")}, similarity {v.get("score")})')
    cand = f'<p><strong>Closest real sentence:</strong> <q>{html.escape(v.get("candidate", "")[:400])}</q></p>' if not ok and v.get("candidate") else ""
    mism = f'<div class="caution" role="note">Model said page {html.escape(str(f.get("page")))}; computed page is {html.escape(str(f.get("page_computed")))}.</div>' if f.get("page_mismatch") else ""
    cid = f"f{i}"
    return f'''
<article class="card" id="{cid}" tabindex="0" data-id="{cid}" data-kind="finding" data-item="{html.escape(str(f.get('item')))}" data-page="{html.escape(str(f.get('page_computed') or f.get('page')))}" data-quote="{html.escape(f['quote'])}" aria-labelledby="{cid}-h">
  <h2 id="{cid}-h">Finding {i}: {html.escape(f['finding'])}</h2>
  <div class="meta"><span class="tag">confidence: {html.escape(f.get('confidence', '?'))}</span><span class="tag">quote from {html.escape(f.get('quote_source', '?'))} filing</span> {gate}</div>
  <blockquote>{html.escape(f['quote'])}</blockquote>
  <p><strong>Why it matters:</strong> {html.escape(f.get('why_it_matters', ''))}</p>
  <p><strong>Impact hypothesis:</strong> {html.escape(f.get('impact_hypothesis', ''))}</p>
  {cand}{mism}
  <div class="decide">
    <button type="button" onclick="decide('{cid}','approved')" aria-label="Approve finding {i}">Approve <kbd>a</kbd></button>
    <button type="button" onclick="decide('{cid}','rejected')" aria-label="Reject finding {i}">Reject <kbd>r</kbd></button>
    <label class="sr" for="{cid}-n">Reviewer note</label>
    <textarea id="{cid}-n" placeholder="Reviewer note" oninput="note('{cid}',this.value)"></textarea>
    <span class="status" aria-live="polite"></span>
  </div>
</article>'''


def render(run_dir: str | Path, out: str | Path | None = None) -> Path:
    rd = Path(run_dir)
    cands = json.loads((rd / "candidates.json").read_text())
    summ = json.loads((rd / "summary.json").read_text())
    filings = json.loads((rd / "filings.json").read_text())
    findings = []
    fp = rd / "findings.json"
    if fp.exists():
        findings = json.loads(fp.read_text()).get("findings", [])
    ticker = summ.get("ticker") or "run"
    form = filings[-1].get("form", "10-K") if filings else "10-K"
    sec_lines = "".join(
        f"<li>Item {it}: {s['old_sentences']} &rarr; {s['new_sentences']} sentences; {s['added']} added, {s['removed']} removed, {s['modified']} modified, {s['unchanged']} unchanged</li>"
        for it, s in summ["sections"].items())
    n_ok = sum(f.get("status") == "verified" for f in findings)
    findings_html = ""
    if findings:
        findings_html = (f'<section aria-labelledby="fh"><h2 id="fh" style="font-size:1.2rem;margin-top:24px">Drafted findings: {n_ok} of {len(findings)} passed the gate</h2>'
                         + "".join(_finding_card(i, f) for i, f in enumerate(findings, 1)) + "</section>")
    cards = "".join(_card(i, r, form) for i, r in enumerate(cands, 1))
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FinePrint review: {html.escape(ticker)} FY{summ['old']} to FY{summ['new']}</title><style>{CSS}</style></head>
<body data-run="{html.escape(ticker)}_{summ['old']}_{summ['new']}">
<header><h1>FinePrint review: {html.escape(ticker)} {html.escape(form)} FY{summ['old']} &rarr; FY{summ['new']}</h1>
<div class="summary"><span>Old: {html.escape(filings[-2]['url'] if len(filings) > 1 else '')}</span><span>New: {html.escape(filings[-1]['url'] if filings else '')}</span><span>Generated {datetime.now().strftime('%b %d, %Y %I:%M %p')}</span></div></header>
<main>
<ul>{sec_lines}</ul>
<p>Every quote below is copied verbatim from the filing; page numbers are computed from the document, not generated. Items are candidates for a human reader, ranked by "where findings hide" signals. Keyboard: focus a card, then <kbd>a</kbd> approve, <kbd>r</kbd> reject, <kbd>u</kbd> undo. Decisions stay in this browser until exported.</p>
<div class="controls" role="group" aria-label="Filters and export">
  <label>Search <input id="q" type="search" oninput="filter()" aria-label="Search candidates"></label>
  <label>Kind <select id="kind" onchange="filter()"><option value="">all</option><option value="added">added</option><option value="removed">removed</option><option value="modified">modified</option><option value="finding">findings</option></select></label>
  <label><input id="hidecaution" type="checkbox" onchange="filter()"> hide items with a caution</label>
  <button type="button" onclick="exportJSON()">Export decisions (JSON)</button>
  <span id="tally" aria-live="polite"></span>
</div>
{findings_html}
<section aria-labelledby="ch"><h2 id="ch" style="font-size:1.2rem;margin-top:24px">Ranked candidates ({len(cands)})</h2>{cards}</section>
</main>
<footer>FinePrint. Source documents are public SEC filings; no personal data is processed. The gate verifies that a quote exists and where; it does not verify an interpretation. That is the reviewer's job.</footer>
<script>{JS}</script></body></html>'''
    dest = Path(out) if out else rd / "review.html"
    dest.write_text(page)
    return dest
