# -*- coding: utf-8 -*-
"""
第四轮审稿意见（v6.2 → v6.3）的执行与核验
  任务甲：AI 安全严格口径由 7 条改为 6 条（剔除 #378「用 AI 做安全」边界项）
          并给 12 条候选一个穷尽、互斥的四类判读结构
  任务乙：交付实施族内薪资模型改为真正的「专科及以下 vs 本科」比较
          （限制学历组后估计），原「全学历组」设定降为稳健性口径
输出：_round5_out.txt + _round5_metrics.json
"""
import io, os, re, json
import numpy as np
import pandas as pd
from scipy import stats

# ---- 项目根定位（补充材料包内不依赖作者本机绝对路径）----
# 优先读环境变量 PROJECT_ROOT；否则自本文件逐级上溯，寻找含「论文分析」子目录的目录
# （即作者的工作区根）。脱离工作区单独解包时回落到本文件所在目录，脚本仍可逐行审计；
# 唯 s2_clean.py 依赖未随包发布的原始平台导出，重跑须先恢复工作区
# （见 S2_README_analysis_chain.md 第 3 节）。
def _project_root():
    env = os.environ.get("PROJECT_ROOT")
    if env:
        return os.path.abspath(env)
    here = os.path.dirname(os.path.abspath(__file__))
    cur = here
    while True:
        if os.path.isdir(os.path.join(cur, "论文分析")):
            return cur
        up = os.path.dirname(cur)
        if up == cur:
            return here
        cur = up


BASE = _project_root()
OUT = io.StringIO()


def p(s=""):
    OUT.write(str(s) + "\n")


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0)
    ph = k / n
    dd = 1 + z * z / n
    c = ph + z * z / (2 * n)
    hw = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return ((c - hw) / dd * 100, (c + hw) / dd * 100)


d = pd.read_csv(BASE + "/论文分析/_清洗后样本_带岗位族.csv", encoding="utf-8-sig",
                dtype=str, keep_default_na=False)
N = len(d)
FAM1 = "① 交付实施族（FDE型）"
M = {}

p("=" * 104)
p("第五轮核验（v6.2 → v6.3）：安全严格口径 → 6 条；交付族内模型参照组校正")
p("=" * 104)
p(f"样本 n = {N}")

# ================================================================
# 甲. 安全口径
# ================================================================
p("")
p("=" * 104)
p("甲. AI 特异性安全：严格口径由 7 条改为 6 条，并给出 12 条候选的穷尽四类判读")
p("=" * 104)

txt = (d["职位描述"].fillna("").astype(str) + " " + d["任职要求"].fillna("").astype(str))
T3 = re.compile(r"AI安全|人工智能安全|大模型安全|模型安全|智能体安全|提示注入|越狱|对抗样本|"
                r"模型对齐|幻觉治理|AI伦理|生成内容安全|内容安全|模型评估安全|红队")
T4 = re.compile(r"伦理|负责任AI|算法公平|算法歧视|可解释|透明性|价值对齐|社会责任治理")
NEG = re.compile(r"(?:无需|不需|不要求|不必|无需具备)[^，。；]{0,12}(?:安全|合规|隐私|伦理|权限)")
hit3 = txt.str.contains(T3, regex=True) & ~txt.str.contains(NEG, regex=True)
hit4 = txt.str.contains(T4, regex=True) & ~txt.str.contains(NEG, regex=True)
cand = hit3 | hit4
idx = list(np.where(cand.values)[0])
ids = [int(d["序号"].iloc[i]) for i in idx]
p(f"甲0. 自动检索候选 T3∪T4 = {len(ids)} 条（{len(ids)/N*100:.2f}%）：{sorted(ids)}")

# —— 人工判读：把 12 条按「AI 特异性来源」归为四类（互斥、穷尽）——
CLS = {
    # 核心：正文明确指向人工智能自身的安全治理
    "核心": [6, 91, 107, 113, 239, 544],
    # 边界一：以人工智能服务于安全业务（用 AI 做安全），非治理 AI 自身安全
    "用AI做安全": [378],
    # 边界二：指向 AI 可靠性/监督机制的治理要求（幻觉与越权识别、可追踪可回滚与人工接管），
    #         但未使用 AI 安全治理的专业表述
    "AI可靠性监督边界": [460, 521],
    # 边界三：命中的「可解释」在语境中指代码与系统的可维护性、或与准确率/延迟并列的设计属性
    "可解释=工程属性": [95, 246, 455],
}
flat = [x for v in CLS.values() for x in v]
assert sorted(flat) == sorted(ids), "四类判读必须穷尽且不重叠"
p("甲1. 12 条候选的人工判读分类（互斥、穷尽）")
for k, v in CLS.items():
    p(f"     {k:<22} {len(v):>2} 条  {v}")
p(f"     合计 = {len(flat)} 条  ✔ 与自动候选一致")

CORE = CLS["核心"]
TIER7 = CORE + CLS["用AI做安全"]
TIER9 = TIER7 + CLS["AI可靠性监督边界"]
TIER12 = TIER9 + CLS["可解释=工程属性"]
assert sorted(TIER12) == sorted(ids)

p("")
p("甲2. 嵌套口径（每层为上一层子集）")
for nm, lst in [("严格口径（主结果）", CORE), ("＋「用AI做安全」边界项", TIER7),
                ("＋AI可靠性/监督边界项", TIER9), ("全部自动候选", TIER12)]:
    k = len(lst)
    lo, hi = wilson(k, N)
    p(f"     {nm:<26} {k:>2} 条  {k/N*100:5.2f}%  95% CI [{lo:.2f}%, {hi:.2f}%]")
M["tiers"] = {nm: {"n": len(lst), "pct": round(len(lst) / N * 100, 2),
                   "ci": [round(wilson(len(lst), N)[0], 2), round(wilson(len(lst), N)[1], 2)],
                   "records": lst}
              for nm, lst in [("strict6", CORE), ("tier7", TIER7), ("tier9", TIER9), ("tier12", TIER12)]}

# —— 逐条明细 ——
p("")
p("甲3. 严格 6 条逐条明细")
recs6 = d[d["序号"].isin([str(x) for x in CORE])]
for _, r in recs6.iterrows():
    p(f"     #{r['序号']:<5} {str(r['岗位族'])[:12]:<14} {str(r['岗位名称'])[:36]:<38} {r['学历要求']}")
# 安全专职岗判定
SEC_TITLE = [107, 239]          # 岗位名称明确含安全研发/安全算法语义
p(f"     岗位名称明确含安全研发或安全算法语义者：{len(SEC_TITLE)} 条（{len(SEC_TITLE)/len(CORE)*100:.1f}%）"
  f"，#{SEC_TITLE[0]}、#{SEC_TITLE[1]}")
M["sec_title_ratio"] = round(len(SEC_TITLE) / len(CORE) * 100, 1)

# —— 岗位族分布与检验 ——
fams = ["① 交付实施族（FDE型）", "② 解决方案/售前族", "③ 研发算法族",
        "④ 产品运营族", "⑤ AI应用/工具族", "⑥ 其他"]
fam_n = d["岗位族"].value_counts()


def rxc_fisher(tab2, nsim=50000, seed=7):
    rng = np.random.default_rng(seed)
    obs = tab2.astype(float)
    rs, cs = obs.sum(1), obs.sum(0)

    def chi2(t):
        e = np.outer(t.sum(1), t.sum(0)) / t.sum()
        return float(((t - e) ** 2 / np.where(e == 0, 1, e)).sum())
    obs_stat = chi2(obs)
    pool = np.repeat(np.arange(len(cs)), cs.astype(int))
    cnt = 0
    for _ in range(nsim):
        rng.shuffle(pool)
        sim = np.zeros_like(obs)
        s = 0
        for kk, r in enumerate(rs.astype(int)):
            sim[kk] = np.bincount(pool[s:s + r], minlength=len(cs))
            s += r
        if chi2(sim) >= obs_stat - 1e-9:
            cnt += 1
    return (cnt + 1) / (nsim + 1)


for nm, lst in [("严格 6 条（主结果）", CORE), ("含边界 7 条", TIER7)]:
    p("")
    p(f"甲4. 岗位族分布 —— {nm}")
    rec = d[d["序号"].isin([str(x) for x in lst])]
    tab = np.array([[int((rec["岗位族"] == f).sum()), int(fam_n.get(f, 0)) - int((rec["岗位族"] == f).sum())]
                    for f in fams])
    p("     %-22s %6s %8s %10s %9s" % ("岗位族", "命中", "族内n", "族内覆盖率", "占命中比"))
    for kk, f in enumerate(fams):
        h, rest = tab[kk]
        p("     %-22s %6d %8d %9.2f%% %8.1f%%" % (f[:20], h, h + rest, h / (h + rest) * 100, h / len(lst) * 100))
    chi2x, pvx, dofx, expx = stats.chi2_contingency(tab)
    f6 = rxc_fisher(tab)
    k_in = int((rec["岗位族"] == FAM1).sum()); n_in = int(fam_n[FAM1])
    k_out = len(lst) - k_in; n_out = N - n_in
    odds, pf = stats.fisher_exact([[k_in, n_in - k_in], [k_out, n_out - k_out]])
    p(f"     2×6 卡方 χ² = {chi2x:.3f}, df = {dofx}, p = {pvx:.4g}（最小期望 {expx.min():.2f}，近似欠稳）")
    p(f"     2×6 Fisher（固定边际置换，50000 次）p = {f6:.4g}")
    p(f"     交付实施族 {k_in}/{n_in}（{k_in/n_in*100:.2f}%）vs 族外 {k_out}/{n_out}（{k_out/n_out*100:.2f}%）")
    p(f"       Fisher 2×2 p = {pf:.4g}, OR = {odds:.3f}")
    M[nm] = {"records": lst, "family_tab": {f: int(tab[kk][0]) for kk, f in enumerate(fams)},
             "pct": round(len(lst) / N * 100, 2),
             "chi2_p": float(pvx), "fisher_2x6_p": float(f6),
             "delivery_k": k_in, "delivery_n": n_in,
             "outside_k": k_out, "outside_n": n_out,
             "fisher_2x2_p": float(pf), "fisher_2x2_or": float(odds)}

# ================================================================
# 乙. 交付实施族内薪资模型：参照组校正
# ================================================================
p("")
p("=" * 104)
p("乙. 交付实施族内薪资模型：使「专科及以下」真正相对「本科」估计")
p("=" * 104)


def parse_salary(s):
    s = str(s).replace("·", "x").replace("薪", "x")
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*K", s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    m = re.search(r"(\d+(?:\.\d+)?)\s*K", s)
    return float(m.group(1)) if m else np.nan


def edu_group(x):
    x = str(x).strip()
    if x in ("大专", "中专/中技", "高中", "初中及以下"): return "专科及以下"
    if x == "学历不限": return "学历不限"
    if x == "本科": return "本科"
    return "硕士及以上"


def exp_mid(x):
    x = str(x).strip()
    if x in ("", "经验不限"): return np.nan
    if x == "在校/应届": return 0.5
    if x == "1年以内": return 1.0
    m = re.match(r"^(\d+)-(\d+)年$", x)
    if m: return (int(m.group(1)) + int(m.group(2))) / 2
    m = re.match(r"^(\d+)年以上$", x)
    if m: return float(m.group(1)) + 2.5
    return np.nan


def size_mid(x):
    x = str(x).strip()
    if x in ("", "未标明"): return np.nan
    m = re.match(r"^(\d+)-(\d+)人$", x)
    if m: return (int(m.group(1)) + int(m.group(2))) / 2
    m = re.match(r"^(\d+)人以上$", x)
    if m: return float(m.group(1)) * 2
    if x == "0-20人": return 10.0
    return np.nan


EXP_LEVELS = ["① 1年以内", "② 1-3年", "③ 3-5年", "④ 5年以上", "⑤ 经验不限"]
SIZE_LEVELS = ["① 0-20人", "② 20-99人", "③ 100-499人", "④ 500人以上"]


def exp_cat(x, keep_any=True):
    x = str(x).strip()
    if x in ("", "未标明"): return None
    if x == "经验不限": return "⑤ 经验不限" if keep_any else None
    if x in ("在校/应届", "1年以内"): return "① 1年以内"
    if x == "1-3年": return "② 1-3年"
    if x == "3-5年": return "③ 3-5年"
    if x in ("5-10年", "10年以上"): return "④ 5年以上"
    return None


def size_cat(x):
    x = str(x).strip()
    if x in ("", "未标明"): return None
    if x == "0-20人": return "① 0-20人"
    if x == "20-99人": return "② 20-99人"
    if x == "100-499人": return "③ 100-499人"
    if x in ("500-999人", "1000-9999人", "10000人以上"): return "④ 500人以上"
    return None


d["薪资K"] = d["薪资"].apply(parse_salary)
d["学历组"] = d["学历要求"].apply(edu_group)
d["经验年"] = d["经验要求"].apply(exp_mid)
d["规模人"] = d["公司规模"].apply(size_mid)
d["城市"] = d["来源城市"].astype(str).str.strip()
CITIES10 = list(d["城市"].value_counts().head(10).index)
d["城市10"] = d["城市"].where(d["城市"].isin(CITIES10), other=None)
p(f"乙0. 城市参照类统一设为「广州」；城市共 10 个：{CITIES10}")


def ols_hc1(X, y):
    import statsmodels.api as sm
    return sm.OLS(y, X).fit(cov_type="HC1")


def build(df, exp_col, size_col, with_fam, with_bx=True, exp_ref="② 1-3年", size_ref="③ 100-499人"):
    cols = [np.ones(len(df))]; names = ["常数"]
    pairs = [("低学历", "专科及以下")]
    if with_bx:
        pairs.append(("学历不限d", "学历不限"))
    for c, nm in pairs:
        cols.append(df[c].values.astype(float)); names.append(nm)
    # 连续变量口径（经验年 / ln 企业规模）
    if exp_col == "经验年":
        cols.append(df["经验年"].values.astype(float)); names.append("工作经验(年)")
    if size_col == "规模人":
        cols.append(np.log(df["规模人"].values.astype(float))); names.append("ln(企业规模)")
    for lv in EXP_LEVELS:
        if lv == exp_ref or lv not in set(df[exp_col]): continue
        cols.append((df[exp_col] == lv).astype(float).values); names.append("经验：" + lv)
    for lv in SIZE_LEVELS:
        if lv == size_ref or lv not in set(df[size_col]): continue
        cols.append((df[size_col] == lv).astype(float).values); names.append("规模：" + lv)
    for lv in CITIES10:                       # 参照类 = 广州
        if lv == "广州" or lv not in set(df["城市10"]): continue
        cols.append((df["城市10"] == lv).astype(float).values); names.append("城市：" + lv)
    if with_fam:
        for lv in fams:
            if lv == FAM1 or lv not in set(df["岗位族"]): continue
            cols.append((df["岗位族"] == lv).astype(float).values); names.append("岗位族：" + lv[:6])
    return np.column_stack(cols), names


def prep(df):
    g = df.copy()
    g["低学历"] = g["学历组"].isin(["专科及以下"]).astype(int)
    g["学历不限d"] = g["学历组"].eq("学历不限").astype(int)
    g["lnsal"] = np.log(g["薪资K"])
    return g


def run(df, label, exp_col, size_col, with_fam, with_bx=True, show_city=True):
    X, names = build(df, exp_col, size_col, with_fam, with_bx=with_bx)
    mod = ols_hc1(X, df["lnsal"].values)
    p("")
    p(f"  【{label}】 n = {len(df)}   R² = {mod.rsquared:.4f}   调整R² = {mod.rsquared_adj:.4f}")
    b, se, t, pv = mod.params[1], mod.bse[1], mod.tvalues[1], mod.pvalues[1]
    star = "***" if pv < .001 else ("**" if pv < .01 else ("*" if pv < .05 else ""))
    p(f"     专科及以下  β = {b:>8.4f}  稳健SE {se:.4f}  t = {t:>6.2f}  p = {pv:>9.3g} {star}")
    if with_bx:
        p(f"     学历不限    β = {mod.params[2]:>8.4f}  稳健SE {mod.bse[2]:.4f}  p = {mod.pvalues[2]:>9.3g}")
    p(f"     （模型共 {len(names)} 项；经验 {sum(1 for n in names if n.startswith('经验：'))}、"
      f"规模 {sum(1 for n in names if n.startswith('规模：'))}、"
      f"城市 {sum(1 for n in names if n.startswith('城市：'))}、"
      f"岗位族 {sum(1 for n in names if n.startswith('岗位族：'))}）")
    return mod, names, b, se, pv


f1 = prep(d[d["岗位族"] == FAM1].dropna(subset=["薪资K", "经验年", "规模人", "城市10"]).copy())
p("")
p(f"乙1. 交付实施族内回归样本 n = {len(f1)}；其学历组构成：{dict(f1['学历组'].value_counts())}")

f1r = f1[f1["学历组"].isin(["专科及以下", "本科"])].copy()
p(f"乙2. 限制为「专科及以下 / 本科」两类的回归样本 n = {len(f1r)}；"
  f"构成：{dict(f1r['学历组'].value_counts())}")

# —— 连续变量口径 ——
p("")
p("乙3. 连续变量口径（经验年、ln 规模）")
mA, _, bA, seA, pvA = run(f1, "原口径：族内全学历组（参照＝本科＋硕士及以上＋学历不限）",
                          "经验年", "规模人", False, with_bx=False)
mB, _, bB, seB, pvB = run(f1r, "修正口径：族内仅「专科及以下 vs 本科」（参照＝本科）",
                          "经验年", "规模人", False, with_bx=False)
M["fam_full_cont"] = {"n": int(len(f1)), "beta": float(bA), "se": float(seA), "p": float(pvA)}
M["fam_restr_cont"] = {"n": int(len(f1r)), "beta": float(bB), "se": float(seB), "p": float(pvB)}

# —— 分类变量口径 ——
p("")
p("乙4. 分类变量口径（与表11一致）")
s1 = d.copy()
s1["经验档"] = s1["经验要求"].apply(lambda x: exp_cat(x, keep_any=False))
s1["规模档"] = s1["公司规模"].apply(size_cat)
s1 = s1.dropna(subset=["薪资K", "城市10"])
s1 = s1[s1["经验档"].notna() & s1["规模档"].notna()].copy()
s1 = prep(s1)
a1 = s1[s1["岗位族"] == FAM1].copy()
a1r = a1[a1["学历组"].isin(["专科及以下", "本科"])].copy()
mA2, _, bA2, seA2, pvA2 = run(a1, "模型2a 原口径：族内全学历组·分类",
                             "经验档", "规模档", False, with_bx=False)
mB2, _, bB2, seB2, pvB2 = run(a1r, "模型2a′ 修正口径：族内仅专科及以下 vs 本科·分类",
                              "经验档", "规模档", False, with_bx=False)

s2 = d.copy()
s2["经验档"] = s2["经验要求"].apply(lambda x: exp_cat(x, keep_any=True))
s2["规模档"] = s2["公司规模"].apply(size_cat)
s2 = s2.dropna(subset=["薪资K", "城市10"])
s2 = s2[s2["经验档"].notna() & s2["规模档"].notna()].copy()
s2 = prep(s2)
a2 = s2[s2["岗位族"] == FAM1].copy()
a2r = a2[a2["学历组"].isin(["专科及以下", "本科"])].copy()
mA3, _, bA3, seA3, pvA3 = run(a2, "模型2b 原口径：族内全学历组·分类＋经验不限",
                              "经验档", "规模档", False, with_bx=False)
mB3, _, bB3, seB3, pvB3 = run(a2r, "模型2b′ 修正口径：族内仅专科及以下 vs 本科·分类＋经验不限",
                              "经验档", "规模档", False, with_bx=False)

M["fam_full_cat"] = {"n": int(len(a1)), "beta": float(bA2), "se": float(seA2), "p": float(pvA2)}
M["fam_restr_cat"] = {"n": int(len(a1r)), "beta": float(bB2), "se": float(seB2), "p": float(pvB2)}
M["fam_full_cat_any"] = {"n": int(len(a2)), "beta": float(bA3), "se": float(seA3), "p": float(pvA3)}
M["fam_restr_cat_any"] = {"n": int(len(a2r)), "beta": float(bB3), "se": float(seB3), "p": float(pvB3)}

# —— 全样本模型（表10 模型1 / 表11 模型1a、1b）复核 ——
p("")
p("乙5. 全样本模型复核（表10 模型1 与 表11 模型1a、1b；学历参照＝本科＋硕士及以上，城市参照＝广州）")
base_all = d.dropna(subset=["薪资K", "经验年", "规模人", "城市10"]).copy()
base_all = prep(base_all)
m1, _, b1, se1, pv1 = run(base_all, "模型1 全样本·全部10城·连续变量", "经验年", "规模人", True, with_bx=True)
c1 = s1.copy(); c1 = prep(c1)
m1a, _, b1a, se1a, pv1a = run(c1, "模型1a 全样本·全部10城·分类", "经验档", "规模档", True, with_bx=True)
c2 = s2.copy(); c2 = prep(c2)
m1b, _, b1b, se1b, pv1b = run(c2, "模型1b 全样本·全部10城·分类＋经验不限", "经验档", "规模档", True, with_bx=True)
M["all10_cont"] = {"n": int(len(base_all)), "beta": float(b1), "se": float(se1), "p": float(pv1)}
M["all10_cat"] = {"n": int(len(c1)), "beta": float(b1a), "se": float(se1a), "p": float(pv1a)}
M["all10_cat_any"] = {"n": int(len(c2)), "beta": float(b1b), "se": float(se1b), "p": float(pv1b)}

p("")
p("=" * 104)
p("小结")
p("=" * 104)
p("甲：严格 AI 特异性安全口径 = %d 条（%.2f%%），剔除 #378「用 AI 做安全」边界项；"
  % (len(CORE), len(CORE) / N * 100))
p("    含边界口径 7 条（%.2f%%）；自动候选 12 条（%.2f%%）。" % (len(TIER7) / N * 100, len(TIER12) / N * 100))
p("乙：交付族内模型改为「专科及以下 vs 本科」后 n = %d，β = %.4f（p = %.3g）；"
  % (len(f1r), bB, pvB))
p("    原全学历组口径 n = %d，β = %.4f（p = %.3g）。" % (len(f1), bA, pvA))

io.open(BASE + "/投稿-MDPI/_round5_out.txt", "w", encoding="utf-8").write(OUT.getvalue())
io.open(BASE + "/投稿-MDPI/_round5_metrics.json", "w", encoding="utf-8").write(
    json.dumps(M, ensure_ascii=False, indent=2))
print(OUT.getvalue())
