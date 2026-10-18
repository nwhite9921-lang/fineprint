"""Build two synthetic 10-K-style HTML documents (FY1, FY2) in the shape EDGAR
inline-XBRL filings take: cover, table of contents, page breaks with printed
folios, Items 1, 1A, 1B, 7, 7A, 8. FY2 edits Risk Factors and MD&A so the
diff has known answers. Used only to test the parser; not a real filing."""
import sys
from pathlib import Path

RF_1 = [
    "We depend on the continued success of a small number of products for a substantial portion of our net revenues.",
    "Our product Alpha accounted for approximately 32% of our total net revenues in 2024.",
    "Changes in government reimbursement, including the Inflation Reduction Act drug price negotiation program, may reduce the prices we receive.",
    "Competition from biosimilars could result in a decrease in the prices and sales volume of our products.",
    "We may be unable to protect our intellectual property, and patent litigation could be costly.",
    "Our effective tax rate could increase as a result of changes in tax laws, including Pillar Two.",
]
RF_2 = [
    "We depend on the continued success of a small number of products for a substantial portion of our net revenues.",
    "Our product Alpha accounted for approximately 38% of our total net revenues in 2025.",
    "Changes in government reimbursement, including the Inflation Reduction Act drug price negotiation program and most favored nation pricing arrangements, will reduce the prices we receive for certain products beginning in 2028.",
    "Competition from biosimilars could result in a decrease in the prices and sales volume of our products.",
    "Tariffs on imported pharmaceutical products could increase our cost of products sold.",
    "Our effective tax rate could increase as a result of changes in tax laws, including Pillar Two.",
]
MDA_1 = [
    "Net revenues increased 4% in 2024 driven by volume growth of Alpha, partially offset by higher rebates.",
    "Gross-to-net adjustments were 41% of gross sales in 2024 compared to 39% in 2023.",
    "Inventories increased 8% while net revenues increased 4%, reflecting the build of launch inventory.",
    "The change in fair value of contingent consideration liabilities resulted in a charge of $1.2 billion in 2024.",
    "We expect continued growth in 2025.",
]
MDA_2 = [
    "Net revenues increased 9% in 2025 driven by volume growth of Alpha, partially offset by higher rebates and unfavorable channel mix.",
    "Gross-to-net adjustments were 45% of gross sales in 2025 compared to 41% in 2024.",
    "Inventories increased 15% while net revenues increased 9%.",
    "The change in fair value of contingent consideration liabilities resulted in a charge of $2.4 billion in 2025, primarily related to higher projected Alpha revenues.",
    "Accounts receivable increased 14%, exceeding revenue growth, due to timing of wholesaler payments.",
]

def para(s):
    return f'<div style="margin-top:6pt"><span style="font-family:Times New Roman;font-size:10pt">{s}</span></div>'

def pagebreak(folio):
    return (f'<div style="text-align:center"><span style="font-size:10pt">{folio}</span></div>'
            f'<hr style="page-break-after:always"/>')

def heading(s):
    return f'<div><span style="font-weight:700;font-size:10pt">{s}</span></div>'

def build(fy, rf, mda):
    h = ['<?xml version="1.0"?><html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><head><title>x</title></head><body>',
         '<div style="display:none"><ix:header>hidden xbrl header Item 1A. Risk Factors</ix:header></div>',
         para(f"UNITED STATES SECURITIES AND EXCHANGE COMMISSION FORM 10-K For the fiscal year ended December 31, {fy}"),
         pagebreak("i"),
         heading("TABLE OF CONTENTS"),
         '<table>' + ''.join(f'<tr><td>Item {i}.</td><td>{t}</td><td>{p}</td></tr>' for i, t, p in
             [("1", "Business", 1), ("1A", "Risk Factors", 2), ("1B", "Unresolved Staff Comments", 4),
              ("7", "Management&#8217;s Discussion and Analysis of Financial Condition and Results of Operations", 5),
              ("7A", "Quantitative and Qualitative Disclosures About Market Risk", 7), ("8", "Financial Statements and Supplementary Data", 8)]) + '</table>',
         pagebreak("ii"),
         heading("PART I"), heading("ITEM 1. BUSINESS"),
         para("The company discovers, develops and sells medicines. See Item 1A, &#8220;Risk Factors,&#8221; for a discussion of risks. " * 20),
         pagebreak("1"),
         heading("ITEM 1A. RISK FACTORS")]
    for i, s in enumerate(rf):
        h.append(para(s + " " + ("Additional explanatory language follows. " * 12)))
        if i == 2:
            h.append(pagebreak("2"))
    h += [pagebreak("3"), heading("ITEM 1B. UNRESOLVED STAFF COMMENTS"), para("None."), pagebreak("4"),
          heading("PART II"), heading("ITEM 7. MANAGEMENT&#8217;S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS")]
    for i, s in enumerate(mda):
        h.append(para(s + " " + ("Further discussion of the drivers follows. " * 12)))
        if i == 1:
            h.append(pagebreak("5"))
    h += ['<table><tr><td>Alpha</td><td>$ 12,345</td><td>$ 10,100</td><td>22 %</td></tr><tr><td>Beta</td><td>$ 2,000</td><td>$ 2,100</td><td>(5) %</td></tr></table>',
          pagebreak("6"), heading("ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK"), para("Interest rate risk discussion. " * 10),
          pagebreak("7"), heading("ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA"), para("Financial statements. " * 50), pagebreak("8"),
          '</body></html>']
    return "\n".join(h)

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
(out / "demo-20241231.htm").write_text(build(2024, RF_1, MDA_1))
(out / "demo-20251231.htm").write_text(build(2025, RF_2, MDA_2))
print("wrote", out)
