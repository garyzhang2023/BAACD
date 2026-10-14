
# Manuscript Data

**Manuscript:** *Bounded Anticipation in AI Curriculum Design: Integrating Current Job Demand, Policy Priorities, and Future Capability Needs in Higher Vocational Education*

This package contains the anonymized derived data, coding documentation, analysis code, reliability records, and anonymized expert-validation materials described in the manuscript. It is designed for upload as the manuscript-data/supplementary-data archive.

## Contents

- `S1_Coding_Manual`: coding dictionary, regular expressions, priority rules, exclusions, and boundary cases.
- `S2_Analysis_Scripts`: scripts used for cleaning documentation, coding, statistical analysis, sensitivity checks, and figure generation.
- `S3_Anonymized_Dataset`: 524-row anonymized derived job-posting dataset in CSV and XLSX formats, with a codebook.
- `S4_Second_Coder_Reliability`: coder instructions/manual, anonymous returned judgments, reliability results, and the reliability script.
- `S5_Sealed_Coder1_Record`: the first coder's anonymous judgments and methodological appendix.
- `S6_Expert_Validation`: anonymized Round 1/Round 2 expert data, item codebook, bounded-anticipation ratings, revision log, results, final wording, and analysis script.
- `FILE_MANIFEST.csv`: byte size and SHA-256 checksum for every included file.

## Confidentiality and exclusions

The archive excludes raw job-posting text, company names, company identifiers, URLs, contact details, expert names, the expert identity key, named invitation/consent files, individual returned expert forms, simulated forms, backups, caches, and working renders. The S4 blank/original workbooks and the Q-ID-to-original-record mapping are also excluded because they contain or reconnect to source text. Anonymous expert IDs (`E01`–`E06` and `V01`–`V06`) identify panel group only and cannot be linked to names from this archive.

## Reproducibility notes

The S3 derived dataset supports the reported analyses without redistributing identifying source text. The first cleaning stage cannot be rerun without the withheld raw platform export; the corresponding code is supplied for auditability. The S4 reliability script reads the anonymous coder-2 file and the sealed coder-1 record. The S6 analysis script reads `S6_expert_validation_data.xlsx` and generates an analysis-results workbook.

## Software

Python 3.11 with pandas, NumPy, SciPy, statsmodels, matplotlib, openpyxl, and Pillow. Randomized procedures use the fixed seeds documented in the scripts.

## Data-use note

These files are supplied for scholarly review and verification. Users must not attempt to re-identify employers, job postings, coders, or expert participants.
