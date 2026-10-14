# -*- coding: utf-8 -*-
"""S4_reliability_kappa_ac1_pabak.py
Inter-coder reliability for the second coder's independent blind coding (n = 130).

Reads
-----
  ../Returned/S4_returned_form_coder2.csv                        (second coder)
  ../../S5_Sealed_Coder1_Record/S5_coder1_sealed_record.csv      (first coder, sealed)

Prints
------
  1. the four binary capability dimensions: agreements, agreement rate, Cohen's kappa,
     Gwet's AC1, PABAK, bootstrap 95% confidence intervals, marginal hit counts and the
     2x2 confusion matrices;
  2. job family (six categories): agreement rate, nominal kappa, AC1, PABAK and the 6x6
     confusion matrix;
  3. the records in which the two coders disagreed on *knows security*, i.e. the records
     referred to the blind third adjudicator.

Design note (the kappa paradox at low prevalence)
------------------------------------------------
*knows security* has only two positives in this subsample. Kappa then degenerates towards zero
even though raw agreement is 98.46%, because the chance-agreement term is driven towards 1 by
extremely unbalanced marginals. Kappa alone is therefore uninterpretable for that dimension and
must be reported alongside Gwet's AC1 (robust to prevalence) and PABAK, together with the
absolute number of agreements. This is the low-prevalence reporting rule fixed in advance in the
coding manual.

Usage:  python S4_reliability_kappa_ac1_pabak.py
"""
import io
import os
import csv
import sys

import numpy as np

N_BOOT = 20000         # one draw count for every interval, so the table is internally uniform
SEED = 20260927
DIMS = ["dim_understand_business", "dim_master_models",
        "dim_know_security", "dim_can_deliver"]
FAM = "job_family"
FAM_ALIASES = ("job_family", "job_family_code_1to6")

HERE = os.path.dirname(os.path.abspath(__file__))
C2_PATH = os.path.normpath(os.path.join(HERE, "..", "Returned", "S4_returned_form_coder2.csv"))
C1_PATH = os.path.normpath(os.path.join(
    HERE, "..", "..", "S5_Sealed_Coder1_Record", "S5_coder1_sealed_record.csv"))


def read_csv_dict(path):
    rows = list(csv.reader(io.open(path, encoding="utf-8-sig", newline="")))
    hdr = [h.strip() for h in rows[0]]
    out = {}
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        out[row[0].strip()] = dict(zip(hdr, [str(x).strip() for x in row]))
    return out


def fam_canon(s):
    """Normalise a job-family label to its leading code 1-6.

    The sealed record stores labels such as '1 Delivery and implementation (FDE-type)'; the
    returned form stores the bare code. Comparing the strings literally would mis-count every
    labelled record as a disagreement, so the leading numeral is used as the canonical key.
    """
    s = (s or "").strip()
    if not s:
        return ""
    if s[0] in "123456":
        return s[0]
    return s


def cohen_kappa(a, b, cats):
    n = len(a)
    ix = {c: i for i, c in enumerate(cats)}
    m = np.zeros((len(cats), len(cats)))
    for x, y in zip(a, b):
        if x in ix and y in ix:
            m[ix[x], ix[y]] += 1
    po = np.trace(m) / n
    pe = float((m.sum(0) / n) @ (m.sum(1) / n))
    k = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return k, po, pe, m


def gwet_ac1(a, b, cats):
    n = len(a)
    q = len(cats)
    if q < 2:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pi = {c: (sum(1 for x in a if x == c) + sum(1 for y in b if y == c)) / (2.0 * n)
          for c in cats}
    pe = sum(pi[c] * (1 - pi[c]) for c in cats) / (q - 1)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def pabak(a, b):
    return 2 * (sum(1 for x, y in zip(a, b) if x == y) / len(a)) - 1


def boot_ci(a, b, cats, fn, nboot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(a)
    aa = np.array(a, dtype=object)
    bb = np.array(b, dtype=object)
    vals = []
    for _ in range(nboot):
        ix = rng.integers(0, n, n)
        v = fn(list(aa[ix]), list(bb[ix]), cats)
        if isinstance(v, tuple):
            v = v[0]
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        if not np.isnan(v):
            vals.append(v)
    if not vals:
        return float("nan"), float("nan")
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main():
    for p in (C1_PATH, C2_PATH):
        if not os.path.isfile(p):
            print("missing input: %s" % p)
            sys.exit(1)
    c1 = read_csv_dict(C1_PATH)
    c2 = read_csv_dict(C2_PATH)
    ids = sorted(set(c1) & set(c2))
    if len(c1) != len(c2) or len(ids) != len(c1):
        print("record sets differ: coder1=%d coder2=%d matched=%d"
              % (len(c1), len(c2), len(ids)))
        sys.exit(2)
    n = len(ids)
    for recs, tag in ((c1, "sealed"), (c2, "returned")):
        if FAM not in recs[ids[0]]:
            for alt in FAM_ALIASES:
                if alt in recs[ids[0]]:
                    for i in recs:
                        recs[i][FAM] = recs[i][alt]
                    break
    print("=" * 78)
    print("Inter-coder reliability (second coder, independent blind coding)")
    print("=" * 78)
    print("matched records: %d" % n)
    print()

    res = {}
    CIS = {}
    print("-" * 78)
    print("1. Binary capability dimensions (n = %d)" % n)
    print("-" * 78)
    print("%-26s %7s %8s %8s %8s %8s %16s" %
          ("dimension", "agree", "rate", "kappa", "AC1", "PABAK", "kappa 95% CI"))
    for k in DIMS:
        a = [c1[i][k] for i in ids]
        b = [c2[i][k] for i in ids]
        agree = sum(1 for x, y in zip(a, b) if x == y)
        kap, po, pe, m = cohen_kappa(a, b, ["0", "1"])
        ac1 = gwet_ac1(a, b, ["0", "1"])
        pb = pabak(a, b)
        lo, hi = boot_ci(a, b, ["0", "1"], lambda x, y, c: cohen_kappa(x, y, c)[0])
        CIS[k] = (lo, hi)
        res[k] = dict(agree=agree, kappa=kap, ac1=ac1, pabak=pb, m=m,
                      n1=sum(1 for x in a if x == "1"), n2=sum(1 for x in b if x == "1"))
        print("%-26s %5d/%-3d %7.4f %8.4f %8.4f %8.4f   [%.3f, %.3f]" %
              (k.replace("dim_", ""), agree, n, agree / float(n), kap, ac1, pb, lo, hi))
    print()
    print("confusion matrices (rows = coder 1, columns = coder 2)")
    for k in DIMS:
        m = res[k]["m"]
        print("  %-26s  c1=0,c2=0 %3d | c1=0,c2=1 %3d | c1=1,c2=0 %3d | c1=1,c2=1 %3d" %
              (k.replace("dim_", ""), m[0][0], m[0][1], m[1][0], m[1][1]))
    print()
    print("marginal hits per coder")
    for k in DIMS:
        print("  %-26s  coder1 %3d (%5.2f%%)   coder2 %3d (%5.2f%%)" %
              (k.replace("dim_", ""), res[k]["n1"], 100.0 * res[k]["n1"] / n,
               res[k]["n2"], 100.0 * res[k]["n2"] / n))
    tot_a = sum(res[k]["agree"] for k in DIMS)
    print("  four-dimension total: %d/%d = %.2f%%" % (tot_a, 4 * n, 100.0 * tot_a / (4 * n)))
    print()

    print("-" * 78)
    print("2. Job family, six categories (n = %d)" % n)
    print("-" * 78)
    a = [fam_canon(c1[i][FAM]) for i in ids]
    b = [fam_canon(c2[i][FAM]) for i in ids]
    cats = sorted(set(a) | set(b))
    agree = sum(1 for x, y in zip(a, b) if x == y)
    kap, po, pe, m = cohen_kappa(a, b, cats)
    ac1 = gwet_ac1(a, b, cats)
    lo, hi = boot_ci(a, b, cats, lambda x, y, c: cohen_kappa(x, y, c)[0])
    CIS["job_family"] = (lo, hi)
    print("agreement %d/%d = %.4f" % (agree, n, agree / float(n)))
    print("Cohen kappa = %.4f (pe = %.4f), 95%% CI [%.3f, %.3f]; AC1 = %.4f; PABAK = %.4f"
          % (kap, pe, lo, hi, ac1, pabak(a, b)))
    print()
    print("confusion matrix (rows = coder 1, columns = coder 2), family codes 1-6:")
    print("        " + "".join("%8s" % c for c in cats))
    for r, c in enumerate(cats):
        print("%-8s" % c + "".join("%8d" % m[r][j] for j in range(len(cats))))
    print("coder 1 marginal: " + ", ".join("%s=%d" % (c, sum(1 for x in a if x == c))
                                           for c in cats))
    print("coder 2 marginal: " + ", ".join("%s=%d" % (c, sum(1 for x in b if x == c))
                                           for c in cats))
    print()

    print("-" * 78)
    print("3. knows-security disagreements -> blind third adjudicator")
    print("-" * 78)
    sa = [c1[i]["dim_know_security"] for i in ids]
    sb = [c2[i]["dim_know_security"] for i in ids]
    dis = [ids[j] for j in range(n) if sa[j] != sb[j]]
    print("disagreeing records: %d %s" % (len(dis), dis))
    for i in dis:
        print("   %s  coder1=%s  coder2=%s" %
              (i, c1[i]["dim_know_security"], c2[i]["dim_know_security"]))
    print()
    print("The adjudicator's ruling is used only to form the final dataset.")
    print("The figures above are pre-negotiation agreement and were not adjusted afterwards.")
    print("=" * 78)

    # ---- machine-checkable assertions against the values reported in the manuscript ----
    exp = {"dim_understand_business": (130, 1.000), "dim_master_models": (129, 0.985),
           "dim_know_security": (128, 0.000), "dim_can_deliver": (127, 0.951)}
    for k, (ag, ka) in exp.items():
        assert res[k]["agree"] == ag, "%s agreement %d != %d" % (k, res[k]["agree"], ag)
        assert abs(res[k]["kappa"] - ka) < 5e-4, "%s kappa %.4f != %.3f" % (k, res[k]["kappa"], ka)
    assert tot_a == 514, "four-dimension total %d != 514" % tot_a
    assert abs(res["dim_know_security"]["ac1"] - 0.984) < 5e-4
    assert abs(res["dim_know_security"]["pabak"] - 0.969) < 5e-4
    assert agree == 102 and abs(kap - 0.720) < 5e-4 and abs(ac1 - 0.746) < 5e-4
    assert len(dis) == 2, "security disagreements %d != 2" % len(dis)
    # bootstrap bounds are asserted to 0.002: a different resampling call may move the third
    # decimal, but not more.
    for k, lo_e, hi_e in [("dim_master_models", 0.952, 1.000),
                          ("dim_can_deliver", 0.888, 1.000)]:
        lo, hi = CIS[k]
        assert abs(lo - lo_e) <= 2e-3 and abs(hi - hi_e) <= 2e-3, \
            "%s CI [%.3f, %.3f] vs [%.3f, %.3f]" % (k, lo, hi, lo_e, hi_e)
    assert abs(CIS["job_family"][0] - 0.629) <= 2e-3, "family CI lower %.3f" % CIS["job_family"][0]
    print("reproduction check: point estimates, agreement counts and bootstrap bounds all match")
    print("the manuscript (Table A1) within 0.002 on the bootstrap bounds  OK")


if __name__ == "__main__":
    main()
