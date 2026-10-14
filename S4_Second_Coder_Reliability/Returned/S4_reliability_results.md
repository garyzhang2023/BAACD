# Supplementary S4 — Inter-Coder Reliability Results

Second coder's independent blind coding of the 130-record stratified random subsample
(24.8% of the 524 analytic records). All values are **pre-negotiation agreement**; none was
adjusted after the fact.

## 1. Summary

| Judgement | Agreements | Agreement rate | Cohen's κ | Gwet's AC1 | PABAK | κ 95% CI |
|---|---:|---:|---:|---:|---:|---|
| Understands business | 130/130 | 100.00% | 1.000 | 1.000 | 1.000 | 1.000–1.000 |
| Masters models | 129/130 | 99.23% | 0.985 | 0.985 | 0.985 | 0.952–1.000 |
| Knows security | 128/130 | 98.46% | 0.000 ᵃ | 0.984 | 0.969 | 0.000–0.000 |
| Can deliver | 127/130 | 97.69% | 0.951 | 0.957 | 0.954 | 0.887–1.000 |
| Four dimensions combined | 514/520 | 98.85% | — | — | — | — |
| Job family (six categories) | 102/130 | 78.46% | 0.720 | 0.746 | 0.569 | 0.628–0.806 |

ᵃ The first coder identified 2 cases and the second coder none. At this prevalence κ degenerates
to zero and is uninterpretable, because the chance-agreement term is driven towards 1 by
extremely unbalanced marginals. Following the low-prevalence reporting rule fixed in advance in
the coding manual (S1, Section 6), this dimension is reported with Gwet's AC1, PABAK and the
absolute number of agreements instead. The raw agreement of 98.46% is not evidence of coder
disagreement. Confidence intervals are percentile bootstrap intervals with 20,000 draws and a
fixed seed (`20260927`).

## 2. Marginal hit counts

| Dimension | Coder 1 | Coder 2 |
|---|---:|---:|
| Understands business | 70 (53.85%) | 70 (53.85%) |
| Masters models | 69 (53.08%) | 68 (52.31%) |
| Knows security | 2 (1.54%) | 0 (0.00%) |
| Can deliver | 80 (61.54%) | 83 (63.85%) |

## 3. Confusion matrices

Binary dimensions (rows = coder 1, columns = coder 2):

| Dimension | c1 = 0, c2 = 0 | c1 = 0, c2 = 1 | c1 = 1, c2 = 0 | c1 = 1, c2 = 1 |
|---|---:|---:|---:|---:|
| Understands business | 60 | 0 | 0 | 70 |
| Masters models | 61 | 0 | 1 | 68 |
| Knows security | 128 | 0 | 2 | 0 |
| Can deliver | 47 | 3 | 0 | 80 |

Job family, codes 1–6 as defined in `S3_README_codebook.md` Section 2 (rows = coder 1,
columns = coder 2):

| Coder 1 ↓ / Coder 2 → | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|
| 1 Delivery and implementation | **41** | 0 | 0 | 0 | 0 | 1 |
| 2 Solutions and pre-sales | 0 | **5** | 2 | 0 | 1 | 2 |
| 3 Research, development and algorithms | 0 | 0 | **29** | 0 | 0 | 1 |
| 4 Product and operations | 0 | 0 | 1 | **4** | 0 | 3 |
| 5 AI applications and tools | 1 | 0 | 2 | 1 | **6** | 4 |
| 6 Other related roles | 2 | 0 | 1 | 0 | 6 | **17** |

The 28 job-family disagreements concentrate on the boundaries between codes 5 and 6 (10 records)
and between codes 1 and 6 (3 records), which is where the job title and the skill tags point in
different directions. The reported κ = 0.720 is "substantial" on the Landis and Koch scale.

## 4. Records referred for blind adjudication

The two records in which the coders disagreed on *knows security* were referred to a third
adjudicator who took no part in coding. The disputed records are `Q030` (AI技术工程师) and
`Q046` (量化交易工程师); in both, the first coder counted the skill tags 风控算法 and 风控/安全策略经验
("risk-control algorithms", "risk-control / security strategy experience") as a security
governance hit, while the second coder treated them as using AI for a security-related *business*
scenario, which the manual excludes (S1, Section 3.4). Details, including the disputed skill tags
and the adjudication column, are in `Returned/S4_third_adjudication_table.csv`. The disputed
job-description excerpts are withheld for the same reason as the main dataset (they can identify
a firm).

**The adjudicator's ruling is used only to form the final dataset. It was not used to revise, and
does not appear in, the agreement values reported above.**

## 5. Reproduction

```bash
cd Scripts
python S4_reliability_kappa_ac1_pabak.py
```

The packaged script re-runs against the packaged files and reproduces every figure above.

**Reproduction note.** Agreement counts, agreement rates, κ, AC1, PABAK and all confusion
matrices reproduce exactly. The bootstrap confidence bounds agree with the values printed in
Table A1 of the manuscript to within 0.001 in the third decimal (the packaged script gives
0.887–1.000 for *can deliver* and 0.628–0.806 for job family, against 0.888–1.000 and
0.629–0.806 in Table A1); the difference reflects the resampling implementation, not the data,
and the packaged script uses a single draw count of 20,000 for every row of the table.
