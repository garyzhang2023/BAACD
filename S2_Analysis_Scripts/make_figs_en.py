# -*- coding: utf-8 -*-
"""make_figs_en.py —— 图件链第 1 段：按 M5 重绘基础英文图（>= 600 dpi，图内文字全英文）。

注：本脚本产出 figs_en/（8 张），供稿件采用的仅 Figure 3；Figure 4–9 由
make_figs_en_v2.py 重绘、Figure 1–2 由 make_figs_docx.py 按版面重绘，
最终由 build_figs_final.py 装配为 figs_docx/。完整链路见 S2_README_analysis_chain.md。

数据来源（均为当前口径 n = 524）：
  论文分析/_专家版_指标.json                     —— 族、四维覆盖、共现、学历/经验分布、Cochran's Q
  补充材料-Supplementary/S3_Anonymized_Dataset/postings_derived_anonymized.csv —— 图 8 箱线图
输出：<FIGROOT>/figs_en/fig1..fig8*.png（作者工作区即 投稿-MDPI/figs_en/）
"""
import io
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["savefig.dpi"] = 600
plt.rcParams["figure.dpi"] = 600
plt.rcParams["font.size"] = 9

# ---- 工作区定位（补充材料包内不依赖作者本机绝对路径）----
# 图件脚本需要两个根：
#   BASE    = 含「论文分析」的目录（提供 _专家版_指标.json）
#   FIGROOT = 含 figs_en/ 或 figs_en_v2/ 的目录（作者工作区为 投稿-MDPI/）
# 可分别用 PROJECT_ROOT / FIG_ROOT 覆盖；否则自本文件逐级上溯；找不到则回落本文件目录。
def _locate(probes, env_name):
    env = os.environ.get(env_name)
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    while True:
        if any(os.path.isdir(os.path.join(cur, p)) for p in probes):
            return cur
        up = os.path.dirname(cur)
        if up == cur:
            return here
        cur = up


BASE = _locate(["论文分析"], "PROJECT_ROOT")
FIGROOT = _locate(["figs_en", "figs_en_v2"], "FIG_ROOT")

HERE = os.path.dirname(os.path.abspath(__file__))
ANA = os.path.join(BASE, "论文分析")
FIG = os.path.join(FIGROOT, "figs_en")
os.makedirs(FIG, exist_ok=True)

J = json.load(io.open(os.path.join(ANA, "_专家版_指标.json"), encoding="utf-8"))
N = J["n_keep"]
_S3_CAND = [os.path.join(os.path.dirname(HERE), "S3_Anonymized_Dataset",
                         "S3_postings_derived_anonymized.csv"),
            os.path.join(os.path.dirname(HERE), "S3_Anonymized_Dataset",
                         "postings_derived_anonymized.csv"),
            os.path.join(FIGROOT, "补充材料-Supplementary", "S3_Anonymized_Dataset",
                         "postings_derived_anonymized.csv")]
S3 = next((c for c in _S3_CAND if os.path.isfile(c)), _S3_CAND[-1])

C_TEAL, C_BLUE, C_PURP = "#0F6E56", "#185FA5", "#534AB7"
C_GRAY, C_RED, C_AMBER = "#5F5E5A", "#A32D2D", "#B7791F"
C_LINE = "#BFBFBF"


def save(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=600, bbox_inches="tight", facecolor="white", pad_inches=0.10)
    plt.close(fig)
    from PIL import Image
    im = Image.open(p)
    print("  %-42s %5dx%-5d  %d dpi  width=%.2f in" %
          (name, im.size[0], im.size[1], im.info.get("dpi", (600,))[0],
           im.size[0] / im.info.get("dpi", (600,))[0]))


# ===================== Figure 1. Policy-job-education framework =====================
fig, ax = plt.subplots(figsize=(6.9, 4.35))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8.1)
ax.axis("off")


def band(y, h, label, items, color, bg):
    ax.add_patch(FancyBboxPatch((0.15, y), 9.7, h,
                                boxstyle="round,pad=0.05,rounding_size=0.12",
                                linewidth=1.1, edgecolor=color, facecolor=bg, zorder=1))
    ax.text(0.45, y + h / 2, label, ha="center", va="center", rotation=90,
            fontsize=10, color=color, fontweight="bold", zorder=3)
    n = len(items)
    w = 1.95
    gap = (8.6 - n * w) / (n - 1) if n > 1 else 0
    for i, it in enumerate(items):
        x = 1.35 + i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, y + h / 2 - 0.42), w, 0.84,
                                    boxstyle="round,pad=0.03,rounding_size=0.09",
                                    linewidth=1.0, edgecolor=color, facecolor="white", zorder=2))
        ax.text(x + w / 2, y + h / 2, it, ha="center", va="center", fontsize=8.9,
                color="#2B2B2B", zorder=3)


band(5.85, 1.5, "Policy", ["Understands\nbusiness", "Masters\nmodels", "Knows\nsecurity", "Can\ndeliver"],
     C_TEAL, "#EEF6F2")
band(3.30, 1.5, "Job", ["Job family", "Education\nthreshold", "Capability\nexpression", "Salary\nstructure"],
     C_BLUE, "#EDF3FA")
band(0.75, 1.5, "Education", ["Programme\npositioning", "Curriculum\nmodules", "Progressive\nprojects",
                              "Assessment\nevidence"],
     C_PURP, "#F1EFF9")
for (y0, y1, txt) in [(5.83, 4.83, "test"), (3.28, 2.28, "translate")]:
    ax.add_patch(FancyArrowPatch((5.0, y0), (5.0, y1), arrowstyle="-|>",
                                 mutation_scale=15, linewidth=1.5, color=C_GRAY, zorder=4))
    ax.text(5.22, (y0 + y1) / 2, txt, ha="left", va="center", fontsize=8.8,
            color=C_GRAY, fontweight="bold", zorder=4)
ax.text(0.15, 7.82, "Policy capability  ->  work tasks and capability evidence  ->  vocational provision",
        fontsize=8.5, color=C_GRAY, ha="left", va="center")
save(fig, "fig1_policy_job_education_framework.png")

# ===================== Figure 2. Sustainability framework =====================
fig, ax = plt.subplots(figsize=(12.0, 7.3))
ax.set_xlim(0, 1200)
ax.set_ylim(0, 730)
ax.axis("off")
INK, INK2 = "#1a1a1a", "#4a4a4a"
EDGE = "#8a8a8a"
C_G, E_G = "#fde9e0", "#d9541e"
C_R, E_R = "#fdeaea", "#bc2d2d"
C_A, E_A = "#e2eef7", "#1f6fb2"
C_S, E_S = "#e6f2e6", "#3d7a3d"


def box(x, y, w, h, fc, ec, lw=1.6, r=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=%d" % r,
                                fc=fc, ec=ec, lw=lw, zorder=2))


def txt(x, y, s, size=11.0, color=INK, weight="normal", ha="center", lh=1.5):
    ax.text(x, y, s, fontsize=size, color=color, ha=ha, va="center",
            fontweight=weight, linespacing=lh, zorder=4)


def arrow(p1, p2, color=EDGE, lw=2.4, style="-|>", ms=14, ls="solid"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=ms,
                                 lw=lw, color=color, zorder=3, linestyle=ls))


txt(600, 700, "Sustainability framework for talent supply in AI application services", size=15.5, weight="bold")
arrow((975, 645), (975, 662), color=E_A, lw=1.7, style="-", ms=1)
arrow((975, 662), (590, 662), color=E_A, lw=1.7, style="-", ms=1, ls=(0, (5, 3)))
arrow((590, 662), (590, 645), color=E_A, lw=1.7, ms=12)
txt(782, 673, "mitigates", size=9.8, color=E_A)

COL_Y, COL_H = 350, 295
cols = [(30, 350, C_G, E_G, "(1) Industrial scale targets", "MIIT Circular No. 414"),
        (415, 350, C_R, E_R, "(2) Two sustainability risks", "gap between policy and explicit market language"),
        (800, 350, C_A, E_A, "(3) Educational response", "higher vocational colleges, Guangdong")]
for x, w, fc, ec, t, sub in cols:
    box(x, COL_Y, w, COL_H, fc, ec)
    txt(x + w / 2, 622, t, size=12.5, color=ec, weight="bold")
    txt(x + w / 2, 598, sub, size=10.0, color=INK2)
    ax.plot([x + 30, x + w - 30], [584, 584], color=ec, lw=1.0, alpha=0.55)

box(46, 498, 318, 70, "#ffffff", E_G, lw=1.1)
txt(205, 545, "by end-2026  >= 2,000", size=12, weight="bold")
txt(205, 516, "by end-2027  >= 3,000 providers", size=10.2, color=INK2)
box(46, 464, 318, 26, "#ffffff", E_G, lw=1.1)
txt(205, 477, "pilot-zone provinces >= 100", size=10.2, color=INK2)
box(46, 392, 318, 64, "#ffffff", E_G, lw=1.1)
txt(205, 431, ">= 10 service teams per province", size=11.4, weight="bold")
txt(205, 406, "(1 lead + >= 2 upstream/downstream)", size=9.8, color=INK2)
txt(205, 370, "->  demand for delivery-capable talent", size=10.2, color=E_G, weight="bold")

box(431, 478, 318, 90, "#ffffff", E_R, lw=1.1)
txt(590, 544, "Structural risk", size=11.8, weight="bold", color=E_R)
txt(590, 508, "open sub-degree access (30.0%)\nbut lower offers (median 10.5 thousand/month)", size=9.6, color=INK2)
box(431, 392, 318, 76, "#ffffff", E_R, lw=1.1)
txt(590, 444, "Prospective risk", size=11.8, weight="bold", color=E_R)
txt(590, 412, "security requirement in only 1.5% of postings\nrequired by policy  |  not yet explicit in market",
    size=9.6, color=INK2)
txt(590, 370, "without intervention -> low-level cycle and systemic risk", size=8.8, color=E_R, weight="bold")

box(816, 530, 318, 38, "#ffffff", E_A, lw=1.3)
txt(975, 549, "Strategy: bounded anticipation", size=11.4, weight="bold", color=E_A)
for i, q in enumerate(["Objectives", "Modules", "Projects", "Assessment"]):
    x = 818 + i * 82
    box(x, 452, 68, 66, "#ffffff", E_A, lw=1.2)
    txt(x + 34, 485, q, size=8.8, weight="bold")
box(816, 392, 318, 50, "#ffffff", E_A, lw=1.0)
txt(826, 428, "translation matrix: policy -> tasks -> curriculum -> assessment", size=8.0, color=INK2, ha="left")
txt(826, 408, "JD-R analogy: resource generation and sustained competence", size=8.0, color=E_A, ha="left")

arrow((380, 470), (414, 470), color=E_G, lw=2.6)
arrow((765, 470), (799, 470), color=E_R, lw=2.6)
for x in (205, 590, 975):
    arrow((x, 350), (x, 337), color=EDGE, lw=1.8, ms=11)

box(30, 258, 1140, 77, C_S, E_S)
txt(600, 314, "Sustainable Development Goal anchors", size=11.4, weight="bold", color=E_S)
txt(600, 286, "SDG 4 quality education: skill supply is part of the sustainability of the education system"
              "          |          "
              "SDG 8 decent work: open access must be matched by capability completeness and returns",
    size=9.8, color=INK2)
arrow((600, 258), (600, 247), color=E_S, lw=1.9, ms=12)
box(30, 140, 1140, 105, "#f4f4f4", EDGE, lw=1.2)
txt(600, 228, "Overall judgement", size=11.4, weight="bold")
txt(600, 182, "The sustainability of talent supply depends on the completeness of the capability structure, not on\n"
              "how wide the formal access is: the threshold decides who may enter, the structure decides who can endure.",
    size=10.4, color=INK2)
save(fig, "fig2_sustainability_framework.png")

# ===================== Figure 3. Screening process =====================
fig, ax = plt.subplots(figsize=(6.6, 4.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10.6)
ax.axis("off")
steps = [
    ("Raw records  665", "BOSS Zhipin, 10 cities in Guangdong, 9 search terms, 25 Sep 2026", C_GRAY, "#F4F4F2"),
    ("Exact-link deduplication", "0 duplicate links removed", C_BLUE, "#EDF3FA"),
    ("Near-duplicate review", "31 duplicate releases removed (similarity >= 0.95)", C_AMBER, "#FCF6EA"),
    ("Relevance screening", "110 unrelated records removed (manufacturing, hardware, labelling, ...)", C_BLUE, "#EDF3FA"),
    ("Analytic sample  524", "78.8% retention; used for access, capability and salary analysis", C_TEAL, "#EEF6F2"),
]
y = 9.6
for i, (t, sub, col, bg) in enumerate(steps):
    h = 1.25
    ax.add_patch(FancyBboxPatch((0.5, y - h), 9.0, h, boxstyle="round,pad=0.05,rounding_size=0.1",
                                linewidth=1.2, edgecolor=col, facecolor=bg, zorder=1))
    ax.text(5.0, y - 0.43, t, ha="center", va="center", fontsize=10.4, color=col,
            fontweight="bold", zorder=2)
    ax.text(5.0, y - 0.92, sub, ha="center", va="center", fontsize=7.8, color="#4A4A4A", zorder=2)
    if i < len(steps) - 1:
        ax.add_patch(FancyArrowPatch((5.0, y - h), (5.0, y - h - 0.52), arrowstyle="-|>",
                                     mutation_scale=13, linewidth=1.4, color=C_LINE, zorder=1))
    y -= h + 0.52
save(fig, "fig3_screening_process.png")

# ===================== Figure 4. Education and experience =====================
edu_order = [("Bachelor's", "本科"), ("Associate", "大专"), ("No threshold", "学历不限"),
             ("Master's", "硕士"), ("Doctoral", "博士"), ("Secondary voc.", "中专/中技"),
             ("High school", "高中"), ("Junior high or below", "初中及以下")]
ex_order = [("1-3 years", "1-3年"), ("3-5 years", "3-5年"), ("No threshold", "经验不限"),
            ("5-10 years", "5-10年"), ("Students / recent grad.", "在校/应届"),
            ("Not stated", "(空)"), ("More than 10 years", "10年以上"), ("Up to 1 year", "1年以内")]
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6))
ev = [J["edu"].get(k, 0) for _, k in edu_order]
lbl = [e for e, _ in edu_order]
cols = [C_BLUE if k == "本科" else (C_TEAL if k == "大专" else (C_AMBER if k == "学历不限" else C_GRAY))
        for _, k in edu_order]
axes[0].barh(lbl, ev, color=cols, height=.62)
axes[0].invert_yaxis()
for i, v in enumerate(ev):
    axes[0].text(v + 4, i, "%d (%.1f%%)" % (v, v / N * 100), va="center", fontsize=7.4)
axes[0].set_xlim(0, max(ev) * 1.42)
axes[0].set_title("(a) Education requirement (n = %d)" % N, fontsize=9.6)
axes[0].spines[["top", "right", "bottom"]].set_visible(False)
axes[0].tick_params(axis="both", length=0, labelsize=8.0)

xv = [J["exp"].get(k, 0) for _, k in ex_order]
axes[1].barh([e for e, _ in ex_order], xv,
             color=[C_PURP if k in ("经验不限", "在校/应届") else C_GRAY for _, k in ex_order], height=.62)
axes[1].invert_yaxis()
for i, v in enumerate(xv):
    axes[1].text(v + 4, i, "%d (%.1f%%)" % (v, v / N * 100), va="center", fontsize=7.4)
axes[1].set_xlim(0, max(xv) * 1.42)
axes[1].set_title("(b) Experience requirement (purple = entry routes)", fontsize=9.6)
axes[1].spines[["top", "right", "bottom"]].set_visible(False)
axes[1].tick_params(axis="both", length=0, labelsize=8.0)
plt.tight_layout()
save(fig, "fig4_education_experience.png")

# ===================== Figure 5. Potential sub-degree accessibility =====================
FAM_EN = {"① 交付实施族（FDE型）": "Delivery and implementation\n(FDE type)",
          "② 解决方案/售前族": "Solutions and pre-sales",
          "③ 研发算法族": "Research, development\nand algorithms",
          "④ 产品运营族": "Product and operations",
          "⑤ AI应用/工具族": "AI applications and tools",
          "⑥ 其他": "Other related roles"}
fam = pd.DataFrame(J["family"])
fam["EN"] = fam["岗位族"].map(FAM_EN)
fam = fam.sort_values("潜在可及率", ascending=True)
fig, ax = plt.subplots(figsize=(6.9, 3.5))
cols = []
for k in fam["岗位族"]:
    cols.append(C_TEAL if "交付实施" in k else (C_RED if "研发算法" in k else
                (C_BLUE if "解决方案" in k else C_GRAY)))
lo = fam["潜在可及率"] - fam["CI_low"]
hi = fam["CI_high"] - fam["潜在可及率"]
ax.barh(fam["EN"], fam["潜在可及率"], color=cols, height=.6,
        xerr=np.vstack([lo.values, hi.values]),
        error_kw=dict(ecolor="#5A5A5A", lw=1, capsize=3))
for i, (v, nn) in enumerate(zip(fam["潜在可及率"], fam["n"])):
    ax.text(v + 1.8, i, "%.1f%% (n = %d)" % (v, nn), va="center", fontsize=8.2)
ax.set_xlim(0, 74)
ax.set_xlabel("Potential sub-degree accessibility (%, including no-threshold postings; Wilson 95% CI)",
              fontsize=8.4)
ax.set_title("Potential sub-degree accessibility by job family", fontsize=10.0)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=8.2)
ax.tick_params(axis="x", labelsize=7.8)
save(fig, "fig5_family_accessibility.png")

# ===================== Figure 6. Capability coverage =====================
cov = J["dim_coverage"]
ORD = [("Can deliver", "能交付"), ("Understands business", "懂业务"),
       ("Masters models", "通模型"), ("Knows security", "知安全")]
vals = [cov[k]["rate"] for _, k in ORD]
los = [cov[k]["rate"] - cov[k]["lo"] for _, k in ORD]
his = [cov[k]["hi"] - cov[k]["rate"] for _, k in ORD]
fig, ax = plt.subplots(figsize=(6.9, 3.05))
ax.barh([e for e, _ in ORD], vals, color=[C_TEAL, C_BLUE, C_PURP, C_RED], height=.55,
        xerr=np.vstack([los, his]), error_kw=dict(ecolor="#5A5A5A", lw=1, capsize=3))
ax.invert_yaxis()
for i, (v, (_, k)) in enumerate(zip(vals, ORD)):
    ax.text(v + 2.0, i, "%.1f%%  (%d/%d)" % (v, cov[k]["k"], N), va="center", fontsize=8.4,
            color=C_RED if k == "知安全" else "#2B2B2B",
            fontweight="bold" if k == "知安全" else "normal")
ax.set_xlim(0, 88)
ax.set_xlabel("Posting coverage (%, Wilson 95% CI)", fontsize=8.4)
ax.set_title("Posting coverage of the four policy capabilities\n(Cochran's Q = %.2f, df = %d, p < 0.001)"
             % (J["cochran_q"]["Q"], J["cochran_q"]["df"]), fontsize=9.8)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=8.6)
ax.tick_params(axis="x", labelsize=7.8)
save(fig, "fig6_capability_coverage.png")

# ===================== Figure 7. Co-occurrence matrix =====================
co = J["co4"]
SHORT = {"懂业务": "Business", "通模型": "Models", "知安全": "Security", "能交付": "Delivery"}
KEY = ["懂业务", "通模型", "知安全", "能交付"]
X = np.array([[co["%s|%s" % (a, b)] for b in KEY] for a in KEY], dtype=float)
fig, ax = plt.subplots(figsize=(5.0, 4.2))
im = ax.imshow(X, cmap="BuGn", vmin=0, vmax=X.max())
for i in range(4):
    for j in range(4):
        v = int(X[i, j])
        ax.text(j, i, str(v), ha="center", va="center", fontsize=9.4,
                color="white" if v > X.max() * 0.55 else "#2B2B2B",
                fontweight="bold" if i == j else "normal")
ax.set_xticks(range(4))
ax.set_xticklabels([SHORT[k] for k in KEY], fontsize=8.8)
ax.set_yticks(range(4))
ax.set_yticklabels([SHORT[k] for k in KEY], fontsize=8.8)
ax.set_title("Co-occurrence of the four policy capabilities (n = %d)\n"
             "diagonal: single-capability hits; off-diagonal: joint hits" % N, fontsize=9.4)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(length=0)
save(fig, "fig7_cooccurrence_matrix.png")

# ===================== Figure 8. Salary by education (delivery family) =====================
d = pd.read_csv(S3, dtype=str, keep_default_na=False)
d["s"] = pd.to_numeric(d["salary_midpoint_k_cny_per_month"], errors="coerce")
fam1 = d[d["job_family"].str.startswith("①")]
groups = [("Associate degree\nor below", "专科及以下"), ("No education\nthreshold", "学历不限"),
          ("Bachelor's\ndegree", "本科"), ("Master's degree\nor above", "硕士")]
data = [fam1[fam1["education_group"] == zh]["s"].dropna().values for _, zh in groups]
fig, ax = plt.subplots(figsize=(6.6, 3.5))
bp = ax.boxplot(data, tick_labels=["%s\n(n = %d)" % (en.split("\n")[0], len(x)) for (en, _), x in zip(groups, data)],
                patch_artist=True, widths=.52, showfliers=True,
                flierprops=dict(marker="o", markersize=3.2, markerfacecolor="#999999",
                                markeredgecolor="none", alpha=.55),
                medianprops=dict(color=C_RED, linewidth=1.8))
for patch, c in zip(bp["boxes"], [C_TEAL, C_AMBER, C_BLUE, C_PURP]):
    patch.set_facecolor(c)
    patch.set_alpha(.30)
    patch.set_edgecolor(c)
    patch.set_linewidth(1.2)
for i, x in enumerate(data):
    ax.text(i + 1, np.median(x) + 2.4, "%.1f" % np.median(x), ha="center", fontsize=8.6,
            color=C_RED, fontweight="bold")
ax.set_ylabel("Posted salary (CNY thousand / month)", fontsize=8.8)
ax.set_ylim(0, min(80, max(np.concatenate([x for x in data if len(x)])) * 1.12))
ax.set_title("Salary distribution by education requirement within the delivery and\n"
             "implementation family (Kruskal-Wallis H = 28.863, p < 0.001)", fontsize=9.6)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(axis="x", labelsize=8.2)
ax.tick_params(axis="y", labelsize=7.8)
save(fig, "fig8_salary_by_education.png")

print()
print("箱线图分组样本量：", [(en.replace(chr(10), " "), len(x)) for (en, _), x in zip(groups, data)],
      " 合计 =", sum(len(x) for x in data))
print("输出目录：", FIG)
