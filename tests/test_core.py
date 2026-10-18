"""Run: python3 -m pytest tests/  (or python3 tests/test_core.py)"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fineprint.extract import parse_filing
from fineprint.diff import diff_sections
from fineprint.verify import verify_quote, seed_errors

FIX = ROOT / "fixtures" / "demo"


def setup_module(_=None):
    if not (FIX / "demo-20251231.htm").exists():
        subprocess.run([sys.executable, str(ROOT / "tests" / "make_fixture.py"), str(FIX)], check=True)


def test_sections_and_pages():
    setup_module()
    p = parse_filing(FIX / "demo-20251231.htm")
    assert set(p.sections) == {"1A", "7"}
    assert p.sections["1A"].page_start[1] == "2"      # printed folio read from the page foot
    assert "TABLE OF CONTENTS" not in p.sections["1A"].text


def test_diff_finds_known_edits():
    setup_module()
    old = parse_filing(FIX / "demo-20241231.htm"); new = parse_filing(FIX / "demo-20251231.htm")
    d = diff_sections(old.sections["1A"].text, new.sections["1A"].text, "1A")
    kinds = {(i.kind, (i.new or i.old)[:40]) for i in d.items}
    assert ("added", "Tariffs on imported pharmaceutical produ") in kinds
    assert ("removed", "We may be unable to protect our intellec") in kinds
    assert any(i.kind == "modified" and "38%" in i.new for i in d.items)


def test_gate_accepts_true_and_rejects_planted():
    setup_module()
    p = parse_filing(FIX / "demo-20251231.htm")
    good = "Gross-to-net adjustments were 45% of gross sales in 2025 compared to 41% in 2024."
    r = verify_quote(good, p)
    assert r.passed and r.section == "7" and r.page_folio == "5"
    for name, bad in seed_errors(good).items():
        assert not verify_quote(bad, p).passed, name
    # smart quotes / line wrap tolerance
    assert verify_quote("Gross‑to‑net adjustments were 45% of gross sales in 2025   compared to 41% in 2024.", p).passed
    # ellipsis
    assert verify_quote("Gross-to-net adjustments were 45% ... compared to 41% in 2024.", p).passed
    assert not verify_quote("compared to 41% in 2024 ... Gross-to-net adjustments were 45%", p).passed  # wrong order


if __name__ == "__main__":
    setup_module(); test_sections_and_pages(); test_diff_finds_known_edits(); test_gate_accepts_true_and_rejects_planted(); print("all tests passed")
