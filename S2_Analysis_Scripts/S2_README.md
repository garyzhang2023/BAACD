
# S2 Analysis Scripts

The scripts document the Phase 1 workflow and statistical checks. `s2_clean.py` requires the withheld raw platform export and is included for auditability. Analyses based on derived variables use the anonymized dataset in S3. The figure scripts may require the manuscript figure folders used in the authors' working environment. Fixed random seeds are declared in the relevant scripts.

Main sequence: `s2_clean.py` (cleaning), `s4_family.py` (job families), `s6_expert_stats.py` (capability statistics), `revise_analyses.py` and `verify_round3.py`–`verify_round5.py` (regression and sensitivity checks), followed by the figure scripts.
