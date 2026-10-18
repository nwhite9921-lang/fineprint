"""EDGAR fetch: ticker -> CIK -> last N annual reports -> primary document saved locally.

Uses only documented SEC endpoints:
  https://www.sec.gov/files/company_tickers.json      ticker -> CIK
  https://data.sec.gov/submissions/CIK##########.json  filing index
  https://www.sec.gov/Archives/edgar/data/<cik>/<acc>/<primary_doc>

SEC fair-access rules: declare a User-Agent with contact info and stay under
10 requests/second. See https://www.sec.gov/os/accessing-edgar-data
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

import requests

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SEC_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"

DEFAULT_UA = os.environ.get("FINEPRINT_USER_AGENT", "FinePrint research tool contact@example.com")
MIN_INTERVAL_S = 0.15  # ~6 req/s, under the SEC's 10 req/s limit


@dataclass
class Filing:
    ticker: str
    cik: int
    form: str
    filing_date: str      # YYYY-MM-DD
    report_date: str      # fiscal period end, YYYY-MM-DD
    accession: str        # 0001551152-25-000007
    primary_doc: str      # abbv-20241231.htm
    url: str
    local_path: str = ""

    @property
    def fiscal_year(self) -> str:
        return (self.report_date or self.filing_date)[:4]


class EdgarClient:
    def __init__(self, user_agent: str = DEFAULT_UA, cache_dir: str | Path = "cache"):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._last = 0.0

    # -- polite GET ---------------------------------------------------------
    def _get(self, url: str, **kw) -> requests.Response:
        wait = MIN_INTERVAL_S - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        r = self.session.get(url, timeout=60, **kw)
        self._last = time.time()
        r.raise_for_status()
        return r

    # -- ticker -> CIK ------------------------------------------------------
    def cik_for_ticker(self, ticker: str) -> int:
        path = self.cache_dir / "company_tickers.json"
        if not path.exists() or time.time() - path.stat().st_mtime > 7 * 86400:
            path.write_bytes(self._get(SEC_TICKERS_URL).content)
        data = json.loads(path.read_text())
        t = ticker.upper().strip()
        for row in data.values():
            if row["ticker"].upper() == t:
                return int(row["cik_str"])
        raise LookupError(f"Ticker {ticker!r} not found in SEC company_tickers.json")

    # -- filing index -------------------------------------------------------
    def submissions(self, cik: int) -> dict:
        return self._get(SEC_SUBMISSIONS_URL.format(cik=cik)).json()

    def list_filings(self, ticker: str, forms: Iterable[str] = ("10-K",), limit: int = 2) -> list[Filing]:
        """Most recent `limit` filings of the given form types (10-K excludes 10-K/A by default)."""
        cik = self.cik_for_ticker(ticker)
        sub = self.submissions(cik)
        recent = sub["filings"]["recent"]
        out: list[Filing] = []
        wanted = set(forms)
        for i, form in enumerate(recent["form"]):
            if form not in wanted:
                continue
            acc = recent["accessionNumber"][i]
            doc = recent["primaryDocument"][i]
            out.append(Filing(
                ticker=ticker.upper(), cik=cik, form=form,
                filing_date=recent["filingDate"][i],
                report_date=recent.get("reportDate", [""] * len(recent["form"]))[i],
                accession=acc, primary_doc=doc,
                url=SEC_ARCHIVE_URL.format(cik=cik, acc_nodash=acc.replace("-", ""), doc=doc),
            ))
            if len(out) >= limit:
                break
        if len(out) < limit:
            raise LookupError(f"Only {len(out)} {sorted(wanted)} filings found for {ticker}; need {limit}")
        return out

    # -- download -----------------------------------------------------------
    def download(self, filing: Filing) -> Filing:
        dest_dir = self.cache_dir / filing.ticker
        dest_dir.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", filing.primary_doc)
        dest = dest_dir / f"{filing.form.replace('/', '')}_{filing.fiscal_year}_{safe}"
        if not dest.exists():
            dest.write_bytes(self._get(filing.url).content)
        filing.local_path = str(dest)
        (dest_dir / f"{dest.stem}.meta.json").write_text(json.dumps(asdict(filing), indent=2))
        return filing

    def fetch_last_10ks(self, ticker: str, n: int = 2) -> list[Filing]:
        return [self.download(f) for f in self.list_filings(ticker, ("10-K",), n)]


def local_filing(path: str | Path, ticker: str = "LOCAL", form: str = "10-K", fiscal_year: str = "") -> Filing:
    """Wrap an already-downloaded primary document (e.g. uploaded by a teammate) as a Filing.
    Fiscal year is read from the filename if it looks like <name>-YYYYMMDD.htm, else from `fiscal_year`."""
    p = Path(path)
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", p.name)
    if m:
        report_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    elif fiscal_year:
        report_date = f"{fiscal_year}-12-31"
    else:
        fy = re.search(r"fy[_-]?(20\d{2})", p.name, re.I)
        if not fy:  # read the cover page: "For the fiscal year ended December 31, 2025"
            head = p.read_bytes()[:200000].decode("utf-8", "replace")
            head = re.sub(r"<[^>]+>", " ", head)
            fy = re.search(r"fiscal\s+year\s+ended\s+[A-Za-z]+\s+\d{1,2},?\s+(20\d{2})", head, re.I)
        report_date = f"{fy.group(1)}-12-31" if fy else ""
    return Filing(ticker=ticker.upper(), cik=0, form=form, filing_date="", report_date=report_date,
                  accession="", primary_doc=p.name, url=f"file://{p.resolve()}", local_path=str(p))
