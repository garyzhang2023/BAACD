# -*- coding: utf-8 -*-
"""make_figs_docx.py —— 图件链第 3 段：为 MDPI Word 版面适配图件，输出 figs_docx/。

执行顺序须知：本脚本会把 figs_en/fig3..fig8 复制进 figs_docx/，其中 fig4–fig8 为
v1 旧版；必须随后运行 build_figs_final.py 用 v2 重绘版覆盖并完成改名，
figs_docx/ 才是投稿所用的 9 张图。

与 figs_en/ 的差异（仅两处，其余 6 张原样复制）：
  * fig1 —— 修正 4 个内框相对色带的右偏移（原 gap 公式使末框越出色带 0.1 数据单位），
            并把旋转带标签改为 9pt 以保证不出带。
  * fig2 —— 原图 13.44 in 宽（设计画布 1200×730），缩到 7.10 in 后图内文字仅约 3pt。
            此处按页面重排为 7.10 × 6.25 in（画布 1000×880），
            结构改为「(1)(2) 并排 / (3) 通栏 / SDG 带 / 总体判断」，
            全部文字、数值与箭头语义保持不变。
"""
import os
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["savefig.dpi"] = 600
plt.rcParams["figure.dpi"] = 600

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
SRC = os.path.join(FIGROOT, "figs_en")
DST = os.path.join(FIGROOT, "figs_docx")
os.makedirs(DST, exist_ok=True)

C_TEAL, C_BLUE, C_PURP = "#0F6E56", "#185FA5", "#534AB7"
C_GRAY, C_RED, C_AMBER = "#5F5E5A", "#A32D2D", "#B7791F"


def save(fig, name):
    p = os.path.join(DST, name)
    fig.savefig(p, dpi=600, facecolor="white")
    plt.close(fig)
    from PIL import Image
    im = Image.open(p)
    print("  %-42s %5dx%-5d  width=%.2f in" % (name, im.size[0], im.size[1], im.size[0] / 600.0))


# ===================== Figure 1. Policy-job-education framework（修正内框越界）=====
fig, ax = plt.subplots(figsize=(6.9, 4.35))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8.1)
ax.axis("off")

X0, X1, W_BOX = 1.35, 9.65, 1.95          # 内框可用区间与单框宽度（原来用过 8.6 导致末框越界）


def band(y, h, label, items, color, bg):
    ax.add_patch(FancyBboxPatch((0.15, y), 9.7, h,
                                boxstyle="round,pad=0.05,rounding_size=0.12",
                                linewidth=1.1, edgecolor=color, facecolor=bg, zorder=1))
    ax.text(0.45, y + h / 2, label, ha="center", va="center", rotation=90,
            fontsize=9.0, color=color, fontweight="bold", zorder=3)
    n = len(items)
    gap = (X1 - X0 - n * W_BOX) / (n - 1) if n > 1 else 0
    for i, it in enumerate(items):
        x = X0 + i * (W_BOX + gap)
        ax.add_patch(FancyBboxPatch((x, y + h / 2 - 0.42), W_BOX, 0.84,
                                    boxstyle="round,pad=0.03,rounding_size=0.09",
                                    linewidth=1.0, edgecolor=color, facecolor="white", zorder=2))
        ax.text(x + W_BOX / 2, y + h / 2, it, ha="center", va="center", fontsize=8.9,
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

# ===================== Figure 2. Sustainability framework（按页面重排）=====
# 画布 1000 x 812 数据单位（x 0..1000, y 90..902）；figsize 7.10 x 5.765 in
# 1 单位 = 0.0071 in ≈ 0.5112 pt（x/y 等比，故字号可直接换算）
FIG_W_IN = 7.10
YLO, YHI = 90, 902
fig = plt.figure(figsize=(FIG_W_IN, (YHI - YLO) * FIG_W_IN / 1000.0))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 1000)
ax.set_ylim(YLO, YHI)
ax.axis("off")

INK, INK2, EDGE = "#1a1a1a", "#4a4a4a", "#8a8a8a"
C_G, E_G = "#fde9e0", "#d9541e"
C_R, E_R = "#fdeaea", "#bc2d2d"
C_A, E_A = "#e2eef7", "#1f6fb2"
C_S, E_S = "#e6f2e6", "#3d7a3d"

CHECKS = []          # (artist, (x0, y0, x1, y1), 说明) —— 供出框自检


def box(x, y, w, h, fc, ec, lw=1.6, r=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=%d" % r,
                                fc=fc, ec=ec, lw=lw, zorder=2))


def txt(x, y, s, size=9.0, color=INK, weight="normal", ha="center", lh=1.4, limit=None):
    t = ax.text(x, y, s, fontsize=size, color=color, ha=ha, va="center",
                fontweight=weight, linespacing=lh, zorder=4)
    if limit:
        CHECKS.append((t, limit, size, s[:44]))
    return t


def arrow(p1, p2, color=EDGE, lw=2.0, ms=14, ls="solid"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=ms,
                                 lw=lw, color=color, zorder=3, linestyle=ls))


txt(500, 875, "Sustainability framework for talent supply in AI application services",
    size=12.0, weight="bold", limit=(0, 858, 1000, 902))

# ---- (1) 与 (2) 并排；两框之间留 40 单位供横向箭头 ----
R1, R2 = (8, 630, 480, 860), (520, 630, 992, 860)
box(*[R1[0], R1[1], R1[2] - R1[0], R1[3] - R1[1]], C_G, E_G)
box(*[R2[0], R2[1], R2[2] - R2[0], R2[3] - R2[1]], C_R, E_R)
IN1 = (28, 640, 460, 806)      # (1) 内框可用区
IN2 = (540, 640, 972, 806)

txt(244, 844, "(1) Industrial scale targets", size=11.0, color=E_G, weight="bold", limit=R1)
txt(244, 825, "MIIT Circular No. 414", size=8.5, color=INK2, limit=R1)
ax.plot([48, 440], [813, 813], color=E_G, lw=0.9, alpha=0.55, zorder=3)
# 与 (2) 面板严格对称：上白框 3 行（规模目标）、下白框 3 行（服务团 → 人才需求）
box(28, 734, 432, 74, "#ffffff", E_G, lw=1.0)
txt(244, 793, "by end-2026  >= 2,000", size=10.0, weight="bold", limit=IN1)
txt(244, 772, "by end-2027  >= 3,000 providers", size=8.6, color=INK2, limit=IN1)
txt(244, 753, "pilot-zone provinces >= 100", size=8.6, color=INK2, limit=IN1)
box(28, 656, 432, 64, "#ffffff", E_G, lw=1.0)
txt(244, 704, ">= 10 service teams per province", size=9.6, weight="bold", limit=IN1)
txt(244, 684, "(1 lead + >= 2 upstream/downstream)", size=8.4, color=INK2, limit=IN1)
txt(244, 666, "->  demand for delivery-capable talent", size=8.4, color=E_G,
    weight="bold", limit=IN1)

txt(756, 844, "(2) Two sustainability risks", size=11.0, color=E_R, weight="bold", limit=R2)
txt(756, 825, "gap between policy and explicit market language", size=8.5, color=INK2, limit=R2)
ax.plot([560, 952], [813, 813], color=E_R, lw=0.9, alpha=0.55, zorder=3)
box(540, 734, 432, 74, "#ffffff", E_R, lw=1.0)
txt(756, 793, "Structural risk", size=10.0, weight="bold", color=E_R, limit=IN2)
txt(756, 772, "open sub-degree access (30.0%)", size=8.6, color=INK2, limit=IN2)
txt(756, 753, "but lower offers (median 10.5 thousand/month)", size=8.4, color=INK2, limit=IN2)
box(540, 656, 432, 64, "#ffffff", E_R, lw=1.0)
txt(756, 704, "Prospective risk", size=10.0, weight="bold", color=E_R, limit=IN2)
txt(756, 684, "security requirement in only 1.5% of postings", size=8.4, color=INK2, limit=IN2)
txt(756, 666, "required by policy  |  not yet explicit in market", size=8.4, color=INK2, limit=IN2)

arrow((480, 745), (520, 745), color=E_G, lw=2.4)
# (3) 回应 (2) 的风险 —— 右侧回授箭头
arrow((940, 600), (940, 630), color=E_A, lw=1.5, ms=11, ls=(0, (5, 3)))
txt(930, 615, "mitigates", size=8.4, color=E_A, ha="right", limit=(800, 604, 936, 626))

# ---- (3) 教育响应：通栏 ----
R3 = (8, 400, 992, 600)
box(8, 400, 984, 200, C_A, E_A)
txt(500, 583, "Strategy: bounded anticipation", size=11.0, color=E_A, weight="bold", limit=R3)
for i, q in enumerate(["Objectives", "Modules", "Projects", "Assessment"]):
    x = 88 + i * 212
    box(x, 480, 190, 66, "#ffffff", E_A, lw=1.1)
    txt(x + 95, 513, q, size=9.4, weight="bold", limit=(x, 480, x + 190, 546))
txt(46, 455, "translation matrix: policy -> tasks -> curriculum -> assessment", size=8.5,
    color=INK2, ha="left", limit=R3)
txt(46, 430, "JD-R analogy: resource generation and sustained competence", size=8.5,
    color=E_A, ha="left", limit=R3)
arrow((750, 630), (750, 600), color=EDGE, lw=2.0)

# ---- SDG 锚 ----
R4 = (8, 265, 992, 375)
box(8, 265, 984, 110, C_S, E_S)
txt(500, 356, "Sustainable Development Goal anchors", size=10.5, color=E_S, weight="bold", limit=R4)
txt(500, 326, "SDG 4 quality education: skill supply is part of the sustainability of the "
              "education system", size=8.6, color=INK2, limit=R4)
txt(500, 302, "SDG 8 decent work: open access must be matched by capability completeness "
              "and returns", size=8.6, color=INK2, limit=R4)
arrow((500, 400), (500, 375), color=E_S, lw=1.8, ms=12)

# ---- 总体判断 ----
R5 = (8, 100, 992, 240)
box(8, 100, 984, 140, "#f4f4f4", EDGE, lw=1.2)
txt(500, 220, "Overall judgement", size=10.5, weight="bold", limit=R5)
txt(500, 192, "The sustainability of talent supply depends on the completeness of the "
              "capability structure,", size=8.6, color=INK2, limit=R5)
txt(500, 170, "not on how wide the formal access is: the threshold decides who may enter, "
              "the structure decides", size=8.6, color=INK2, limit=R5)
txt(500, 148, "who can endure.", size=8.6, color=INK2, limit=R5)
arrow((500, 265), (500, 240), color=EDGE, lw=1.8, ms=12)

# ---- 出框自检（文字实测宽度） ----
# 1 pt = 1000/7.10/72 = 1.956 数据单位（x/y 等比，故可直接换算）
PT2U = 1000.0 / FIG_W_IN / 72.0
fig.canvas.draw()
inv = ax.transData.inverted()
bad = 0
RECTS = []           # (bbox_data, limit, size, name)
for art, (x0, y0, x1, y1), size, name in CHECKS:
    bb = art.get_window_extent(fig.canvas.get_renderer())
    (px0, py0) = inv.transform((bb.x0, bb.y0))
    (px1, py1) = inv.transform((bb.x1, bb.y1))
    RECTS.append(((px0, py0, px1, py1), (x0, y0, x1, y1), size, name))
    if px0 < x0 - 1 or px1 > x1 + 1 or py0 < y0 - 1 or py1 > y1 + 1:
        bad += 1
        print("  [出框] %-46s 文本占 x[%.0f,%.0f] y[%.0f,%.0f] 限 x[%d,%d] y[%d,%d]"
              % (name, px0, px1, py0, py1, x0, x1, y0, y1))
print("  文字出框自检：%d 项，%s" % (len(CHECKS), "全部在框内" if bad == 0 else "!! %d 项越界" % bad))

# ---- 同框内文字"真叠字"自检 ----
# 判据：两行中心距 < (字高i + 字高j)/2 才判定真叠字。字高按 0.95 em 估：
#   所需中心距 = 0.95 * PT2U * (size_i + size_j) / 2 = 0.9291 * (size_i + size_j) 数据单位
# 这样正常单倍行距（约 1.1 倍字号）不会误报，而"两行仅差 9 单位"必然被抓。
ovl = 0
for i in range(len(RECTS)):
    for j in range(i + 1, len(RECTS)):
        (a0, b0, a1, b1), lim_i, si, ni = RECTS[i]
        (c0, d0, c1, d1), lim_j, sj, nj = RECTS[j]
        if lim_i != lim_j:            # 只比较同一可用区内的文字
            continue
        if min(a1, c1) - max(a0, c0) <= 2:      # 横向不重叠，无需比较
            continue
        cy_i, cy_j = (b0 + b1) / 2.0, (d0 + d1) / 2.0
        need = 0.95 * PT2U * (si + sj) / 2.0
        if abs(cy_i - cy_j) < need:
            ovl += 1
            print("  [叠字] %-32s 与 %-32s  中心距 %.1f < 需 %.1f"
                  % (ni, nj, abs(cy_i - cy_j), need))
print("  同框叠字自检：%d 处" % ovl)

assert bad == 0 and ovl == 0, "fig2 版式自检未通过（越界 %d/叠字 %d）" % (bad, ovl)

save(fig, "fig2_sustainability_framework.png")

# ===================== 其余 6 张原样复制 =====================
for fn in ["fig3_screening_process.png", "fig4_education_experience.png",
           "fig5_family_accessibility.png", "fig6_capability_coverage.png",
           "fig7_cooccurrence_matrix.png", "fig8_salary_by_education.png"]:
    shutil.copyfile(os.path.join(SRC, fn), os.path.join(DST, fn))
    print("  %-42s (复制)" % fn)
print("完成 ->", DST)
