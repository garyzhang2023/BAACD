# -*- coding: utf-8 -*-
"""make_figs_en_v2.py —— §3 Results 图件重绘（scientific-figure-making / figures4papers house style）

相对 v1（make_figs_en.py）的实质改动 —— 每一条都对应一处已核实的缺陷：
  Fig 4  统一横轴为百分比（v1 两子图量程 0-400 vs 0-200，条长不可比）；补 Wilson 95% CI；
         语义配色（可及 / 不限 / 本科 / 研究生）；补 22.3% 与 33.0% 入口路径累计注记
  Fig 5  n 并入 y 轴标签，消除数值标签与误差棒右端重叠（v1 有 5 处重叠）；
         补 Delivery vs R&D 显著性括号与 30.0% 参考线；语义配色并加图例
  Fig 6  改断轴（0-4.5 / 44-74）。v1 单一 0-88 轴下「知安全 1.5%」条不可读，
         而该条正是全文论断的支点
  Fig 7  补颜色标尺；对角线（边缘覆盖）与交叉格（成对共现）分别标注；澄清
         「成对共现 ≤5 条」与正文「无任何含安全精确组合超过 2 条」不矛盾；补 ≥3 维注记
  Fig 8  改 y 断轴（0-80 / 95-165）。v1 ylim=80 静默截断 105 与 155 两例，
         而 155 正是正文与 Table 9 注专门做稳健性检验的值；补显著性括号与均值菱形
  Fig X  新增候选图：安全治理分层测量阶梯 + 基准词对照（§3.4 在 v1 中无任何图）

数据来源（口径 n = 524，与稿件一致）：
  论文分析/_专家版_指标.json
  补充材料-Supplementary/S3_Anonymized_Dataset/postings_derived_anonymized.csv
输出：<FIGROOT>/figs_en_v2/   （PNG 600 dpi ＋ PDF 矢量，均带白底）
"""
import io
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

# ============================== house style ==============================
# 依据 scientific-figure-making/references/design-theory.md §1 §8 §9
PALETTE = {
    "blue_main": "#0F4D92", "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE", "green_2": "#AADCA9", "green_3": "#8BCF8B",
    "red_1": "#F6CFCB", "red_2": "#E9A6A1", "red_strong": "#B64342",
    "neutral": "#CFCECE", "highlight": "#FFD700",
    "teal": "#42949E", "violet": "#9A4D8E",
}
BLUE, BLUE2 = PALETTE["blue_main"], PALETTE["blue_secondary"]
GRAY, GRAY_LT = "#888780", "#B4B2A9"
RED, TEAL, VIOLET = PALETTE["red_strong"], PALETTE["teal"], PALETTE["violet"]
INK, INK2 = "#2B2B2B", "#5F5E5A"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.9,
    "axes.unicode_minus": False,
    "legend.frameon": False,
    "svg.fonttype": "none",
    "figure.dpi": 600,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.06,
    "savefig.facecolor": "white",
})

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
FIG = os.path.join(FIGROOT, "figs_en_v2")
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
D = pd.read_csv(S3, dtype=str, keep_default_na=False)
assert len(D) == N == 524, "S3 行数 %d 与 n=%d 不符" % (len(D), N)


def wilson(k, n, z=1.96):
    """Wilson score interval，返回百分数区间。与稿件 Table 4/6/7 口径一致。"""
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, (c - h) * 100.0), min(100.0, (c + h) * 100.0)


def flag(col):
    return D[col].astype(str).str.strip().isin(["1", "1.0", "True", "true", "是", "Y"]).values


LOG = []


def save(fig, name, note=""):
    png = os.path.join(FIG, name + ".png")
    pdf = os.path.join(FIG, name + ".pdf")
    fig.savefig(png, dpi=600)
    fig.savefig(pdf)
    plt.close(fig)
    im = Image.open(png)
    dpi = im.info.get("dpi", (600,))[0]
    assert dpi >= 599, "%s dpi=%s 未达 600" % (name, dpi)
    row = "  %-40s %5dx%-5d %d dpi  width=%.2f in" % (name + ".png", im.size[0], im.size[1],
                                                      dpi, im.size[0] / dpi)
    print(row)
    LOG.append(row + ("   " + note if note else ""))


def bracket(ax, x1, x2, y, drop, text, fs=7.2, lw=0.9, color=INK2, va="bottom"):
    """显著性括号（顶横线 + 两侧下垂短线 + 文字）。"""
    ax.plot([x1, x1, x2, x2], [y - drop, y, y, y - drop], color=color, lw=lw,
            clip_on=False, zorder=6, solid_capstyle="butt")
    ax.text((x1 + x2) / 2.0, y + (1.5 if va == "bottom" else -1.5), text,
            ha="center", va=va, fontsize=fs, color=color, zorder=6)


def break_marks_x(axL, axR, d=0.020, color=INK2):
    """横向断轴标记（底部）。"""
    for ax, x in ((axL, 1.0), (axR, 0.0)):
        ax.plot((x - d, x + d), (-d * 1.8, d * 1.8), transform=ax.transAxes,
                color=color, clip_on=False, lw=1.2, zorder=7, solid_capstyle="butt")


def break_marks_y(axT, axB, d=0.012, color=INK2, both_sides=False):
    """纵向断轴标记。左侧必画；右侧仅在坐标轴可见时才画（否则会浮空）。"""
    sides = [(-d, d), (1 - d, 1 + d)] if both_sides else [(-d, d)]
    for xs in sides:
        kw = dict(transform=axT.transAxes, color=color, clip_on=False, lw=1.1,
                  zorder=7, solid_capstyle="butt")
        axT.plot(xs, (-d, d), **kw)
        kw.update(transform=axB.transAxes)
        axB.plot(xs, (1 - d, 1 + d), **kw)


print("=" * 92)
print("make_figs_en_v2.py —— Results 图件重绘")
print("=" * 92)

# ==================== Figure 4. Education and experience ====================
edu = [("Bachelor's degree", "本科", 318, GRAY),
       ("Associate degree", "大专", 103, BLUE),
       ("No education threshold", "学历不限", 56, BLUE2),
       ("Master's degree", "硕士", 23, GRAY_LT),
       ("Doctoral degree", "博士", 10, GRAY_LT),
       ("Secondary vocational", "中专/中技", 10, BLUE),
       ("High school", "高中", 2, BLUE),
       ("Junior high or below", "初中及以下", 2, BLUE)]
exp = [("1-3 years", "1-3年", 143, GRAY),
       ("3-5 years", "3-5年", 120, GRAY),
       ("No experience threshold", "经验不限", 113, BLUE),
       ("5-10 years", "5-10年", 65, GRAY),
       ("Students or recent graduates", "在校/应届", 31, BLUE),
       ("Not stated", "(空)", 24, GRAY_LT),
       ("More than 10 years", "10年以上", 19, GRAY),
       ("Up to 1 year", "1年以内", 9, BLUE2)]

for lab, zh, k, _ in edu + exp:
    assert J["edu"].get(zh, J["exp"].get(zh)) == k, "计数不符: %s" % lab

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.95))
XLIM = 82.0
for ax, rows, ttl, agg in (
        (axes[0], edu, "(a) Education requirement",
         "Direct sub-degree access  22.3%\n(95% CI 19.0-26.1)\n\nIncl. no-threshold  33.0%\n(95% CI 29.1-37.2)"),
        (axes[1], exp, "(b) Experience requirement",
         "Entry-level routes  27.5%\n(no threshold or student)\n\nIncl. up to 1 year  29.2%")):
    y = np.arange(len(rows))
    ks = np.array([r[2] for r in rows], dtype=float)
    share = ks / N * 100.0
    lo = np.array([wilson(int(k), N)[0] for k in ks])
    hi = np.array([wilson(int(k), N)[1] for k in ks])
    ax.barh(y, share, color=[r[3] for r in rows], height=0.66,
            edgecolor="black", linewidth=0.55, zorder=3)
    ax.errorbar(share, y, xerr=[share - lo, hi - share], fmt="none",
                ecolor="#4D4D4D", elinewidth=0.9, capsize=2.4, capthick=0.9, zorder=4)
    for i, (s, k, h) in enumerate(zip(share, ks, hi)):
        ax.text(h + 2.2, i, "%d (%.1f%%)" % (k, s), va="center", ha="left",
                fontsize=7.0, color=INK, zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.8)
    ax.invert_yaxis()
    ax.set_xlim(0, XLIM)
    ax.set_xticks([0, 20, 40, 60, 80])
    ax.set_xticklabels(["0", "20", "40", "60", "80"], fontsize=7.4)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=7.4, length=2.2)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Share of valid postings (%, Wilson 95% CI)", fontsize=8.0)
    ax.set_title(ttl, fontsize=9.6, pad=6)
    ax.text(0.985, 0.035, agg, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.0, color=INK2, linespacing=1.45, zorder=5)

lg = [plt.Rectangle((0, 0), 1, 1, fc=BLUE, ec="black", lw=0.55),
      plt.Rectangle((0, 0), 1, 1, fc=BLUE2, ec="black", lw=0.55),
      plt.Rectangle((0, 0), 1, 1, fc=GRAY, ec="black", lw=0.55),
      plt.Rectangle((0, 0), 1, 1, fc=GRAY_LT, ec="black", lw=0.55)]
fig.legend(lg,
           ["Sub-degree entry route", "No threshold / up to 1 year", "Threshold above entry route",
            "Not stated"],
           loc="lower center", ncol=4, fontsize=7.2, frameon=False,
           bbox_to_anchor=(0.5, -0.035), handlelength=1.1, handleheight=0.85,
           columnspacing=1.4)
fig.tight_layout()
save(fig, "fig4_education_experience", "统一 % 轴 + Wilson CI（v1 两子图量程不同）")

# ==================== Figure 5. Potential sub-degree accessibility ====================
FAM_EN = {"① 交付实施族（FDE型）": "Delivery and implementation (FDE type)",
          "② 解决方案/售前族": "Solutions and pre-sales",
          "③ 研发算法族": "Research, development and algorithms",
          "④ 产品运营族": "Product and operations",
          "⑤ AI应用/工具族": "AI applications and tools",
          "⑥ 其他": "Other related roles"}
fam = pd.DataFrame(J["family"])
fam["EN"] = fam["岗位族"].map(FAM_EN)
fam = fam.sort_values("潜在可及率").reset_index(drop=True)
roles = []
for k in fam["岗位族"]:
    roles.append(BLUE if "交付实施" in k else (RED if "研发算法" in k else GRAY))

fig, ax = plt.subplots(figsize=(7.2, 3.5))
y = np.arange(len(fam))
v = fam["潜在可及率"].values
lo, hi = fam["CI_low"].values, fam["CI_high"].values
ax.barh(y, v, color=roles, height=0.62, edgecolor="black", linewidth=0.55, zorder=3)
ax.errorbar(v, y, xerr=[v - lo, hi - v], fmt="none", ecolor="#4D4D4D",
            elinewidth=0.9, capsize=2.4, zorder=4)
for i, s in enumerate(v):
    ax.text(hi[i] + 1.3, i, "%.1f%%" % s, va="center", ha="left", fontsize=7.6,
            color=INK, zorder=5)

ax.axvline(30.0, color=BLUE, lw=0.9, ls=(0, (4, 3)), zorder=2)
ax.text(30.6, 5.52, "Delivery and implementation 30.0%", fontsize=7.0,
        color=BLUE, ha="left", va="center", zorder=5)

i_del = int(np.where(fam["岗位族"].str.contains("交付实施").values)[0][0])
i_res = int(np.where(fam["岗位族"].str.contains("研发算法").values)[0][0])
xl = max(hi) + 5.0
ax.plot([xl + 2.0, xl, xl, xl + 2.0], [i_res, i_res, i_del, i_del],
        color=INK2, lw=0.9, zorder=6)
ax.text(xl - 1.0, (i_del + i_res) / 2.0,
        "chi2 = 10.26\np = 0.001\nOR = 2.65",
        ha="right", va="center", fontsize=6.9, color=INK2, linespacing=1.45, zorder=6)

ax.set_yticks(y)
ax.set_yticklabels(["%s  (n = %d)" % (r.EN, r.n) for r in fam.itertuples()], fontsize=7.8)
ax.set_xlim(0, 78)
ax.set_ylim(-0.62, 5.95)
ax.set_xticks([0, 20, 40, 60])
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", labelsize=7.4, length=2.2)
ax.spines["left"].set_visible(False)
ax.set_xlabel("Potential sub-degree accessibility (%, incl. no-threshold; Wilson 95% CI)",
              fontsize=8.0)
ax.set_title("Potential sub-degree accessibility by job family", fontsize=9.6, pad=6)
lg = [plt.Rectangle((0, 0), 1, 1, fc=BLUE, ec="black", lw=0.55),
      plt.Rectangle((0, 0), 1, 1, fc=RED, ec="black", lw=0.55),
      plt.Rectangle((0, 0), 1, 1, fc=GRAY, ec="black", lw=0.55)]
fig.legend(lg, ["Policy focus (delivery and implementation)",
                "Contrast (research and algorithms)", "Other families"],
           loc="lower center", ncol=3, fontsize=7.0, frameon=False,
           bbox_to_anchor=(0.5, -0.045), handlelength=1.1, handleheight=0.85,
           columnspacing=1.6)
fig.tight_layout()
save(fig, "fig5_family_accessibility", "标签/误差棒不再重叠 + 显著性括号（v1 有 5 处重叠）")

# ==================== Figure 6. Capability coverage (broken axis) ====================
cov = J["dim_coverage"]
ROWS6 = [("Knows security", "知安全", RED, "8/524"),
         ("Masters models", "通模型", VIOLET, "268/524"),
         ("Understands business", "懂业务", BLUE, "279/524"),
         ("Can deliver", "能交付", BLUE2, "343/524")]
v = np.array([cov[z]["rate"] for _, z, _, _ in ROWS6])
lo = np.array([cov[z]["lo"] for _, z, _, _ in ROWS6])
hi = np.array([cov[z]["hi"] for _, z, _, _ in ROWS6])
for k in ("知安全",):
    w = wilson(cov[k]["k"], N)
    assert abs(w[0] - cov[k]["lo"]) < 0.02 and abs(w[1] - cov[k]["hi"]) < 0.02, "Wilson 口径不符"

fig, (axL, axR) = plt.subplots(
    1, 2, figsize=(7.0, 2.95), sharey=True,
    gridspec_kw=dict(width_ratios=[1.0, 4.1]))
y6 = np.arange(len(ROWS6))
for ax in (axL, axR):
    ax.barh(y6, v, color=[c for _, _, c, _ in ROWS6], height=0.56,
            edgecolor="black", linewidth=0.55, zorder=3)
    ax.errorbar(v, y6, xerr=[v - lo, hi - v], fmt="none", ecolor="#4D4D4D",
                elinewidth=0.9, capsize=2.4, zorder=4)
axL.set_xlim(0, 4.6)
axR.set_xlim(44, 74)
for i in (1, 2, 3):
    axR.text(hi[i] + 0.9, i, "%.1f%%" % v[i], va="center", ha="left", fontsize=7.8,
             color=INK, zorder=5)
axL.text(hi[0] + 0.18, 0, "%.1f%%" % v[0], va="center", ha="left", fontsize=7.8,
         color=RED, fontweight="bold", zorder=5)
axL.set_yticks(y6)
axL.set_yticklabels(["%s  (%s)" % (nm, nn) for nm, _, _, nn in ROWS6], fontsize=7.8)
axL.tick_params(axis="y", length=0)
axL.tick_params(axis="x", labelsize=7.2, length=2.2)
axR.tick_params(axis="y", left=False, labelleft=False, length=0)
axR.tick_params(axis="x", labelsize=7.2, length=2.2)
axL.spines["left"].set_visible(False)
axR.spines["left"].set_visible(False)
break_marks_x(axL, axR)
fig.text(0.53, -0.045, "Posting coverage (% of 524; Wilson 95% CI)  —  broken axis, 0-4.5 then 44-74",
         ha="center", va="center", fontsize=8.0, color=INK)
fig.suptitle("Posting coverage of the four policy capabilities\n"
             "(Cochran's Q = %.2f, df = %d, p < 0.001)"
             % (J["cochran_q"]["Q"], J["cochran_q"]["df"]), fontsize=9.6, y=1.02)
fig.tight_layout()
fig.subplots_adjust(wspace=0.05)   # 断轴两段需紧贴（tight_layout 不接受 gridspec_kw 里的 wspace）
save(fig, "fig6_capability_coverage", "断轴使「知安全 1.5%」可辨（v1 单一 0-88 轴下不可读）")

# ==================== Figure 7. Co-occurrence matrix ====================
co = J["co4"]
KEY = [("懂业务", "Business"), ("通模型", "Models"), ("知安全", "Security"), ("能交付", "Delivery")]
X = np.array([[co["%s|%s" % (a, b)] for b, _ in KEY] for a, _ in KEY], dtype=float)
names = [en for _, en in KEY]
assert X.shape == (4, 4) and X[0, 0] == 279 and X[3, 3] == 343, "共现矩阵与稿件不符"

fig, ax = plt.subplots(figsize=(5.6, 4.3))
im = ax.imshow(X, cmap="Blues", vmin=0, vmax=X.max())
for i in range(4):
    for j in range(4):
        val = int(X[i, j])
        ax.text(j, i - 0.11, str(val), ha="center", va="center", fontsize=9.0,
                color="white" if val > X.max() * 0.55 else INK,
                fontweight="bold" if i == j else "normal", zorder=4)
        ax.text(j, i + 0.20, "%.1f%%" % (val / N * 100), ha="center", va="center",
                fontsize=6.4, color="#EAF0F7" if val > X.max() * 0.55 else INK2, zorder=4)
# 对角线为边缘覆盖，语义不同：加斜线纹理示意
for i in range(4):
    ax.add_patch(plt.Rectangle((i - 0.5, i - 0.5), 1, 1, fill=False, hatch="//",
                               edgecolor="white", lw=0, alpha=0.16, zorder=3))
cb = fig.colorbar(im, ax=ax, fraction=0.042, pad=0.03)
cb.set_label("Number of postings", fontsize=7.6)
cb.ax.tick_params(labelsize=7.0, length=2.0)
cb.outline.set_linewidth(0.5)
ax.set_xticks(range(4))
ax.set_xticklabels(names, fontsize=8.0)
ax.set_yticks(range(4))
ax.set_yticklabels(names, fontsize=8.0)
ax.set_xticks(np.arange(-0.5, 4, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 4, 1), minor=True)
ax.grid(which="minor", color="white", lw=0.8)
ax.tick_params(which="both", length=0)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_title("Co-occurrence of the four policy capabilities (n = 524)\n"
             "diagonal (hatched) = marginal coverage; off-diagonal = pairwise joint hits",
             fontsize=8.8, pad=7)
ax.text(0.5, -0.135,
        "At least three capabilities co-occurred in 140 postings (26.7%). Pairwise hits with\n"
        "Security reach 5, yet no exact capability combination containing Security exceeds 2 postings.",
        transform=ax.transAxes, ha="center", va="top", fontsize=6.8, color=INK2, linespacing=1.45)
fig.tight_layout()
save(fig, "fig7_cooccurrence_matrix", "补 色标 + 对角线区分 + 成对/精确组合澄清（v1 无色标）")

# ==================== Figure 8. Salary by education (broken y-axis) ====================
d = D.copy()
d["s"] = pd.to_numeric(d["salary_midpoint_k_cny_per_month"], errors="coerce")
fam1 = d[d["job_family"].str.startswith("①")]
GRP = [("Associate degree\nor below", "专科及以下", BLUE),
       ("No education\nthreshold", "学历不限", GRAY_LT),
       ("Bachelor's\ndegree", "本科", GRAY),
       ("Master's degree\nor above", "硕士", GRAY_LT)]
data = [fam1[fam1["education_group"] == zh]["s"].dropna().values for _, zh, _ in GRP]
assert [len(x) for x in data] == [36, 12, 102, 7], "分组样本量与稿件不符"
assert max(np.concatenate(data)) == 155.0 and sum(len(x) for x in data) == 157

YLO, YHI = 80.0, 95.0
fig, (axT, axB) = plt.subplots(
    2, 1, figsize=(6.8, 4.5), sharex=True,
    gridspec_kw=dict(height_ratios=[1.0, 3.5]))
labels = ["%s\n(n = %d)" % (en, len(x)) for (en, _, _), x in zip(GRP, data)]
for ax in (axT, axB):
    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, widths=0.5,
                    showfliers=True,
                    flierprops=dict(marker="o", markersize=2.6, markerfacecolor="#7A7A7A",
                                    markeredgecolor="none", alpha=0.6),
                    medianprops=dict(color=RED, linewidth=1.6),
                    whiskerprops=dict(color=INK, linewidth=0.9),
                    capprops=dict(color=INK, linewidth=0.9),
                    boxprops=dict(linewidth=0.9))
    for patch, (_, _, c) in zip(bp["boxes"], GRP):
        patch.set_facecolor(c)
        patch.set_alpha(0.30)
        patch.set_edgecolor(c)
    for i, x in enumerate(data):
        ax.plot(i + 1, x.mean(), marker="D", markersize=3.4, markerfacecolor="white",
                markeredgecolor=INK, markeredgewidth=0.8, zorder=6)
axT.set_ylim(YHI, 170)
axB.set_ylim(0, YLO)
axT.spines["bottom"].set_visible(False)
axB.spines["top"].set_visible(False)
axT.tick_params(axis="x", bottom=False, labelbottom=False)
axT.tick_params(axis="y", labelsize=7.4, length=2.2)
axB.tick_params(axis="y", labelsize=7.4, length=2.2)
axB.tick_params(axis="x", labelsize=7.6, length=0)
axB.set_xlim(0.38, 4.80)
break_marks_y(axT, axB, both_sides=False)

for i, x in enumerate(data):
    axB.text(i + 1.30, np.median(x), "%.1f" % np.median(x), ha="left", va="center",
             fontsize=7.6, color=RED, fontweight="bold", zorder=7)
bracket(axB, 1, 3, 75, 6, "Mann-Whitney U = 705.5, p < 0.001, Cliff's delta = -0.616", fs=7.0)
axT.annotate("2 postings at 105 and 155\n(shown in full; see Table 9 note)",
             xy=(3, 155), xytext=(3.42, 126), fontsize=6.8, color=INK2, linespacing=1.4,
             arrowprops=dict(arrowstyle="-", color=GRAY, lw=0.7, shrinkA=0, shrinkB=2))
axT.text(0.012, 0.90, "box = IQR;  red line = median;  diamond = mean\n"
                      "n = 7 and n = 12 groups: IQR is unstable, read medians only",
         transform=axT.transAxes, ha="left", va="top", fontsize=6.6, color=INK2, linespacing=1.5)
fig.text(0.028, 0.5, "Posted salary (CNY thousand / month)", rotation=90,
         ha="center", va="center", fontsize=8.4, color=INK)
fig.suptitle("Salary distribution by education requirement within the delivery and implementation\n"
             "family (Kruskal-Wallis H = 28.863, p < 0.001; broken y-axis: 0-80 then 95-170)",
             fontsize=9.2, y=1.02)
fig.tight_layout(rect=(0.045, 0, 1, 1))
fig.subplots_adjust(hspace=0.08)   # 断轴上下两段需紧贴
save(fig, "fig8_salary_by_education",
     "y 断轴如实显示 105/155（v1 ylim=80 静默截断）+ 显著性括号")

# ==================== Figure X. Security measurement ladder (candidate, new) ====================
# Table 7 的十行须逐行齐备（正文写「report 7, 9, and 12 as progressively broader
# sensitivity counts」，缺 incl. boundary language = 7 一行会让阶梯断级）
T7 = [("Any security semantics (T1-T5)", 78, BLUE, "aggregate"),
      ("T5 Business compliance", 56, GRAY, "general"),
      ("T2 Data governance", 32, GRAY, "general"),
      ("T1 General information security", 14, GRAY, "general"),
      ("T3 union T4:\nautomated candidates", 12, RED, "aispec"),
      ("T3 union T4:\nincl. boundary + oversight", 9, RED, "aispec"),
      ("Structured security tags\n(Table 6)", 8, TEAL, "tags"),
      ("T3 union T4:\nincl. boundary language", 7, RED, "aispec"),
      ("T3 AI model security (regex)", 7, RED, "aispec"),
      ("T4 Ethical governance", 6, RED, "aispec"),
      ("T3 union T4: strict\n(manually verified)", 6, RED, "strict")]
assert [t[1] for t in T7] == sorted([t[1] for t in T7], reverse=True), "阶梯须按条数非递增排列"
k7 = {c: int(flag(c).sum()) for c in
      ["sec_any_T1toT5", "sec_T5_business_compliance", "sec_T2_data_governance",
       "sec_T1_general_infosec", "sec_ai_specific_candidate_T3orT4",
       "sec_T3_ai_model_safety", "sec_T4_ethics_governance"]}
assert k7["sec_any_T1toT5"] == 78 and k7["sec_T5_business_compliance"] == 56, "S3 与 Table 7 不符"
assert k7["sec_ai_specific_candidate_T3orT4"] == 12 and k7["sec_T2_data_governance"] == 32

BENCH = [("Communication", 274, GRAY), ("Training", 141, GRAY), ("On-site", 110, GRAY),
         ("Any security semantics", 78, BLUE), ("AI-specific security (strict)", 6, RED)]

fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.62), gridspec_kw=dict(width_ratios=[1.45, 1]))
ax = axes[0]
y = np.arange(len(T7))
vv = np.array([k7m / N * 100.0 for _, k7m, _, _ in T7])
lo = np.array([wilson(k7m, N)[0] for _, k7m, _, _ in T7])
hi = np.array([wilson(k7m, N)[1] for _, k7m, _, _ in T7])
ax.barh(y, vv, color=[c for _, _, c, _ in T7], height=0.62,
        edgecolor="black", linewidth=0.55, zorder=3)
ax.errorbar(vv, y, xerr=[vv - lo, hi - vv], fmt="none", ecolor="#4D4D4D",
            elinewidth=0.9, capsize=2.2, zorder=4)
for i, (_, k7m, _, kind) in enumerate(T7):
    ax.text(hi[i] + 0.45, i, "%d (%.2f%%)" % (k7m, vv[i]), va="center", ha="left",
            fontsize=6.9, color=RED if kind == "strict" else INK,
            fontweight="bold" if kind == "strict" else "normal", zorder=5)
ax.invert_yaxis()
ax.set_yticks(y)
ax.set_yticklabels([t[0] for t in T7], fontsize=7.2)
for tick, t in zip(ax.get_yticklabels(), T7):
    if t[3] == "strict":
        tick.set_color(RED)
        tick.set_fontweight("bold")
ax.tick_params(axis="y", length=0)
ax.tick_params(axis="x", labelsize=7.3, length=2.2)
ax.spines["left"].set_visible(False)
ax.set_xlim(0, 21)
ax.set_xlabel("Posting coverage (%, Wilson 95% CI)", fontsize=8.0)
ax.set_title("(a) Layered measurement of security-governance demand\n(levels overlap; counts are not additive)",
             fontsize=8.6, pad=6)
lg = [plt.Rectangle((0, 0), 1, 1, fc=BLUE, ec="black", lw=0.55),
      plt.Rectangle((0, 0), 1, 1, fc=GRAY, ec="black", lw=0.55),
      plt.Rectangle((0, 0), 1, 1, fc=TEAL, ec="black", lw=0.55),
      plt.Rectangle((0, 0), 1, 1, fc=RED, ec="black", lw=0.55)]
fig.legend(lg, ["Any security semantics", "General, not AI-specific",
                "Structured platform tags", "AI-specific"],
           loc="lower center", ncol=4, fontsize=7.0, frameon=False,
           bbox_to_anchor=(0.5, -0.045), handlelength=1.1, handleheight=0.85,
           columnspacing=1.6)

ax2 = axes[1]
y2 = np.arange(len(BENCH))
b = np.array([k / N * 100.0 for _, k, _ in BENCH])
blo = np.array([wilson(k, N)[0] for _, k, _ in BENCH])
bhi = np.array([wilson(k, N)[1] for _, k, _ in BENCH])
ax2.barh(y2, b, color=[c for _, _, c in BENCH], height=0.6,
         edgecolor="black", linewidth=0.55, zorder=3)
ax2.errorbar(b, y2, xerr=[b - blo, bhi - b], fmt="none", ecolor="#4D4D4D",
             elinewidth=0.9, capsize=2.2, zorder=4)
for i, (_, k7m, _) in enumerate(BENCH):
    ax2.text(bhi[i] + 1.2, i, "%.2f%%" % b[i], va="center", ha="left", fontsize=7.0,
             color=RED if i == len(BENCH) - 1 else INK,
             fontweight="bold" if i == len(BENCH) - 1 else "normal", zorder=5)
ax2.invert_yaxis()
ax2.set_yticks(y2)
ax2.set_yticklabels([t[0] for t in BENCH], fontsize=7.4)
ax2.tick_params(axis="y", length=0)
ax2.tick_params(axis="x", labelsize=7.3, length=2.2)
ax2.spines["left"].set_visible(False)
ax2.set_xlim(0, 72)
ax2.set_xlabel("Postings matched (%, Wilson 95% CI)", fontsize=8.0)
ax2.set_title("(b) Security language against\nbenchmark terms", fontsize=8.6, pad=6)
fig.tight_layout()

# ---- 版式自检：panel (a) 共 11 行标签，行距须大于最高标签实测字高（防压字） ----
fig.canvas.draw()
_rd = fig.canvas.get_renderer()
_bbs = [t.get_window_extent(_rd) for t in ax.get_yticklabels()]
_hmax = max(b.y1 - b.y0 for b in _bbs)
_pitch = abs(_bbs[0].y0 - _bbs[1].y0)
assert _pitch > 1.06 * _hmax, \
    "panel (a) 行距 %.1f px < 最高标签 %.1f px，会压字" % (_pitch, _hmax)
print("  panel (a) 行距自检：pitch=%.1f px，最高标签=%.1f px（%.2f 倍）→ 通过"
      % (_pitch, _hmax, _pitch / _hmax))

save(fig, "figX_security_measurement_candidate",
     "候选新图，建议插入 §3.4 作 Figure 8（v1 该节无图）")

print()
print("箱线图分组样本量：", [(en.replace(chr(10), " "), len(x)) for (en, _, _), x in zip(GRP, data)],
      " 合计 =", sum(len(x) for x in data))
print("输出目录：", FIG)
print("同时导出 PNG(600 dpi) 与 PDF(矢量)，可编辑文字。")
