# -*- coding: utf-8 -*-
"""第6步：按专家意见重构统计口径。
变更点：
  1) 去掉"独立两比例z检验"，四项能力总体差异改用 Cochran's Q（配对二分数据）
  2) 两两能力比较改用 McNemar 检验 + Holm 校正
  3) 薪资组间比较改用 Kruskal-Wallis / Mann-Whitney U
  4) 补算：交付实施族内部学历—薪资（n/中位数/P25/P75）
  5) 补算：学历与经验结构、四维能力共现矩阵
  6) 补做：详情链接去重与近似重复的记录性核查（如实报告，不预设已完成）
"""
import os, re, json
from collections import Counter
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
OUT = os.path.join(BASE, "论文分析")
R = []
def p(s=""):
    R.append(str(s)); print(s)

raw = pd.read_csv(os.path.join(BASE, "BOSS招聘数据-广东.csv"), encoding="utf-8-sig",
                  dtype=str, keep_default_na=False)
keep = pd.read_csv(os.path.join(OUT, "_清洗后样本_带岗位族.csv"), encoding="utf-8-sig",
                   dtype=str, keep_default_na=False)

# ---------------- 0. 去重核查（如实记录） ----------------
p("=" * 84)
p("【0】重复记录核查（如实报告，不预设已完成）")
p("=" * 84)
for name, d in [("原始665条", raw), ("有效547条", keep)]:
    if "详情链接" in d.columns:
        n_dup = int(d["详情链接"].duplicated().sum())
        p(f"  {name}：详情链接完全重复 {n_dup} 条；去重后 {len(d) - n_dup} 条")
    else:
        p(f"  {name}：无『详情链接』字段，无法做链接去重")
# 近似重复：同公司 + 同岗位名称 + 同城市
key = keep["公司"].astype(str).str.strip() + "|" + keep["岗位名称"].astype(str).str.strip() + "|" + keep["来源城市"].astype(str).str.strip()
p(f"  有效样本中(公司+岗位名+城市)三元组重复 {int(key.duplicated().sum())} 条 —— 需人工复核是否同一岗位多次发布")
# 去掉公司名泛化后缀后复核
comp = keep["公司"].astype(str).str.replace(r"(有限公司|股份有限公司|科技|网络|信息|技术|集团)", "", regex=True).str.strip()
key2 = comp + "|" + keep["岗位名称"].astype(str).str.strip()
p(f"  泛化公司名后(公司核心+岗位名)重复 {int(key2.duplicated().sum())} 条")
title_dup = keep["岗位名称"].astype(str).str.strip().value_counts()
p(f"  岗位名称重复度 Top5：{dict(title_dup.head(5))}")

# ---------------- 薪资解析 ----------------
def parse_salary(s):
    s = str(s).replace("·", "x").replace("薪", "x")
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*K", s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2
    m = re.search(r"(\d+(?:\.\d+)?)\s*K", s)
    return float(m.group(1)) if m else np.nan

d = keep.copy()
d["薪资K"] = d["薪资"].apply(parse_salary)
n_sal = int(d["薪资K"].notna().sum())

def edu_group(x):
    x = str(x).strip()
    if x in ("大专", "中专/中技", "高中", "初中及以下"):
        return "专科及以下"
    if x == "学历不限":
        return "学历不限"
    if x == "本科":
        return "本科"
    return "硕士及以上"

d["学历组"] = d["学历要求"].apply(edu_group)
# 可及口径：直接可及=专科及以下；潜在可及=专科及以下+学历不限
d["直接可及"] = d["学历组"].eq("专科及以下").astype(int)
d["潜在可及"] = d["学历组"].isin(["专科及以下", "学历不限"]).astype(int)

def wilson(k, n, z=1.959964):
    if n == 0: return (np.nan, np.nan)
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0, c - h) * 100, min(1, c + h) * 100)

# ---------------- 1. 学历与经验结构 ----------------
p("\n" + "=" * 84)
p("【1】有效样本学历与经验结构（n=%d）" % len(d))
p("=" * 84)
edu_vc = d["学历要求"].str.strip().value_counts()
p("-- 学历要求 --")
for k, v in edu_vc.items():
    lo, hi = wilson(v, len(d))
    p(f"   {k:<10}{v:>5}  {v/len(d)*100:5.2f}%  95%CI[{lo:.1f}%,{hi:.1f}%]")
k1 = int(d["直接可及"].sum()); k2 = int(d["潜在可及"].sum())
lo1, hi1 = wilson(k1, len(d)); lo2, hi2 = wilson(k2, len(d))
p(f"   → 直接可及(专科及以下)：{k1} = {k1/len(d)*100:.2f}%  95%CI[{lo1:.1f}%,{hi1:.1f}%]")
p(f"   → 潜在可及(＋学历不限)：{k2} = {k2/len(d)*100:.2f}%  95%CI[{lo2:.1f}%,{hi2:.1f}%]")

p("-- 经验要求 --")
exp_vc = d["经验要求"].astype(str).str.strip().replace("", "(空)").value_counts()
for k, v in exp_vc.items():
    lo, hi = wilson(v, len(d))
    p(f"   {k:<14}{v:>5}  {v/len(d)*100:5.2f}%  95%CI[{lo:.1f}%,{hi:.1f}%]")

p("-- 学历组 × 经验要求 --")
ct_ee = pd.crosstab(d["学历组"], d["经验要求"].astype(str).str.strip())
p(ct_ee.to_string())

# ---------------- 2. 岗位族 × 学历门槛 ----------------
p("\n" + "=" * 84)
p("【2】岗位族 × 学历门槛（潜在可及率，含Wilson 95%CI）")
p("=" * 84)
order = ["① 交付实施族（FDE型）", "② 解决方案/售前族", "③ 研发算法族",
         "④ 产品运营族", "⑤ AI应用/工具族", "⑥ 其他"]
fam_rows = []
p(f"{'岗位族':<22}{'n':>5}{'潜在可及':>9}{'可及率':>9}{'95%CI':>20}{'薪资中位':>9}")
for f in order:
    s = d[d["岗位族"] == f]
    if len(s) == 0: continue
    k = int(s["潜在可及"].sum())
    lo, hi = wilson(k, len(s))
    med = s["薪资K"].median()
    fam_rows.append({"岗位族": f, "n": len(s), "潜在可及数": k,
                     "潜在可及率": k / len(s) * 100, "CI_low": lo, "CI_high": hi,
                     "薪资中位数": med})
    p(f"{f:<22}{len(s):>5}{k:>9}{k/len(s)*100:>8.1f}%{'['+format(lo,'.1f')+','+format(hi,'.1f')+']':>20}{med:>9.1f}")
fam = pd.DataFrame(fam_rows)

# 2×2 列联表：交付实施族 vs 研发算法族 × 潜在可及
sub = d[d["岗位族"].isin(["① 交付实施族（FDE型）", "③ 研发算法族"])]
ct = pd.crosstab(sub["岗位族"], sub["潜在可及"])
p("\n-- 2×2 列联表（交付实施族 vs 研发算法族 × 潜在可及）--")
p(ct.to_string())
chi2, pv, dof, exp = stats.chi2_contingency(ct.values, correction=False)
phi = np.sqrt(chi2 / ct.values.sum())
# 列顺序：(0=不可及, 1=可及)；OR 以"可及"为事件，即 (交付可及×研发不可及)/(交付不可及×研发可及)
n_dlv_no, n_dlv_ok = int(ct.iloc[0, 0]), int(ct.iloc[0, 1])
n_rd_no, n_rd_ok = int(ct.iloc[1, 0]), int(ct.iloc[1, 1])
orv = (n_dlv_ok * n_rd_no) / (n_dlv_no * n_rd_ok)
se = np.sqrt(1/n_dlv_ok + 1/n_dlv_no + 1/n_rd_ok + 1/n_rd_no)
or_lo, or_hi = np.exp(np.log(orv) - 1.96 * se), np.exp(np.log(orv) + 1.96 * se)
p(f"   Pearson χ²={chi2:.3f}, df={dof}, p={pv:.6f}, Phi={phi:.3f}")
p(f"   OR（交付实施族相对研发算法族的专科潜在可及机会比）={orv:.2f}，95%CI[{or_lo:.2f}, {or_hi:.2f}]")

# ---------------- 3. 四维能力：岗位覆盖率 ----------------
p("\n" + "=" * 84)
p("【3】四维能力岗位覆盖率（专家3.3：标签频次与岗位覆盖率分开报告）")
p("=" * 84)
PROD_SAFETY = re.compile(r"房建|市政|机电安全|土建|注册安全工程师|工程安全|生产安全|施工")
DIM_RULES = [
    ("知安全", re.compile(r"安全|合规|隐私|伦理|审计|等保|脱敏|权限|风控|保密|治理|防泄漏|水印")),
    ("通模型", re.compile(r"\bAI\b|人工智能|大模型|LLM|GPT|Agent|智能体|模型|算法|推理|多模态|"
                       r"提示词|Prompt|RAG|检索增强|向量|机器学习|深度学习|NLP|视觉|语音|知识图谱|"
                       r"微调|Function|LangChain|MCP|AIGC|生成式|Qwen|通义|豆包|DeepSeek|Coze|扣子|"
                       r"Dify|vLLM|Copilot|强化学习", re.I)),
    ("能交付", re.compile(r"交付|部署|实施|上线|运维|监控|解决方案|培训|文档|驻场|现场|服务经验|"
                       r"售前|咨询|接口|集成|Docker|Kubernetes|容器|CI|CD|DevOps|PMP|项目管理|"
                       r"架构设计|性能优化|微服务|分布式|全栈|云平台|SaaS|低代码")),
    ("懂业务", re.compile(r"客户|业务|行业|制造|电商|零售|教育|金融|医疗|健康|交通|物流|政务|能源|"
                       r"电力|汽车|工业|广告|渠道|销售|面销|陌拜|需求分析|商务|CRM|ERP|OA|报表|BI|"
                       r"数据分析|市场营销|管理相关专业|企业服务|B端|C端|咨询|甲方")),
    ("技术工具", re.compile(r"Python|Java|JavaScript|TypeScript|C\+\+|SQL|MySQL|Linux|数据库|API|"
                        r"Redis|PostgreSQL|Git|Golang|\bGo\b|Hadoop|Hive|Vue|React|CSS|HTML|Spring|"
                        r"Django|Flask|Node|MongoDB|Oracle|Kafka|ETL|数据管道|PyTorch|\bC\b|"
                        r"嵌入式|BMS|小程序|爬虫|前端|后端|开发经验", re.I)),
]

def tag_dim(t):
    if PROD_SAFETY.search(t): return "非相关安全（生产安全）"
    for nm, pat in DIM_RULES:
        if pat.search(t): return nm
    return "未归类"

dim_counter = Counter(); tag_counter = Counter()
mat_rows = []
for _, r in d.iterrows():
    ts = [t.strip() for t in re.split(r"[,，;；/、]", str(r["技能标签"])) if t.strip()]
    ds = set()
    for t in ts:
        if len(t) > 20: continue
        dm = tag_dim(t)
        dim_counter[dm] += 1; tag_counter[t] += 1
        if dm not in ("未归类", "非相关安全（生产安全）"): ds.add(dm)
    mat_rows.append({nm: int(nm in ds) for nm, _ in DIM_RULES})
M = pd.DataFrame(mat_rows)
TOTAL_TAG = sum(dim_counter.values())
p(f"标签总出现次数 {TOTAL_TAG}，去重标签 {len(tag_counter)} 个")
p(f"\n{'能力维度':<10}{'标签次数':>9}{'标签占比':>10}{'岗位数':>8}{'岗位覆盖率':>12}{'95%CI':>20}")
cov = {}
for nm, _ in DIM_RULES:
    k = int(M[nm].sum()); n = len(M); lo, hi = wilson(k, n)
    cov[nm] = {"k": k, "rate": k/n*100, "lo": lo, "hi": hi, "tags": dim_counter[nm],
               "tag_pct": dim_counter[nm]/TOTAL_TAG*100}
    p(f"{nm:<10}{dim_counter[nm]:>9}{dim_counter[nm]/TOTAL_TAG*100:>9.1f}%{k:>8}{k/n*100:>11.1f}%{'['+format(lo,'.1f')+','+format(hi,'.1f')+']':>20}")

# ---------------- 4. Cochran's Q + McNemar + Holm ----------------
p("\n" + "=" * 84)
p("【4】四项政策能力覆盖率的总体差异：Cochran's Q（配对二分数据）")
p("=" * 84)
dims = [nm for nm, _ in DIM_RULES]                      # 含技术工具，仅用于描述
DIMS4 = ["懂业务", "通模型", "知安全", "能交付"]           # 414号文任务四的四项政策能力
X = M[DIMS4].values.astype(int)
n, k = X.shape
Tj = X.sum(axis=0); Ci = X.sum(axis=1); T = X.sum()
Q = (k - 1) * (k * (Tj ** 2).sum() - T ** 2) / (k * T - (Ci ** 2).sum())
p_q = 1 - stats.chi2.cdf(Q, k - 1)
p(f"   k={k} 项政策能力，n={n} 条岗位")
p(f"   T_j（各能力命中岗位数）={dict(zip(DIMS4, Tj.tolist()))}")
p(f"   Cochran's Q = {Q:.3f}, df={k-1}, p = {p_q:.3e}")
# 补充：把技术工具一并纳入做敏感性检验
X5 = M[dims].values.astype(int); k5 = X5.shape[1]
Tj5 = X5.sum(axis=0); Ci5 = X5.sum(axis=1); T5 = X5.sum()
Q5 = (k5 - 1) * (k5 * (Tj5 ** 2).sum() - T5 ** 2) / (k5 * T5 - (Ci5 ** 2).sum())
p(f"   [敏感性] 并入技术工具后的 5 项 Cochran's Q = {Q5:.3f}, df={k5-1}, "
  f"p = {1 - stats.chi2.cdf(Q5, k5-1):.3e}")

p("\n-- 两两比较：McNemar 检验 + Holm 校正（4项能力，6 组）--")
pairs = []
for i in range(k):
    for j in range(i + 1, k):
        a = DIMS4[i]; b = DIMS4[j]
        n11 = int(((X[:, i] == 1) & (X[:, j] == 1)).sum())
        n10 = int(((X[:, i] == 1) & (X[:, j] == 0)).sum())
        n01 = int(((X[:, i] == 0) & (X[:, j] == 1)).sum())
        disc = n10 + n01
        if disc < 25:  # 精确二项检验
            pv = stats.binomtest(min(n10, n01), disc, 0.5).pvalue * 1.0
            method = "exact"
            stat = float("nan")
        else:
            stat = (abs(n10 - n01) - 1) ** 2 / disc
            pv = 1 - stats.chi2.cdf(stat, 1)
            method = "χ²(cc)"
        pairs.append({"A": a, "B": b, "n10": n10, "n01": n01, "stat": stat, "p": pv, "method": method,
                      "disc": disc})
# McNemar 精确检验的双尾 p 已由 binomtest 给出；χ² 近似则再乘 2 由 chi2 尾部给出（单尾→双尾）
for pr in pairs:
    if pr["method"] == "χ²(cc)":
        pr["p"] = min(1.0, 2 * pr["p"])
pairs_sorted = sorted(pairs, key=lambda x: x["p"])
m = len(pairs_sorted)
prev_reject = True
for rank, pr in enumerate(pairs_sorted):
    alpha = 0.05 / (m - rank)
    reject = pr["p"] < alpha
    if not reject: prev_reject = False
    pr["holm_alpha"] = alpha; pr["holm_reject"] = bool(reject and prev_reject)
for pr in sorted(pairs, key=lambda x: (x["A"], x["B"])):
    p(f"   {pr['A']:<5} vs {pr['B']:<5}  不一致对 n10={pr['n10']:>4} n01={pr['n01']:>4}  "
      f"{pr['method']:<8} p={pr['p']:.3e}  Holmα={pr['holm_alpha']:.4f}  "
      f"{'✅显著' if pr['holm_reject'] else '—'}")

# ---------------- 5. 共现结构 ----------------
p("\n" + "=" * 84)
p("【5】四维政策能力共现结构")
p("=" * 84)
p("-- 共现矩阵（cell=同时含两者岗位数；对角线=该能力命中岗位数）--")
p(f"{'':<8}" + "".join(f"{nm:>10}" for nm in DIMS4))
co4 = {}
for i, a in enumerate(DIMS4):
    row = []
    for j in range(k):
        v = int(((X[:, i] == 1) & (X[:, j] == 1)).sum())
        row.append(v)
        co4[f"{a}|{DIMS4[j]}"] = v
    p(f"{a:<8}" + "".join(f"{v:>10}" for v in row))
p("\n-- 能力组合 Top12（一条岗位可多维命中）--")
combo = M.apply(lambda r: " + ".join([nm for nm in DIMS4 if r[nm]]) or "(无标签)", axis=1)
combo_vc = combo.value_counts()
for kk, vv in combo_vc.head(12).items():
    lo, hi = wilson(vv, n)
    p(f"   {kk:<40}{vv:>5}  {vv/n*100:5.1f}%  95%CI[{lo:.1f}%,{hi:.1f}%]")
n_multi3 = int((M[DIMS4].sum(axis=1) >= 3).sum())
p(f"   → 同时命中≥3项政策能力的岗位 {n_multi3} 条 = {n_multi3/n*100:.1f}%")
combos = [{"组合": kk, "n": int(vv), "pct": vv/n*100} for kk, vv in combo_vc.head(16).items()]

# ---------------- 6. 安全维度：标签 + 正文 ----------------
p("\n" + "=" * 84)
p("【6】安全治理语义的表达（标签层 + 职位正文层）")
p("=" * 84)
sec_tags = [(t, c) for t, c in tag_counter.items()
            if DIM_RULES[0][1].search(t) and not PROD_SAFETY.search(t)]
p(f"  安全类标签种类 {len(sec_tags)}，累计出现 {sum(c for _, c in sec_tags)} 次")
p(f"  明细：{sorted(sec_tags, key=lambda x: -x[1])}")
core = d[d["相关性"] == "A-核心FDE族"]
core_sec = int(sum(1 for _, r in core.iterrows() if any(
    DIM_RULES[0][1].search(t.strip()) and not PROD_SAFETY.search(t.strip())
    for t in re.split(r"[,，;；/、]", str(r["技能标签"])) if t.strip())))
p(f"  核心FDE族（n={len(core)}）中含安全类标签岗位 {core_sec} = {core_sec/len(core)*100:.1f}%")
txt = (d["职位描述"] + " " + d["任职要求"])
sec_word_rows = []
p(f"\n{'检索词':<12}{'命中条数':>9}{'命中率':>10}")
for w in ["数据安全", "AI安全", "大模型安全", "智能体安全", "隐私", "脱敏", "等保",
          "审计", "合规", "权限", "伦理"]:
    nn = int(txt.str.contains(w, regex=False).sum())
    lo, hi = wilson(nn, len(d))
    sec_word_rows.append({"词": w, "n": nn, "rate": nn/len(d)*100, "lo": lo, "hi": hi})
    p(f"{w:<12}{nn:>9}{nn/len(d)*100:>9.2f}%")
p("-- 对照：高频非安全语义 --")
for w in ["沟通", "培训", "现场", "出差"]:
    nn = int(txt.str.contains(w, regex=False).sum())
    p(f"{'  '+w:<12}{nn:>9}{nn/len(d)*100:>9.2f}%")

# ---------------- 7. 交付实施族内部学历—薪资 ----------------
p("\n" + "=" * 84)
p("【7】交付实施族内部学历—薪资（专家4.5要求重算）")
p("=" * 84)
fam1 = d[d["岗位族"] == "① 交付实施族（FDE型）"].copy()
rows7 = []
p(f"{'学历组':<12}{'n':>5}{'中位数':>9}{'P25':>8}{'P75':>8}{'均值':>8}")
for g in ["专科及以下", "学历不限", "本科", "硕士及以上"]:
    s = fam1[fam1["学历组"] == g]["薪资K"].dropna()
    if len(s) == 0: continue
    rows7.append({"学历组": g, "n": len(s), "median": s.median(),
                  "p25": s.quantile(.25), "p75": s.quantile(.75), "mean": s.mean()})
    p(f"{g:<12}{len(s):>5}{s.median():>9.1f}{s.quantile(.25):>8.1f}{s.quantile(.75):>8.1f}{s.mean():>8.1f}")
kw_groups = [fam1[fam1["学历组"] == g]["薪资K"].dropna().values
             for g in ["专科及以下", "学历不限", "本科", "硕士及以上"]]
kw_groups = [g for g in kw_groups if len(g) > 0]
H, p_kw = stats.kruskal(*kw_groups)
p(f"\n  Kruskal-Wallis（4组）H={H:.3f}, p={p_kw:.3e}")
low = fam1[fam1["学历组"].isin(["专科及以下", "学历不限"])]["薪资K"].dropna()
high = fam1[fam1["学历组"].isin(["本科", "硕士及以上"])]["薪资K"].dropna()
U, p_u = stats.mannwhitneyu(low, high, alternative="two-sided")
p(f"  Mann-Whitney U（专科及以下+不限 vs 本科及以上）U={U:.1f}, p={p_u:.3e}")
p(f"    低学历组 n={len(low)} 中位={low.median():.1f} | 高学历组 n={len(high)} 中位={high.median():.1f}")
# Cliff's delta 作为效应量
def cliffs_delta(a, b):
    a = np.asarray(a); b = np.asarray(b)
    gt = sum((x > b).sum() for x in a); lt = sum((x < b).sum() for x in a)
    return (gt - lt) / (len(a) * len(b))
p(f"    Cliff's delta = {cliffs_delta(low.values, high.values):.3f}")

# ---------------- 8. 全样本薪资与城市/规模 ----------------
p("\n" + "=" * 84)
p("【8】全样本薪资结构与区域/企业结构")
p("=" * 84)
sal = d["薪资K"].dropna()
p(f"  可解析 {len(sal)}/{len(d)} = {len(sal)/len(d)*100:.1f}%")
p(f"  中位数 {sal.median():.1f} | 均值 {sal.mean():.1f} | P25 {sal.quantile(.25):.1f} | "
  f"P75 {sal.quantile(.75):.1f} | P90 {sal.quantile(.9):.1f} | 区间 {sal.min():.1f}—{sal.max():.1f}")
p("\n  学历组 × 薪资（全样本）")
for g in ["专科及以下", "学历不限", "本科", "硕士及以上"]:
    s = d[d["学历组"] == g]["薪资K"].dropna()
    if len(s): p(f"    {g:<10} n={len(s):>4} 中位={s.median():>6.1f} P25={s.quantile(.25):>6.1f} P75={s.quantile(.75):>6.1f}")
p("\n  城市分布")
for kk, vv in d["来源城市"].astype(str).str.strip().value_counts().items():
    p(f"    {kk:<8}{vv:>5}  {vv/len(d)*100:5.1f}%")
p("\n  公司规模分布")
for kk, vv in d["公司规模"].astype(str).str.strip().replace("", "(空)").value_counts().items():
    p(f"    {kk:<16}{vv:>5}  {vv/len(d)*100:5.1f}%")

# ---------------- 导出 ----------------
out = {
    "n_keep": len(d), "n_salary": n_sal,
    "edu": {k: int(v) for k, v in edu_vc.items()},
    "direct_ok": {"k": k1, "rate": k1/len(d)*100},
    "potential_ok": {"k": k2, "rate": k2/len(d)*100},
    "exp": {str(k): int(v) for k, v in exp_vc.items()},
    "family": fam.to_dict("records"),
    "chi2_family_edu": {"chi2": chi2, "p": pv, "phi": phi, "OR": orv,
                        "OR_low": float(np.exp(np.log(orv)-1.96*se)),
                        "OR_high": float(np.exp(np.log(orv)+1.96*se))},
    "dim_coverage": cov, "dim_tag_counter": dict(dim_counter), "total_tag": TOTAL_TAG,
    "cochran_q": {"Q": Q, "df": k-1, "p": float(p_q), "Tj": dict(zip(DIMS4, Tj.tolist())),
                  "Q5_sensitivity": float(Q5)},
    "mcnemar": pairs_sorted, "co4": co4,
    "combos": combos, "n_multi3": n_multi3,
    "sec_tags": sec_tags, "core_sec": core_sec, "n_core": len(core),
    "sec_words": sec_word_rows,
    "fam1_edu_salary": rows7,
    "kw_fam1": {"H": H, "p": float(p_kw)},
    "mw_fam1": {"U": U, "p": float(p_u), "low_med": float(low.median()),
                "high_med": float(high.median()), "low_n": int(len(low)), "high_n": int(len(high)),
                "cliffs_delta": float(cliffs_delta(low.values, high.values))},
    "salary_all": {"median": float(sal.median()), "mean": float(sal.mean()),
                   "p25": float(sal.quantile(.25)), "p75": float(sal.quantile(.75)),
                   "p90": float(sal.quantile(.9)), "min": float(sal.min()), "max": float(sal.max()),
                   "by_edu": {g: {"n": int(len(d[d['学历组']==g]['薪资K'].dropna())),
                                  "median": float(d[d['学历组']==g]['薪资K'].dropna().median())}
                              for g in ["专科及以下", "学历不限", "本科", "硕士及以上"]}},
    "city": {str(k): int(v) for k, v in d["来源城市"].astype(str).str.strip().value_counts().items()},
    "scale": {str(k): int(v) for k, v in d["公司规模"].astype(str).str.strip().replace("", "(空)").value_counts().items()},
}
json.dump(out, open(os.path.join(OUT, "_专家版_指标.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
M.to_csv(os.path.join(OUT, "_专家版_能力矩阵.csv"), index=False, encoding="utf-8-sig")
with open(os.path.join(OUT, "_s6_专家版统计.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(R))
print("\n>>> 已写出 _专家版_指标.json / _专家版_能力矩阵.csv / _s6_专家版统计.txt")
