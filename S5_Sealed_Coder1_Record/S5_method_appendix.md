# Supplementary S5 — Method Appendix to the Coding Manual

*Sections 6–8 of the coding manual. This appendix was retained by the researchers and was not issued to the second coder, because it states the marginal totals and the expected number of security hits, which would anchor the coder's judgements. Sections 1–5 are in `S1_Coding_Manual/S1_Coding_Manual.md` and, as issued, in `S4_Second_Coder_Reliability/Kit/S4_coding_manual_coder_version.md`.*

---

## 6. Agreement metrics and reporting requirements

All of the following must be reported:

| Metric | Applies to | Note |
|---|---|---|
| Cohen's κ | Job family (6 categories, nominal) | primary metric |
| Cohen's κ per dimension | Each of the four binary variables | reported dimension by dimension |
| Krippendorff's α | Four dimensions (multilabel specification) | for comparison with κ |
| **Gwet's AC1** | Four dimensions, **especially *knows security*** | required — see the warning below |
| **PABAK** | Four dimensions | prevalence-adjusted κ, as above |
| Raw agreement | All | so that readers can judge |
| F1 | Four dimensions | first coder as reference |

> ### Low-prevalence warning (must be stated in the paper)
>
> In the 130-record subsample, *knows security* is expected to have only about
> **2 hits (1.5%)**. At such a low prevalence **Cohen's κ suffers the "kappa paradox"**: even
> when the two coders agree on 98% of records, κ may be close to zero or even negative,
> because κ corrects for chance agreement using the marginal distributions, and extremely
> unbalanced marginals drive the chance-agreement term towards 1.
>
> Accordingly, agreement on *knows security* **must not be reported with κ alone**; Gwet's AC1
> or PABAK must be reported alongside it, together with the raw agreement rate and the number
> of hits. Otherwise reviewers will read the κ value as evidence that coding is unreliable.
>
> If the number of hits is so small that no agreement statistic is stable, report the
> **absolute number of agreements** instead (e.g. "of 130 records the two coders both coded 1
> for X, both coded 0 for Y, and disagreed on Z"), and state that the dimension is unsuitable
> for κ reporting because of its very low prevalence.

---

## 7. Work already completed that can substitute for part of an agreement check

The following work **cannot substitute** for an inter-coder agreement check (reviewers rightly
pointed out that the two test different kinds of error), but serves as supporting evidence:

1. **Rule self-consistency check.** Re-running the rules in the table above reproduced the
   marginal totals reported in the paper exactly (understands business 279 / masters models 268
   / knows security 8 / can deliver 343).
2. **Coding-rule sensitivity test.** Under multilabel coding, coverage became understands
   business 281 / masters models 268 / knows security 8 / can deliver 349 — **the ordering is
   unchanged and the number of security hits is unchanged**, showing that low coverage is not
   an artefact of the priority rule.
3. **Record-level security semantics review.** A graded security variable built from the full
   job description yielded 12 AI-specific security hits (2.29%); after record-by-record manual
   reading the precision was approximately 10/12, and three of those records were
   security-dedicated roles.
4. **Threshold sensitivity.** Sample size under varying near-duplicate similarity thresholds
   (see the reproducibility appendix, Appendix A.2 of the manuscript).

---

## 8. File list

| File | Purpose |
|---|---|
| `S4_Second_Coder_Reliability/Kit/S4_blind_coding_form.xlsx` (and `.csv`) | form issued to the second coder (order randomised, renumbered Q001–Q130) |
| `S4_Second_Coder_Reliability/Kit/S4_instructions_to_second_coder.md` | operating instructions issued to the coder |
| **this file, Sections 1–5** | the coding rules issued to the coder |
| `S5_Sealed_Coder1_Record/S5_coder1_sealed_record.csv` | first coder's results, aligned to the blind Q-numbering; **not to be shown before agreement has been computed** |
| `S5_Sealed_Coder1_Record/S5_key_Q_id_to_original_record_id.csv` | mapping from blind Q-ids to original record ids |
| `S4_Second_Coder_Reliability/Scripts/S4_reliability_kappa_ac1_pabak.py` | reads the returned form, outputs κ / AC1 / PABAK (with bootstrap 95% CI) and the third-adjudicator table |
| this file, Sections 6–8 | methodological appendix (retained by the researchers) |
