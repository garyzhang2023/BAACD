# -*- coding: utf-8 -*-
"""
第三轮审稿意见（v6.0 → v6.1）的执行与核验
  任务A：安全口径统一为「严格 7 条」——重算岗位族分布与集中性检验
  任务B：经验与企业规模改用分类变量，重跑薪资敏感性模型
  附加：对严格 7 条中最可疑的一条（#378）做单独审计，并给出 6 条备选情形

输出：_round4_out.txt + _round4_metrics.json
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


d = pd.read_csv(BASE + "/论文分析/_清洗后样本_带岗位族.csv", encoding="utf-8-sig",
                dtype=str, keep_default_na=False)
N = len(d)
FAM1 = "① 交付实施族（FDE型）"
p("=" * 100)
p("第四轮核验（v6.0 → v6.1）：安全口径统一 + 分类变量敏感性模型")
p("=" * 100)
p(f"样本 n = {N}")

M = {}

# ================================================================
# 甲. 安全口径统一为严格 7 条
# ================================================================
p("")
p("=" * 100)
p("甲. 安全口径统一：岗位族分布改按「严格 7 条」重算")
p("=" * 100)

txt = (d["职位描述"].fillna("").astype(str) + " " + d["任职要求"].fillna("").astype(str))
T3 = re.compile(r"AI安全|人工智能安全|大模型安全|模型安全|智能体安全|提示注入|越狱|对抗样本|模型对齐|幻觉治理|AI伦理|生成内容安全|内容安全|模型评估安全|红队")
T4 = re.compile(r"伦理|负责任AI|算法公平|算法歧视|可解释|透明性|价值对齐|社会责任治理")
NEG = re.compile(r"(?:无需|不需|不要求|不必|无需具备)[^，。；]{0,12}(?:安全|合规|隐私|伦理|权限)")

hit3 = txt.str.contains(T3, regex=True) & ~txt.str.contains(NEG, regex=True)
hit4 = txt.str.contains(T4, regex=True) & ~txt.str.contains(NEG, regex=True)
cand = hit3 | hit4
idx = list(np.where(cand.values)[0])
p(f"甲0. 自动检索候选 T3∪T4 = {len(idx)} 条（{len(idx)/N*100:.2f}%）")
p(f"     其中仅命中 T3（AI 模型安全层）= {int(hit3.sum())} 条")
p(f"     其中仅命中 T4（伦理治理层，含「可解释」）= {int((hit4 & ~hit3).sum())} 条")

# 仅靠「可解释」才进入口径的
only_exp = []
for i in idx:
    t = txt.iloc[i]
    h3 = bool(re.search(T3, t)); h4 = bool(re.search(T4, t))
    if h4 and not h3:
        others = [w for w in T4.pattern.split("|") if w != "可解释" and w in t]
        if not others:
            only_exp.append(int(d["序号"].iloc[i]))
p(f"甲1. 仅靠「可解释」才进入口径的 = {len(only_exp)} 条：{only_exp}")
strict7 = [int(d["序号"].iloc[i]) for i in idx if int(d["序号"].iloc[i]) not in only_exp]
p(f"甲2. 剔除「可解释」后 = {len(strict7)} 条（严格口径）：{strict7}")

# #378 审计
p("")
p("甲3. 严格 7 条中最可疑一条（#378）的命中审计")
for i in idx:
    if int(str(d["序号"].iloc[i])) == 378:
        t = txt.iloc[i]
        words = [w for w in T3.pattern.split("|") if w in t] + [w for w in T4.pattern.split("|") if w in t]
        p(f"     岗位名称：{d['岗位名称'].iloc[i]}")
        p(f"     岗位族：{d['岗位族'].iloc[i]} | 学历：{d['学历要求'].iloc[i]}")
        p(f"     命中词：{words}")
        for w in words:
            for m in re.finditer(re.escape(w), t):
                a = max(0, m.start() - 60); b = min(len(t), m.end() + 60)
                p(f"       ⟨[{w}] {t[a:b].replace(chr(10),' ')}⟩")
        break

recs = d[d["序号"].isin([str(x) for x in strict7])]
p("")
p("甲4. 严格 7 条的逐条归属")
for _, r in recs.iterrows():
    p(f"     #{r['序号']:<5} {str(r['岗位族'])[:12]:<14} {str(r['岗位名称'])[:34]:<36} {r['学历要求']}")

fams = ["① 交付实施族（FDE型）", "② 解决方案/售前族", "③ 研发算法族",
        "④ 产品运营族", "⑤ AI应用/工具族", "⑥ 其他"]
fam_n = d["岗位族"].value_counts()
tab = np.array([[int((recs["岗位族"] == f).sum()), int(fam_n.get(f, 0)) - int((recs["岗位族"] == f).sum())]
                for f in fams])


def rxc_fisher(tab2, nsim=200000, seed=42):
    """RxC 精确检验（固定边际的置换检验）"""
    rng = np.random.default_rng(seed)
    obs = tab2.astype(float)
    rs, cs = obs.sum(1), obs.sum(0)
    n = obs.sum()
    # 以卡方统计量为检验量
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
        for k, r in enumerate(rs.astype(int)):
            sim[k] = np.bincount(pool[s:s + r], minlength=len(cs))
            s += r
        if chi2(sim) >= obs_stat - 1e-9:
            cnt += 1
    return (cnt + 1) / (nsim + 1)


p("")
p("甲5. 严格 7 条的岗位族分布")
p("     %-22s %6s %8s %10s %9s" % ("岗位族", "命中", "族内n", "族内覆盖率", "占命中比"))
for k, f in enumerate(fams):
    hit, rest = tab[k]
    p("     %-22s %6d %8d %9.2f%% %8.1f%%" % (f[:20], hit, hit + rest, hit / (hit + rest) * 100, hit / 7 * 100))
chi2_v = stats.chi2_contingency(tab)[0:2]
p(f"     2×6 卡方：χ² = {chi2_v[0]:.3f}, df = {stats.chi2_contingency(tab)[2]}, p = {chi2_v[1]:.4g}")
p("     （最小期望频数 %.2f，卡方近似欠稳，仅作参考）"
  % stats.chi2_contingency(tab)[3].min())
_f6 = rxc_fisher(tab, nsim=50000, seed=7)
p(f"     2×6 Fisher 精确检验（固定边际置换检验，50000 次）：p = {_f6:.4g}")

k_in = int((recs["岗位族"] == FAM1).sum()); n_in = int(fam_n[FAM1])
k_out = 7 - k_in; n_out = N - n_in
odds, pf = stats.fisher_exact([[k_in, n_in - k_in], [k_out, n_out - k_out]])
p(f"     交付实施族 {k_in}/{n_in}（{k_in/n_in*100:.2f}%）vs 族外 {k_out}/{n_out}（{k_out/n_out*100:.2f}%）")
p(f"       Fisher 精确检验 p = {pf:.4g}, OR = {odds:.3f}")
p(f"     ⇒ 分布差异{'显著' if pf < .05 else '不显著'}")

M["sec_strict7"] = {"n": 7, "pct": round(7 / N * 100, 2), "records": strict7,
                    "family_tab": {f: int(tab[k][0]) for k, f in enumerate(fams)},
                    "chi2_p": float(chi2_v[1]),
                    "fisher_2x2_p": float(pf), "fisher_2x2_or": float(odds)}

# 备选：剔除 #378 → 6 条
alt6 = [x for x in strict7 if x != 378]
recs6 = d[d["序号"].isin([str(x) for x in alt6])]
p("")
p("甲6. 备选口径：严格 7 条再剔除 #378（判为「用 AI 做安全」而非「AI 自身安全」）= 6 条")
for _, r in recs6.iterrows():
    p(f"     #{r['序号']:<5} {str(r['岗位族'])[:12]:<14} {str(r['岗位名称'])[:34]:<36}")
k6_in = int((recs6["岗位族"] == FAM1).sum())
odds6, pf6 = stats.fisher_exact([[k6_in, n_in - k6_in], [6 - k6_in, n_out - (6 - k6_in)]])
p(f"     交付实施族 {k6_in}/{n_in} vs 族外 {6-k6_in}/{n_out}：Fisher p = {pf6:.4g}, OR = {odds6:.3f}")
M["sec_alt6"] = {"n": 6, "pct": round(6 / N * 100, 2), "records": alt6,
                 "fisher_2x2_p": float(pf6), "fisher_2x2_or": float(odds6)}

# ================================================================
# 乙. 薪资回归：经验与企业规模改分类变量
# ================================================================
p("")
p("=" * 100)
p("乙. 薪资敏感性模型：经验与企业规模改分类变量")
p("=" * 100)


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
p(f"乙0. 城市：{CITIES10}")


def ols_hc1(X, y, names):
    import statsmodels.api as sm
    mod = sm.OLS(y, X).fit(cov_type="HC1")
    return mod


def build(df, exp_col, size_col, with_fam, with_bx=True, exp_ref="② 1-3年", size_ref="③ 100-499人"):
    cols = [np.ones(len(df))]
    names = ["常数"]
    pairs = [("低学历", "专科及以下")]
    if with_bx:
        pairs.append(("学历不限d", "学历不限"))
    for c, nm in pairs:
        cols.append(df[c].values.astype(float)); names.append(nm)
    for lv in EXP_LEVELS:
        if lv == exp_ref or lv not in set(df[exp_col]): continue
        cols.append((df[exp_col] == lv).astype(float).values); names.append("经验：" + lv)
    for lv in SIZE_LEVELS:
        if lv == size_ref or lv not in set(df[size_col]): continue
        cols.append((df[size_col] == lv).astype(float).values); names.append("规模：" + lv)
    for lv in CITIES10:
        if lv == "广州" or lv not in set(df["城市10"]): continue
        cols.append((df["城市10"] == lv).astype(float).values); names.append("城市：" + lv)
    if with_fam:
        for lv in fams:
            if lv == FAM1 or lv not in set(df["岗位族"]): continue
            cols.append((df["岗位族"] == lv).astype(float).values); names.append("岗位族：" + lv[:6])
    return np.column_stack(cols), names


def prep(df, mode):
    g = df.copy()
    g["低学历"] = g["学历组"].isin(["专科及以下"]).astype(int)
    g["学历不限d"] = g["学历组"].eq("学历不限").astype(int)
    g["lnsal"] = np.log(g["薪资K"])
    return g


def run(df, label, exp_col, size_col, with_fam, with_bx=True, n_note=""):
    X, names = build(df, exp_col, size_col, with_fam, with_bx=with_bx)
    mod = ols_hc1(X, df["lnsal"].values, names)
    p("")
    p(f"  【{label}】n = {len(df)}   R² = {mod.rsquared:.4f}   调整R² = {mod.rsquared_adj:.4f}   {n_note}")
    p("     变量                          系数        稳健SE      t        p")
    for k, nm in enumerate(names):
        if k > 0 and not (nm.startswith("专科") or nm.startswith("学历不限")):
            continue
        b = mod.params[k]; se = mod.bse[k]; t = mod.tvalues[k]; pv = mod.pvalues[k]
        star = "***" if pv < .001 else ("**" if pv < .01 else ("*" if pv < .05 else ""))
        p(f"     {nm:<26} {b:>9.4f} {se:>11.4f} {t:>8.2f} {pv:>9.3g} {star}")
    p(f"     （完整模型含 {len(names)} 项；经验 {sum(1 for n in names if n.startswith('经验：'))}项、"
      f"规模 {sum(1 for n in names if n.startswith('规模：'))}项、"
      f"城市 {sum(1 for n in names if n.startswith('城市：'))}项、"
      f"岗位族 {sum(1 for n in names if n.startswith('岗位族：'))}项）")
    return mod, names


# —— 基准：连续变量（原模型口径）——
base_all = d.dropna(subset=["薪资K", "经验年", "规模人", "城市10"]).copy()
base_all = prep(base_all, "cont")
p("")
p("乙1. 基准（连续变量，原模型口径）")
p(f"     全样本·全部10城 n = {len(base_all)}")
Xb = np.column_stack([
    np.ones(len(base_all)), base_all["低学历"].values, base_all["学历不限d"].values,
    base_all["经验年"].values, np.log(base_all["规模人"].values)] +
    [ (base_all["城市10"] == lv).astype(float).values for lv in CITIES10 if lv != "广州" ] +
    [ (base_all["岗位族"] == lv).astype(float).values for lv in fams if lv != FAM1 ])
mb = ols_hc1(Xb, base_all["lnsal"].values, None)
p(f"     专科及以下 β = {mb.params[1]:.4f} (SE {mb.bse[1]:.4f}), p = {mb.pvalues[1]:.3g}")
M["base_all10"] = {"n": int(len(base_all)), "beta": float(mb.params[1]), "se": float(mb.bse[1]),
                   "p": float(mb.pvalues[1]), "r2": float(mb.rsquared), "r2adj": float(mb.rsquared_adj)}

# —— 敏感性1：分类变量，剔除「经验不限」——
s1 = d.copy()
s1["经验档"] = s1["经验要求"].apply(lambda x: exp_cat(x, keep_any=False))
s1["规模档"] = s1["公司规模"].apply(size_cat)
s1 = s1.dropna(subset=["薪资K", "城市10"])
s1 = s1[s1["经验档"].notna() & s1["规模档"].notna()].copy()
s1 = prep(s1, "cat")
p("")
p("乙2. 敏感性（经验/规模改为分类变量；与基准同口径，剔除「经验不限」）")
m1a, n1a = run(s1, "全样本·全部10城·分类", "经验档", "规模档", True)
m1b_df = s1[s1["岗位族"] == FAM1].copy()
m1b, n1b = run(m1b_df, "仅交付实施族内·分类", "经验档", "规模档", False, with_bx=False)
M["cat_all10"] = {"n": int(len(s1)), "beta": float(m1a.params[1]), "se": float(m1a.bse[1]),
                  "p": float(m1a.pvalues[1]), "r2": float(m1a.rsquared), "r2adj": float(m1a.rsquared_adj)}
M["cat_fam1"] = {"n": int(len(m1b_df)), "beta": float(m1b.params[1]), "se": float(m1b.bse[1]),
                 "p": float(m1b.pvalues[1]), "r2": float(m1b.rsquared), "r2adj": float(m1b.rsquared_adj)}

# —— 敏感性2：分类变量，「经验不限」作为独立类别 ——
s2 = d.copy()
s2["经验档"] = s2["经验要求"].apply(lambda x: exp_cat(x, keep_any=True))
s2["规模档"] = s2["公司规模"].apply(size_cat)
s2 = s2.dropna(subset=["薪资K", "城市10"])
s2 = s2[s2["经验档"].notna() & s2["规模档"].notna()].copy()
s2 = prep(s2, "cat")
p("")
p("乙3. 敏感性（「经验不限」保留为独立类别，样本量更大）")
m2a, n2a = run(s2, "全样本·全部10城·分类+经验不限", "经验档", "规模档", True)
m2b_df = s2[s2["岗位族"] == FAM1].copy()
m2b, n2b = run(m2b_df, "仅交付实施族内·分类+经验不限", "经验档", "规模档", False, with_bx=False)
M["cat_all10_any"] = {"n": int(len(s2)), "beta": float(m2a.params[1]), "se": float(m2a.bse[1]),
                      "p": float(m2a.pvalues[1]), "r2": float(m2a.rsquared), "r2adj": float(m2a.rsquared_adj)}
M["cat_fam1_any"] = {"n": int(len(m2b_df)), "beta": float(m2b.params[1]), "se": float(m2b.bse[1]),
                     "p": float(m2b.pvalues[1]), "r2": float(m2b.rsquared), "r2adj": float(m2b.rsquared_adj)}

# —— 中位数回归 ——
try:
    import statsmodels.api as sm
    qr = sm.QuantReg(base_all["lnsal"].values, Xb).fit(q=0.5)
    p("")
    p(f"乙4. 中位数回归（连续变量口径）：专科及以下 β = {qr.params[1]:.4f}, p = {qr.pvalues[1]:.3g}")
    M["qreg"] = {"beta": float(qr.params[1]), "p": float(qr.pvalues[1])}
except Exception as e:
    p(f"乙4. 中位数回归失败：{e}")

# —— 纳入/排除样本比较（保留口径 = 全部10城）——
p("")
p("乙5. 回归样本的纳入与排除比较（全部10城口径）")
inc_flag = d.index.isin(base_all.index)
p(f"     纳入 n = {int(inc_flag.sum())}（{inc_flag.mean()*100:.1f}%）；排除 n = {int((~inc_flag).sum())}")
for var in ["岗位族", "学历组", "城市"]:
    tab2 = pd.crosstab(d[var], inc_flag)
    if tab2.shape[1] < 2:
        p(f"     {var}: 只有单一取值，跳过"); continue
    chi2x, pvx, dofx, expx = stats.chi2_contingency(tab2.values)
    k = min(tab2.shape) - 1
    v = np.sqrt(chi2x / (tab2.values.sum() * k)) if k > 0 else np.nan
    p(f"     {var:<6} χ² = {chi2x:>7.2f}, df = {dofx:>2}, p = {pvx:<9.3g}, Cramér's V = {v:.3f}"
      f"  {'← 存在系统差异' if pvx < .05 else '无显著差异'}")
    if pvx < .05:
        prop = (pd.crosstab(d[var], inc_flag, normalize="columns") * 100).round(1)
        p("       纳入/排除构成（%）：")
        for lv in prop.index:
            p(f"         {str(lv)[:22]:<24} 纳入 {prop.loc[lv, True]:>5.1f}   排除 {prop.loc[lv, False]:>5.1f}")
M["inclusion_test"] = {}
for var in ["岗位族", "学历组", "城市"]:
    tab2 = pd.crosstab(d[var], inc_flag)
    if tab2.shape[1] < 2: continue
    chi2x, pvx, dofx, _ = stats.chi2_contingency(tab2.values)
    M["inclusion_test"][var] = {"chi2": float(chi2x), "df": int(dofx), "p": float(pvx)}

# —— 中位数回归（保留口径）——
p("")
p("乙6. 中位数回归（保留口径）")
try:
    import statsmodels.api as sm
    q1 = sm.QuantReg(base_all["lnsal"].values, Xb).fit(q=0.5)
    p(f"     全样本·全部10城（连续变量）  β = {q1.params[1]:.4f}, p = {q1.pvalues[1]:.3g}, n = {len(base_all)}")
    fc = sorted(m1b_df["城市10"].unique())
    Xf = np.column_stack([
        np.ones(len(m1b_df)), m1b_df["低学历"].values,
        m1b_df["经验年"].values, np.log(m1b_df["规模人"].values)] +
        [(m1b_df["城市10"] == lv).astype(float).values for lv in fc[1:]])
    q2 = sm.QuantReg(m1b_df["lnsal"].values, Xf).fit(q=0.5)
    p(f"     仅交付实施族内（连续变量）    β = {q2.params[1]:.4f}, p = {q2.pvalues[1]:.3g}, n = {len(m1b_df)}")
    M["qreg_all10"] = {"beta": float(q1.params[1]), "p": float(q1.pvalues[1]), "n": int(len(base_all))}
    M["qreg_fam1"] = {"beta": float(q2.params[1]), "p": float(q2.pvalues[1]), "n": int(len(m1b_df))}
except Exception as e:
    p(f"     中位数回归失败：{e}")

p("")
p("=" * 100)
p("结论：两种敏感性设定（分类变量 / 分类变量＋经验不限独立类别）下「专科及以下」系数方向与显著性")

io.open(BASE + "/投稿-MDPI/_round4_out.txt", "w", encoding="utf-8").write(OUT.getvalue())
io.open(BASE + "/投稿-MDPI/_round4_metrics.json", "w", encoding="utf-8").write(
    json.dumps(M, ensure_ascii=False, indent=2))
print(OUT.getvalue())
