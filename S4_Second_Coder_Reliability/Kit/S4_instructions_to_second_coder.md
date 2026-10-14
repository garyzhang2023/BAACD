# Instructions to the Second Coder

*This is the document that was issued to the second coder, reproduced in English. It is included
so that the conditions of the second coding can be audited.*

---

## What this is

A study of capability requirements in AI application-service jobs needs **two researchers to code
the same 130 job postings independently**, in order to compute **inter-coder reliability**. You
are the second coder.

## What you are asked to do

1. Open `S4_blind_coding_form.xlsx` and fill in, row by row, the five columns
   `job_family_code_1to6`, `dim_understand_business`, `dim_master_models`,
   `dim_know_security`, `dim_can_deliver`. The workbook has drop-down constraints, so only valid
   values can be entered.
2. Base every decision on `S4_coding_manual_coder_version.md` (supplied with this kit). Read it
   through before starting.
3. The information available per row is the job title, the skill tags and an excerpt of the job
   description. You do **not** need to look the company up online.
4. Expected time: 35–45 minutes. Return the file when you are done.

## Three hard requirements on independence

This matters far more than how quickly you finish.

1. **Do not** ask the first coder (or anyone who has seen the first coder's results) whether a
   given record should be 0 or 1.
2. **Do not** accept, request or open any file containing completed coding results. If someone
   sends you one, ignore it and tell the researcher.
3. For records you are unsure about, **decide according to your own reading and write your
   reasoning in the `coder_note` column** — do not leave it blank, and do not change a judgement
   in order to make the two coders "look consistent". **Disagreement is itself what this study
   measures**; a large number of disagreements does not mean you coded badly.

> Note: the presentation order of the form has been shuffled and renumbered 001–130. This
> numbering is unrelated to the record numbers in the manuscript; the purpose is to prevent
> anyone from recalling or aligning existing results by position.

## The five columns (full rules in the coding manual)

| Column | Values | Meaning |
|---|---|---|
| `job_family_code_1to6` | 1–6 | 1 delivery and implementation, 2 solutions and pre-sales, 3 research, development and algorithms, 4 product and operations, 5 AI applications and tools, 6 other |
| `dim_understand_business` | 0/1 | does the posting explicitly require understanding of industry processes or business scenarios, communicating with business stakeholders, or requirements analysis? |
| `dim_master_models` | 0/1 | does it explicitly require knowledge of, or ability to tune, large models, machine learning or algorithms? |
| `dim_know_security` | 0/1 | does it explicitly state AI or data security governance responsibilities? (**production safety and information-security operations do not count**) |
| `dim_can_deliver` | 0/1 | does it explicitly require on-site deployment, implementation, go-live or customer delivery? |

**Pay particular attention to `dim_know_security`.** Count only governance relating to the
**AI model or the data itself** — for example AI security, model security, prompt injection,
jailbreak, adversarial examples, AI ethics and compliance, content safety, or explainability used
as a governance instrument. **Plant production safety, fire safety, information-security
operations and data-permission administration as such do not count.** When in doubt, record your
reasoning in `coder_note`.

## About the small number of *knows security* hits

Explicit mention of AI security governance is very rare in this set of postings — most likely a
single-digit number. Coding almost everything as 0 is **expected**, not an omission. Please do
not relax the criterion because the column looks too sparse.
