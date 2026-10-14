# -*- coding: utf-8 -*-
"""build_figs_final.py —— 落成"投稿即用"图集 figs_docx/（文件名 = 最终图号）

改名原因：§3.4 插入新图后编号发生变化——
  figs_en_v2/figX_security_measurement_candidate.png  ->  fig8_security_measurement.png（新 Figure 8）
  figs_en_v2/fig8_salary_by_education.png             ->  fig9_salary_by_education.png （原 Figure 8 变 Figure 9）
figs_en_v2/ 保持 v1→v2 对照时的原名不动（图件对照-v1到v2.html 仍可正常显示）。

来源：
  fig1/fig2  已按 Word 版面重绘（上一轮 make_figs_docx.py 产出，本脚本不改动）
  fig3       v1（筛选流程图，本轮未重绘）
  fig4–fig7  figs_en_v2（v2 重绘版，文件名与图号一致）
  fig8       figs_en_v2/figX_...（新增，renamed）
  fig9       figs_en_v2/fig8_salary_by_education（v2 重绘版，renamed）

断言：9 张齐备、尺寸与源一致（MD5）、宽高比未被改动；旧文件名 fig8_salary_by_education.png
若残留则移入 _dotwork/stale/（不删除，保留可追溯）。
"""
import hashlib
import io
import os
import shutil

from PIL import Image

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

HERE = FIGROOT     # 图件工作目录（作者工作区即 投稿-MDPI/）；下游 HERE 引用随之指向该目录
V1 = os.path.join(HERE, "figs_en")
V2 = os.path.join(HERE, "figs_en_v2")
OUT = os.path.join(HERE, "figs_docx")
STALE = os.path.join(HERE, "_dotwork", "stale")
MAXFIG = 7.10          # 版心通栏宽度（in），make_docx.py 的 MAX_FIG_IN

PLAN = [
    ("fig4_education_experience.png", V2, "fig4_education_experience.png"),
    ("fig5_family_accessibility.png", V2, "fig5_family_accessibility.png"),
    ("fig6_capability_coverage.png", V2, "fig6_capability_coverage.png"),
    ("fig7_cooccurrence_matrix.png", V2, "fig7_cooccurrence_matrix.png"),
    ("fig8_security_measurement.png", V2, "figX_security_measurement_candidate.png"),
    ("fig9_salary_by_education.png", V2, "fig8_salary_by_education.png"),
    ("fig3_screening_process.png", V1, "fig3_screening_process.png"),
]
KEEP = ["fig1_policy_job_education_framework.png", "fig2_sustainability_framework.png"]

os.makedirs(OUT, exist_ok=True)
os.makedirs(STALE, exist_ok=True)

# ---- fig1/fig2 必须在位（本轮不改它们）
for k in KEEP:
    p = os.path.join(OUT, k)
    assert os.path.isfile(p), "缺 %s（上一轮重绘版，不得丢失）" % k

# ---- 旧命名文件移出（保留，不删）
old = os.path.join(OUT, "fig8_salary_by_education.png")
if os.path.isfile(old):
    shutil.move(old, os.path.join(STALE, "fig8_salary_by_education.png"))
    print("  旧命名文件已移入 _dotwork/stale/：fig8_salary_by_education.png")

# ---- 复制并逐张校验
rows = []
for dst, srcdir, srcname in PLAN:
    s = os.path.join(srcdir, srcname)
    d = os.path.join(OUT, dst)
    assert os.path.isfile(s), "源图缺失：%s" % s
    shutil.copyfile(s, d)
    hs = hashlib.md5(open(s, "rb").read()).hexdigest()
    hd = hashlib.md5(open(d, "rb").read()).hexdigest()
    assert hs == hd, "%s 复制后 MD5 不一致" % dst
    im = Image.open(d)
    dpi = im.info.get("dpi", (600,))[0]
    assert dpi >= 599, "%s dpi=%s 未达 600" % (dst, dpi)
    rows.append((dst, im.size[0], im.size[1], dpi, im.size[1] / float(im.size[0]),
                 im.size[0] / dpi, os.path.relpath(s, HERE)))
    print("  %-42s %5dx%-5d %d dpi  设计宽 %.2f in  显示 %.2f x %.2f in  <- %s"
          % (dst, im.size[0], im.size[1], dpi, im.size[0] / dpi,
             min(MAXFIG, im.size[0] / dpi),
             min(MAXFIG, im.size[0] / dpi) * im.size[1] / float(im.size[0]),
             os.path.relpath(s, HERE)))

# ---- 齐备性断言
have = sorted(f for f in os.listdir(OUT) if f.lower().endswith(".png"))
want = sorted(KEEP + [p[0] for p in PLAN])
assert have == want, "figs_docx 内容不符\n  期望 %s\n  实得 %s" % (want, have)
assert len(have) == 9, "图集应为 9 张，实得 %d" % len(have)

# ---- 落一份对照表，供交付说明与 docx 生成核对
tab = os.path.join(HERE, "_dotwork", "_figs_final_map.md")
with io.open(tab, "w", encoding="utf-8", newline="\n") as f:
    f.write("# figs_docx 图集对照表（文件名 = 最终图号）\n\n")
    f.write("| 投稿图号 | 文件 | 源文件 | 像素 | 设计宽 |\n|---|---|---|---|---|\n")
    f.write("| Figure 1 | fig1_policy_job_education_framework.png | 上一轮按版面重绘 | - | - |\n")
    f.write("| Figure 2 | fig2_sustainability_framework.png | 上一轮按版面重绘 | - | - |\n")
    for dst, w, h, dpi, ratio, win, src in rows:
        n = int(dst[3]) if dst[3].isdigit() else 0
        f.write("| Figure %s | %s | %s | %dx%d | %.2f in |\n" % (n, dst, src, w, h, win))
print()
print("图集齐备：%d 张（fig1–fig9）｜对照表：%s" % (len(have), os.path.relpath(tab, HERE)))
