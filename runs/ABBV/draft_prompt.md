You are a forensic equity analyst reading year-over-year changes in a company's annual report.
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
- Confidence: high only when the quote itself states the fact; medium when inference is needed; low when speculative.

---

Company: ABBV. Old filing FY2024, new filing FY2025.
Ranked changed-language excerpts follow. 'page' is the printed page in the filing the sentence comes from.

### Candidate 1 | MODIFIED | Item 7 | FY2025 filing | page 35 | signals: contingent_consideration, litigation, impairment
OLD: Diluted earnings per share in 2024 was $2.39 and included the following after-tax costs: (i) $6.5 billion related to the amortization of intangible assets; (ii) $3.7 billion for the change in fair value of contingent consideration liabilities; (iii) $3.5 billion related to intangible asset impairment; (iv) $978 million of acquisition and integration expenses; and (v) $721 million for charges related to litigation matters.
NEW: Financial results for 2025 also included the following costs: (i) $7.4 billion related to the amortization of intangible assets; (ii) $6.5 billion for the change in fair value of contingent consideration liabilities; (iii) $847 million related to intangible asset impairment; and (iv) $276 million of acquisition and integration expenses.

### Candidate 2 | REMOVED | Item 7 | FY2024 filing | page 42 | signals: contingent_consideration, segment_reclass, impairment
OLD (dropped in the new filing): The effective income tax rate in 2023 was higher than prior periods due to increased changes in fair value of contingent consideration, intangible asset impairments and the impacts of the transition from the Puerto Rico excise tax to an income tax.

### Candidate 3 | MODIFIED | Item 7 | FY2025 filing | page 43 | signals: contingent_consideration, tax
OLD: The lower effective income tax rate in 2024 also reflects an increase due to acquisition costs related to certain business development activities and a decrease related to changes in fair value of contingent consideration.
NEW: The effective income tax rate in 2025 was higher than 2024 primarily due to a one-time tax benefit associated with the closing of a three-year U.S. IRS examination in 2024, partially offset by decreases in unrecognized tax benefits, a decrease in the impact of acquisition costs related to certain business development activities and a decrease related to the impact of changes in fair value of contingent consideration.

### Candidate 4 | MODIFIED | Item 7 | FY2025 filing | page 44 | signals: contingent_consideration, litigation
OLD: FINANCIAL POSITION, LIQUIDITY AND CAPITAL RESOURCES years ended December 31 (in millions) 2024 2023 2022 Cash flows provided by (used in) Operating activities $ 18,806 $ 22,839 $ 24,943 Investing activities (20,820) (2,009) (623) Financing activities (5,211) (17,222) (24,803) Operating cash flows in 2024 decreased compared to the prior year primarily due to the timing of working capital and higher contingent consideration payments classified as operating cash flows, partially offset by increased results from operations driven by higher net revenues.
NEW: FINANCIAL POSITION, LIQUIDITY AND CAPITAL RESOURCES years ended December 31 (in millions) 2025 2024 2023 Cash flows provided by (used in) Operating activities $ 19,030 $ 18,806 $ 22,839 Investing activities (6,643) (20,820) (2,009) Financing activities (12,724) (5,211) (17,222) Operating cash flows in 2025 increased compared to the prior year primarily due to increased results from operations driven by higher net revenues, timing of working capital and lower acquisition-related cash expenses, partially offset by higher payments related to litigation matters and higher payments of contingent consideration liabilities.

### Candidate 5 | MODIFIED | Item 1A | FY2025 filing | page 16 | signals: gross_to_net, medicare_negotiation
OLD: Under the IRA, the U.S Department of Health and Human Services can effectively set prices for certain single-source drugs and biologics reimbursed under Medicare Part B and Part D. Generally, these government prices can apply as soon as nine years (for small-molecule drugs) or 13 years (for biological products) from their FDA approval and will be capped at a statutory ceiling price that is likely to represent a significant discount from average prices to wholesalers and direct purchasers.
NEW: Under the IRA, HHS can effectively set prices for certain single-source drugs and biologics reimbursed under Medicare Part B and Part D. Generally, these government prices can apply as soon as nine years (for small-molecule drugs) or 13 years (for biological products) from their FDA approval and will be capped at a statutory ceiling price that is likely to represent a significant discount from average prices to wholesalers and direct purchasers.

### Candidate 6 | REMOVED | Item 7 | FY2024 filing | page 42 | signals: tax, segment_reclass
OLD (dropped in the new filing): The effective income tax rate in 2024 was lower than prior periods due to the resolutions of various tax positions pertaining to multiple prior tax years, including the closing of U.S. IRS examinations covering three tax years, partially offset by increases in unrecognized tax benefits pertaining to prior years.

### Candidate 7 | ADDED | Item 1A | FY2025 filing | page 21 | signals: gross_to_net, litigation
NEW: Adverse outcomes in 340B-related litigation or significant changes to our 340B approach could adversely affect our revenues and results of operations.

### Candidate 8 | MODIFIED | Item 1A | FY2025 filing | page 17 | signals: medicare_negotiation
OLD: In January 2025, HHS, through the CMS, selected Vraylar and Linzess as two of the 15 medicines subject to government-set prices in Medicare Part D beginning in 2027.
NEW: In January 2026, Botox was selected as one of 15 medicines subject to government-set prices in Medicare Parts B and D beginning January 1, 2028.

### Candidate 9 | ADDED | Item 1A | FY2025 filing | page 17 | signals: medicare_negotiation, mfn_tariff
NEW: In addition to the pricing mechanisms established under the IRA, governments and other payers may pursue or implement additional approaches intended to reduce pharmaceutical costs, including arrangements or frameworks that reference international prices, most-favored-nation (MFN) concepts, or other comparative pricing methodologies.

### Candidate 10 | ADDED | Item 1A | FY2025 filing | page 17 | signals: gross_to_net, pipeline_dependency
NEW: A limited number of these entities negotiate pricing, rebates and patient access terms on behalf of health plans and government programs that cover a significant portion of insured patients in the United States.

### Candidate 11 | ADDED | Item 1A | FY2025 filing | page 18 | signals: gross_to_net, litigation
NEW: PBM business practices, rebate structures and pricing arrangements are also subject to change as a result of enforcement actions, regulatory settlements, legislation or other government actions.

### Candidate 12 | MODIFIED | Item 7 | FY2025 filing | page 34 | signals: patent_exclusivity
OLD: AbbVie expects to achieve its strategic objectives through: • Maximizing revenue growth of our key on-market products, including Skyrizi, Rinvoq, Venclexta, Elahere, Vraylar, Ubrelvy, Qulipta, Vyalev/Produodopa, Botox and Juvederm Collection. • Advancing our research and development pipeline by delivering late-stage pipeline milestones, achieving key proof-of-concept objectives across therapeutic areas and continuing to invest in key on-market product indication expansion. • Maximizing the value of key acquisitions as well as continuing to invest in external innovation. • Continuing to effectively manage the impact of Humira biosimilar erosion. • The favorable impact of pipeline products and indications recently approved or currently under regulatory review where approval is expected in 2025.
NEW: AbbVie expects to achieve its strategic objectives through: • Maximizing revenue growth of our key on-market products, including Skyrizi, Rinvoq, Vraylar, Botox Therapeutic, Ubrelvy, Qulipta, Vyalev, Venclexta, Elahere, Botox Cosmetic and Juvederm Collection. • Advancing our research and development pipeline by delivering late-stage pipeline milestones, achieving key proof-of-concept objectives across therapeutic areas and continuing to invest in key on- market product indication expansion. • Maximizing the value of key acquisitions as well as continuing to invest in external innovation. • The favorable impact of pipeline products and indications recently approved or currently under regulatory review where approval is expected in 2026.

### Candidate 13 | MODIFIED | Item 7 | FY2025 filing | page 41 | signals: patent_exclusivity
OLD: In the United States, Humira sales decreased 41% in 2024 primarily driven by direct biosimilar competition following loss of exclusivity on January 31, 2023.
NEW: Net revenues for Humira decreased 49% in 2025 primarily driven by continued impact of direct biosimilar competition following the loss of exclusivity.

### Candidate 14 | MODIFIED | Item 7 | FY2025 filing | page 41 | signals: patent_exclusivity
OLD: Internationally, Humira revenues decreased 13% in 2024 primarily driven by the continued impact of direct biosimilar competition.
NEW: Net revenues for Botox Therapeutic increased 15% in 2025 primarily driven by market growth as well as continued market share uptake.

### Candidate 15 | MODIFIED | Item 7 | FY2025 filing | page 42 | signals: working_capital
OLD: In the United States, Botox Cosmetic net revenues increased 1% primarily driven by favorable pricing, partially offset by the unfavorable impact of customer inventory destocking and decreased consumer demand.
NEW: In the United States, Botox Cosmetic net revenues decreased 11% primarily driven by unfavorable pricing due to customer loyalty program changes, lower market share and decreased consumer demand, partially offset by the timing of customer inventory destocking in the prior year.

### Candidate 16 | MODIFIED | Item 7 | FY2025 filing | page 42 | signals: working_capital
OLD: Net revenues for Juvederm Collection decreased 12% in 2024 primarily driven by the unfavorable impact of decreased consumer demand and customer inventory destocking.
NEW: Net revenues for Juvederm Collection decreased 15% in 2025 primarily driven by decreased consumer demand, partially offset by the timing of customer inventory destocking in the prior year.

### Candidate 17 | MODIFIED | Item 7 | FY2025 filing | page 42 | signals: impairment
OLD: Gross margin percentage for 2024 was favorably impacted by lower intangible asset impairment charges and lower amortization of intangibles.
NEW: R&D expense percentage for 2025 was favorably impacted by lower intangible asset impairment charges.

### Candidate 18 | MODIFIED | Item 7 | FY2025 filing | page 47 | signals: gross_to_net
OLD: (in millions) Medicaid and Medicare Rebates Managed Care Rebates Wholesaler Chargebacks Balance as of December 31, 2021 $ 3,816 $ 3,097 $ 902 Provisions 11,713 14,119 13,070 Payments (10,331) (12,974) (12,829) Balance as of December 31, 2022 5,198 4,242 1,143 Provisions 15,153 23,978 14,191 Payments (15,054) (21,200) (14,162) Balance as of December 31, 2023 5,297 7,020 1,172 Provisions 15,866 24,127 14,782 Payments (13,756) (25,622) (14,797) Balance as of December 31, 2024 $ 7,407 $ 5,525 $ 1,157 Other Allowances Other allowances include cash discounts, product returns, sales incentives and other adjustments, which are accounted for as variable consideration and are recorded as a reduction to revenue in the same period the related product is sold.
NEW: (in millions) Medicaid and Medicare RebatesManaged Care Rebates Wholesaler Chargebacks Balance as of December 31, 2022 $ 5,198 $ 4,242 $ 1,143 Provisions 15,153 23,978 14,191 Payments (15,054) (21,200) (14,162) Balance as of December 31, 2023 5,297 7,020 1,172 Provisions 15,866 24,127 14,782 Payments (13,756) (25,622) (14,797) Balance as of December 31, 2024 7,407 5,525 1,157 Provisions 21,283 22,307 17,710 Payments (21,250) (22,487) (17,482) Balance as of December 31, 2025 $ 7,440 $ 5,345 $ 1,385 Other Allowances Other allowances include cash discounts, product returns, sales incentives and other adjustments, which are accounted for as variable consideration and are recorded as a reduction to revenue in the same period the related product is sold.

### Candidate 19 | MODIFIED | Item 7 | FY2025 filing | page 43 | signals: contingent_consideration, litigation
OLD: The effective income tax rates in 2024, 2023 and 2022 differed from the statutory tax rate principally due to the impact of foreign operations with lower income tax rates in locations outside the United States, the U.S. global minimum tax, changes in fair value of contingent consideration, tax audits and settlements, tax credits and incentives in the United States, Puerto Rico and other foreign tax jurisdictions, and business development activities.
NEW: The effective income tax rates in 2025, 2024 and 2023 differed from the statutory tax rate principally due to the impact of foreign operations with lower income tax rates in locations outside the United States, the U.S. global minimum tax, changes in fair value of contingent consideration, tax audits and settlements, tax credits and incentives in the United States, Puerto Rico and other foreign tax jurisdictions, and business development activities.

### Candidate 20 | MODIFIED | Item 7 | FY2025 filing | page 35 | signals: medicare_negotiation
OLD: Regulation The Inflation Reduction Act of 2022 has and will continue to have a significant impact on how drugs are covered and paid for under the Medicare program, including through the creation of financial penalties for drugs whose price increases outpace inflation, the redesign of Medicare Part D benefits to shift a greater portion of the costs to manufacturers, and through government price-setting for certain Medicare Part B and Part D drugs.
NEW: The Inflation Reduction Act of 2022 has and will continue to have a significant impact on how drugs are covered and paid for under the Medicare program, including through the creation of financial penalties for drugs whose price increases outpace inflation, the redesign of Medicare Part D benefits to shift a greater portion of the costs to manufacturers, and through government price-setting for certain Medicare Part B and Part D drugs.

### Candidate 21 | MODIFIED | Item 7 | FY2025 filing | page 41 | signals: royalty_profit_share
OLD: AbbVie's global Imbruvica revenues decreased 7% in 2024 primarily driven by decreased demand and lower market share in the United States as well as decreased collaboration revenues.
NEW: AbbVie's global Imbruvica revenues decreased 14% in 2025 primarily driven by decreased demand and unfavorable pricing in the United States as well as decreased collaboration revenues.

### Candidate 22 | REMOVED | Item 1A | FY2024 filing | page 14 | signals: patent_exclusivity
OLD (dropped in the new filing): Humira has faced competition from biosimilar products in the United States following the loss of exclusivity in 2023.

### Candidate 23 | REMOVED | Item 1A | FY2024 filing | page 16 | signals: medicare_negotiation
OLD (dropped in the new filing): In August 2023, HHS, through the CMS, selected Imbruvica as one of the first 10 medicines subject to government-set prices beginning in 2026.

### Candidate 24 | REMOVED | Item 1A | FY2024 filing | page 16 | signals: medicare_negotiation
OLD (dropped in the new filing): In August 2024, the CMS published Medicare Part D prices that will be applicable to these medicines, including Imbruvica, beginning January 1, 2026.

### Candidate 25 | REMOVED | Item 7 | FY2024 filing | page 34 | signals: litigation
OLD (dropped in the new filing): These costs were partially offset by an income tax benefit of $1.8 billion primarily related to the settlement of income tax examinations.

### Candidate 26 | REMOVED | Item 7 | FY2024 filing | page 34 | signals: medicare_negotiation
OLD (dropped in the new filing): In 2024, the CMS published Medicare Part D prices that will be applicable to the 10 selected drugs, including Imbruvica, beginning in 2026.

### Candidate 27 | REMOVED | Item 7 | FY2024 filing | page 34 | signals: medicare_negotiation
OLD (dropped in the new filing): In January 2025, HHS, through the CMS, selected Vraylar and Linzess as two of the 15 medicines subject to government-set prices beginning in 2027.

### Candidate 28 | REMOVED | Item 7 | FY2024 filing | page 39 | signals: royalty_profit_share
OLD (dropped in the new filing): The following table details AbbVie's worldwide net revenues: Percent change At actual currency rates At constant currency rates years ended December 31 (dollars in millions) 2024 2023 2022 2024 2023 2024 2023 Immunology Humira United States $ 7,142 $ 12,160 $ 18,619 (41.3)% (34.7)% (41.3)% (34.7)% International 1,851 2,244 2,618 (17.5)% (14.3)% (13.2)% (11.8)% Total $ 8,993 $ 14,404 $ 21,237 (37.6)% (32.2)% (36.9)% (31.9)% Skyrizi United States $ 10,086 $ 6,753 $ 4,484 49.3 % 50.6 % 49.3 % 50.6 % International 1,632 1,010 681 61.6 % 48.3 % 65.4 % 50.3 % Total $ 11,718 $ 7,763 $ 5,165 50.9 % 50.3 % 51.4 % 50.6 % Rinvoq United States $ 4,259 $ 2,824 $ 1,794 50.8 % 57.4 % 50.8 % 57.4 % International 1,712 1,145 728 49.6 % 57.3 % 57.0 % 60.7 % Total $ 5,971 $ 3,969 $ 2,522 50.4 % 57.4 % 52.5 % 58.4 % Oncology Imbruvica United States $ 2,448 $ 2,665 $ 3,426 (8.1)% (22.2)% (8.1)% (22.2)% Collaboration revenues 899 931 1,142 (3.5)% (18.5)% (3.5)% (18.5)% Total $ 3,347 $ 3,596 $ 4,568 (6.9)% (21.3)% (6.9)% (21.3)% Venclexta United States $ 1,234 $ 1,087 $ 1,009 13.5 % 7.8 % 13.5 % 7.8 % International 1,349 1,201 1,000 12.3 % 20.1 % 18.0 % 22.3 % Total $ 2,583 $ 2,288 $ 2,009 12.9 % 13.9 % 15.9 % 15.0 % Elahere United States $ 477 $ — $ — n/m n/m n/m n/m International 2 — — n/m n/m n/m n/m Total $ 479 $ — $ — n/m n/m n/m n/m Epkinly Collaboration revenues $ 118 $ 28 $ — >100.0 % n/m >100.0 % n/m International 28 3 — >100.0 % n/m >100.0 % n/m Total $ 146 $ 31 $ — >100.0 % n/m >100.0 % n/m Aesthetics Botox Cosmetic United States $ 1,682 $ 1,670 $ 1,654 0.7 % 1.0 % 0.7 % 1.0 % International 1,038 1,012 961 2.7 % 5.3 % 6.7 % 9.7 % Total $ 2,720 $ 2,682 $ 2,615 1.4 % 2.6 % 2.9 % 4.2 % Juvederm Collection United States $ 469 $ 519 $ 548 (9.6)% (5.4)% (9.6)% (5.4)% International 708 859 880 (17.6)% (2.4)% (13.4)% 1.9 % Total $ 1,177 $ 1,378 $ 1,428 (14.6)% (3.6)% (12.0)% (0.9)% Other Aesthetics United States $ 1,118 $ 1,060 $ 1,122 5.5 % (5.6)% 5.5 % (5.6)% International 161 174 168 (7.1)% 3.3 % (1.0)% 8.1 % Total $ 1,279 $ 1,234 $ 1,290 3.7 % (4.4)% 4.6 % (3.8)% Neuroscience Botox Therapeutic United States $ 2,718 $ 2,476 $ 2,255 9.8 % 9.8 % 9.8 % 9.8 % International 565 515 464 9.8 % 11.1 % 14.0 % 15.5 % Total $ 3,283 $ 2,991 $ 2,719 9.8 % 10.0 % 10.5 % 10.8 % Vraylar United States $ 3,260 $ 2,755 $ 2,037 18.4 % 35.2 % 18.4 % 35.2 % International 7 4 1 57.8 % >100.0 % 58.6 % >100.0 % Total $ 3,267 $ 2,759 $ 2,038 18.4 % 35.4 % 18.4 % 35.4 % Duodopa United States $ 96 $ 97 $ 95 (1.8)% 3.0 % (1.8)% 3.0 % International 351 371 363 (5.3)% 2.1 % (5.4)% 1.8 % Total $ 447 $ 468 $ 458 (4.6)% 2.3 % (4.7)% 2.1 % Ubrelvy United States $ 981 $ 803 $ 680 22.1 % 18.2 % 22.1 % 18.2 % International 25 12 — >100.0 % >100.0 % >100.0 % >100.0 % Total $ 1,006 $ 815 $ 680 23.4 % 19.9 % 23.4 % 19.9 % Qulipta United States $ 628 $ 405 $ 158 55.3 % >100.0 % 55.3 % >100.0 % International 30 3 — >100.0 % >100.0 % >100.0 % >100.0 % Total $ 658 $ 408 $ 158 61.3 % >100.0 % 61.3 % >100.0 % (a)

### Candidate 29 | REMOVED | Item 7 | FY2024 filing | page 41 | signals: litigation
OLD (dropped in the new filing): SG&A expense was unfavorably impacted by litigation reserve charges of $910 million in 2024 compared to income of $485 million in 2023 and acquisition and integration costs incurred in connection with the ImmunoGen and Cerevel Therapeutics acquisitions including cash-settled, post-closing expense for both ImmunoGen and Cerevel Therapeutics employee incentive awards.

### Candidate 30 | REMOVED | Item 7 | FY2024 filing | page 41 | signals: impairment
OLD (dropped in the new filing): R&D expense percentage for 2024 was unfavorably impacted by the intangible asset impairment charge of $4.5 billion related to emraclidine compared to an intangible asset impairment charge of $630 million in 2023, increased funding to support all stages of the company's pipeline assets and acquisition and integration costs incurred in connection with the ImmunoGen and Cerevel Therapeutics acquisitions including cash-settled, post-closing expense for employee incentive awards.

### Candidate 31 | REMOVED | Item 7 | FY2024 filing | page 42 | signals: working_capital
OLD (dropped in the new filing): In 2022, Puerto Rico enacted Act 52-2002 (the Puerto Rico Act) allowing for a transition from a Puerto Rico excise tax levied on gross inventory purchases to an income-based tax beginning in 2023.

### Candidate 32 | ADDED | Item 1A | FY2025 filing | page 16 | signals: medicare_negotiation
NEW: In August 2023, HHS, through CMS,

### Candidate 33 | ADDED | Item 1A | FY2025 filing | page 17 | signals: mfn_tariff
NEW: In January 2026, AbbVie entered into a voluntary agreement with the United States government to provide certain pricing concessions and U.S.-based research and development and capital investments in exchange for exemptions from tariffs and future pricing mandates during the three-year agreement period.

### Candidate 34 | MODIFIED | Item 1A | FY2025 filing | page 17 | signals: medicare_negotiation
OLD: AbbVie continues to evaluate the impact that the IRA may have on the company.
NEW: AbbVie continues to evaluate the impact that pricing and cost-containment related policy developments may have on the company.

### Candidate 35 | MODIFIED | Item 1A | FY2025 filing | page 17 | signals: gross_to_net
OLD: AbbVie cannot predict with certainty if additional government initiatives to contain health care costs or other factors could lead to new or modified regulatory requirements that include higher or incremental rebates or discounts.
NEW: AbbVie cannot predict with certainty whether additional government initiatives to contain health care costs or other factors could lead to new or modified regulatory or contractual requirements that include higher or incremental rebates, discounts or other price concessions.

### Candidate 36 | MODIFIED | Item 1A | FY2025 filing | page 17 | signals: gross_to_net
OLD: Other rebate and discount programs arise from contractual agreements with private payers.
NEW: Other rebate and discount programs arise from contractual agreements with private payers, including PBMs and managed care organizations.

### Candidate 37 | MODIFIED | Item 1A | FY2025 filing | page 17 | signals: gross_to_net
OLD: Various factors, including market factors and the ability of private payers to control patient access to products, may provide payers the leverage to negotiate higher or additional rebates or discounts that could have a material adverse effect on AbbVie's operations.
NEW: Various factors, including market factors, consolidation among PBMs and the ability of private payers to control patient access to products, including through formulary management and utilization controls, may provide payers the leverage to negotiate higher or additional rebates or discounts that could have a material adverse effect on AbbVie's operations.

### Candidate 38 | ADDED | Item 1A | FY2025 filing | page 21 | signals: gross_to_net
NEW: The 340B Drug Pricing Program requires participating manufacturers to offer discounts to covered entities and growth in entities claiming entitlement to 340B pricing has increased the portion of our sales subject to such discounts.

### Candidate 39 | ADDED | Item 7 | FY2025 filing | page 35 | signals: medicare_negotiation
NEW: The 2025 Act also includes certain new health care provisions related to the orphan drug exclusion of the Inflation Reduction Act of 2022, and Medicaid, which have various effective dates.

### Candidate 40 | ADDED | Item 7 | FY2025 filing | page 35 | signals: litigation
NEW: Intellectual Property Protection and Regulatory Exclusivity In September 2025, AbbVie announced the settlement of litigation with all generic manufacturers that filed abbreviated new drug applications with the U.S. Food and Drug Administration (FDA) for generic versions of upadacitinib tablets, which AbbVie markets as Rinvoq.

Draft up to 12 findings. Rank by materiality to revenue, operating income or EPS.