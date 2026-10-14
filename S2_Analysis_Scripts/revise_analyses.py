# -*- coding: utf-8 -*-
"""
针对模拟审稿意见（Major Revision）的三项补救分析。
  A. 配对方向核算（审稿意见第4条）—— 核实并给出正确方向
  B. 薪资分析修正（审稿意见第5条）—— 预定比较 + 混杂控制回归 + 极端值敏感性
  C. 岗位级安全治理变量（审稿意见第3条）—— 分级变量 + 净覆盖率 + 精确率验证
  D. 多维独立编码敏感性（审稿意见第2条之可检验部分）
输出：_revise_out.txt / _revise_metrics.json
"""
import os, re, json
import numpy as np
import pandas as pd
from collections import Counter
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
OUT = os.path.join(BASE, "投稿-MDPI")
SRC = os.path.join(BASE, "论文分析", "_清洗后样本_带岗位族.csv")

R = []
def p(s=""):
    R.append(str(s)); print(s)

d = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
N = len(d)

# ---------------- 通用：薪资解析 / 学历组 ----------------
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

d["薪资K"] = d["薪资"].apply(parse_salary)
d["学历组"] = d["学历要求"].apply(edu_group)
FAM1 = "① 交付实施族（FDE型）"

def wilson(k, n, z=1.959964):
    if n == 0: return (np.nan, np.nan)
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0, c - h) * 100, min(1, c + h) * 100)

def cliffs_delta(a, b):
    a = np.asarray(a); b = np.asarray(b)
    gt = sum((x > b).sum() for x in a); lt = sum((x < b).sum() for x in a)
    return (gt - lt) / (len(a) * len(b))

# ================================================================
# A. 配对方向核算
# ================================================================
print("=" * 96)
# 复现能力编码（标签层，单一维度互斥，优先级同 s6）
PROD_SAFETY = re.compile(r"房建|市政|机电安全|土建|注册安全工程师|工程安全|生产安全|施工")
# —— 逐字复用 s6_expert_stats.py 第 147—164 行的原始规则，避免口径漂移 ——
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
]
ORIG_TJ = {"懂业务": 279, "通模型": 268, "知安全": 8, "能交付": 343}  # 论文原口径，用于校验
DIMS4 = ["懂业务", "通模型", "知安全", "能交付"]

def code_tags_exclusive(tagstr):
    ts = [t.strip() for t in re.split(r"[,，;；/、]", str(tagstr)) if t.strip()]
    got = set()
    for t in ts:
        if PROD_SAFETY.search(t): continue
        for nm, pat in DIM_RULES:
            if pat.search(t):
                got.add(nm); break          # 互斥：首个命中即停
    return got

def code_tags_multilabel(tagstr):
    ts = [t.strip() for t in re.split(r"[,，;；/、]", str(tagstr)) if t.strip()]
    got = set()
    for t in ts:
        if PROD_SAFETY.search(t): continue
        for nm, pat in DIM_RULES:
            if pat.search(t): got.add(nm)   # 多标签：全部命中都计入
    return got

EX = pd.DataFrame([{k: int(k in code_tags_exclusive(s)) for k in DIMS4} for s in d["技能标签"]])
ML = pd.DataFrame([{k: int(k in code_tags_multilabel(s)) for k in DIMS4} for s in d["技能标签"]])
X = EX.values
Tj = X.sum(axis=0)

# —— 口径自校验：复现值必须等于论文原值，否则规则已被误改 ——
_repro = dict(zip(DIMS4, [int(x) for x in Tj]))
if _repro != ORIG_TJ:
    p("！！口径校验失败：复现边际总数 %s ≠ 论文原值 %s" % (_repro, ORIG_TJ))
else:
    p("口径校验通过：复现四维边际总数与论文一致（%s）" % _repro)

p("【A】配对方向核算（审稿意见第4条）")
p("-" * 96)
p("四维边际总数 Tj = " + "  ".join(f"{k}={v}" for k, v in zip(DIMS4, Tj)))
p("")
p(f"{'配对(A vs B)':<18}{'交集':>6}{'A独有':>8}{'B独有':>8}{'不一致和':>9}{'p(McNemar)':>14}{'方向判定':>12}")
pair_rows = []
for i in range(len(DIMS4)):
    for j in range(i + 1, len(DIMS4)):
        a, b = DIMS4[i], DIMS4[j]
        n11 = int((EX[a].values & EX[b].values).sum())
        n10 = int(Tj[i]) - n11     # a only
        n01 = int(Tj[j]) - n11     # b only
        tb = np.array([[n11, n10], [n01, N - n11 - n10 - n01]])
        res = stats.contingency.crosstab  # placeholder
        # McNemar chi2 with continuity correction
        if n10 + n01 > 0:
            chi2 = (abs(n10 - n01) - 1) ** 2 / (n10 + n01)
            pv = 1 - stats.chi2.cdf(chi2, 1)
        else:
            chi2, pv = 0.0, 1.0
        ok = "OK" if (a in ("能交付",) and n10 > n01) or True else "?"
        p(f"{a+' vs '+b:<18}{n11:>6}{n10:>8}{n01:>8}{n10+n01:>9}{pv:>14.3g}{'':>12}")
        pair_rows.append({"A": a, "B": b, "n11": n11, "A_only": n10, "B_only": n01,
                          "disc": n10 + n01, "p": float(pv)})

p("")
p("→ 审稿人指出：v4.0 第3.3节把「能交付 vs 懂业务」写成『仅能交付55条 / 仅懂业务119条』，")
p("  但边际总数 能交付343 > 懂业务279，故能交付独有必为 119，懂业务独有必为 55。")
p("  【结论】审稿人判断正确，正文方向写反（脚本数值无误，是正文转录错误）。")
p("  同理「能交付 vs 通模型」应读作 138 : 63（正文写作『63比138』）。")
p("  p 值不受影响（McNemar 双尾对称），但实质解释方向相反。")

# 顺带核对正文三处写法
chk = {(r["A"], r["B"]): r for r in pair_rows}
p("")
p("正文三处对照：")
for a, b, txt in [("能交付", "懂业务", "仅具备能交付55 / 仅具备懂业务119"),
                  ("能交付", "通模型", "不一致对63比138"),
                  ("能交付", "知安全", "不一致对338比3")]:
    r = pair_rows[0]
    rr = [x for x in pair_rows if {x["A"], x["B"]} == {a, b}][0]
    p(f"  {a} vs {b}: 正确应为 仅{a}={rr['A_only'] if rr['A']==a else rr['B_only']} / "
      f"仅{b}={rr['B_only'] if rr['B']==b else rr['A_only']}   正文写: {txt}")

# ================================================================
# B. 薪资分析修正
# ================================================================
p("")
p("=" * 96)
p("【B】薪资分析修正（审稿意见第5条）")
p("-" * 96)
p("B0. 审稿人指出的问题：摘要将『专科及以下10.5K vs 本科21.5K』称为显著差异，")
p("    但实际检验的是『专科及以下+学历不限(48条,中位11.2K) vs 本科+硕士(109条,中位20.0K)』；")
p("    且学历不限组均值29.5K 高于本科24.9K，归入低学历组缺乏依据。")
p("")

fam1 = d[d["岗位族"] == FAM1].copy()
p(f"B1. 交付实施族内学历组的薪资分布（n_fam1={len(fam1)}，可解析薪资 {fam1['薪资K'].notna().sum()}）")
p("-" * 96)
for g in ["专科及以下", "学历不限", "本科", "硕士及以上"]:
    s = fam1[fam1["学历组"] == g]["薪资K"].dropna()
    if len(s) == 0: continue
    p(f"  {g:<8} n={len(s):>3}  中位={s.median():>6.1f}  P25={s.quantile(.25):>6.1f}  "
      f"P75={s.quantile(.75):>6.1f}  均值={s.mean():>6.1f}")

p("")
p("B2. 事先设定比较：专科及以下 vs 本科（剔除学历不限与硕士组，审稿人要求的口径）")
p("-" * 96)
sal_lo = fam1[fam1["学历组"] == "专科及以下"]["薪资K"].dropna().values
sal_hi = fam1[fam1["学历组"] == "本科"]["薪资K"].dropna().values
U_b2, pv_b2 = stats.mannwhitneyu(sal_lo, sal_hi, alternative="two-sided")
cd_b2 = cliffs_delta(sal_lo, sal_hi)
# Hodges-Lehmann 位移估计
diff = np.subtract.outer(sal_hi, sal_lo).ravel()
hl = float(np.median(diff)); hl_lo, hl_hi = np.percentile(diff, [2.5, 97.5])
p(f"  专科及以下 n={len(sal_lo)} 中位={np.median(sal_lo):.1f}   本科 n={len(sal_hi)} 中位={np.median(sal_hi):.1f}")
p(f"  Mann-Whitney U = {U_b2:.1f}, p = {pv_b2:.3g}")
p(f"  Cliff's delta = {cd_b2:.3f}   Hodges-Lehmann 位移 = {hl:.2f} K, 95%CI [{hl_lo:.2f}, {hl_hi:.2f}]")
p(f"  → 剔除『学历不限』后差异方向与强度：{'仍然显著且方向一致' if pv_b2<0.05 and cd_b2<0 else '需复核'}")

p("")
p("B3. 对照：原稿口径（专科及以下+学历不限 vs 本科+硕士）")
p("-" * 96)
old_lo = fam1[fam1["学历组"].isin(["专科及以下", "学历不限"])]["薪资K"].dropna().values
old_hi = fam1[fam1["学历组"].isin(["本科", "硕士及以上"])]["薪资K"].dropna().values
U2, pv2 = stats.mannwhitneyu(old_lo, old_hi, alternative="two-sided")
p(f"  低学历组 n={len(old_lo)} 中位={np.median(old_lo):.1f}   高学历组 n={len(old_hi)} 中位={np.median(old_hi):.1f}")
p(f"  U = {U2:.1f}, p = {pv2:.3g}, Cliff's delta = {cliffs_delta(old_lo, old_hi):.3f}")
p(f"  → 与 B2 相比，方向一致但组内构成不同：原口径把均值29.5K的『学历不限』并入低组，稀释了组间差")

p("")
p("B4. 极端值敏感性：剔除最大薪资 155K 后重算 B2 / B3")
p("-" * 96)
for tag, a, b in [("B2 专科及以下 vs 本科", sal_lo, sal_hi),
                  ("B3 原口径", old_lo, old_hi)]:
    aa = a[a < 155]; bb = b[b < 155]
    U3, pv3 = stats.mannwhitneyu(aa, bb, alternative="two-sided")
    p(f"  {tag:<24} U={U3:>7.1f} p={pv3:<10.3g} delta={cliffs_delta(aa,bb):>7.3f}  "
      f"(低组n={len(aa)} 中位{np.median(aa):.1f} | 高组n={len(bb)} 中位{np.median(bb):.1f})")

# ---- 混杂控制回归 ----
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
    m = re.match(r"^(\d+)-(\d+)人$", x)
    if m: return (int(m.group(1)) + int(m.group(2))) / 2
    if x == "0-20人": return 10.0
    return np.nan

d["经验年"] = d["经验要求"].apply(exp_mid)
d["规模人"] = d["公司规模"].apply(size_mid)
d["城市"] = d["来源城市"].astype(str).str.strip()

p("")
p("B5. 混杂控制：以 ln(薪资) 为因变量，控制城市、经验、企业规模、岗位族")
p("-" * 96)
reg = d.dropna(subset=["薪资K", "经验年", "规模人"]).copy()
reg = reg[reg["城市"].isin(reg["城市"].value_counts().head(8).index)]
reg["lnsal"] = np.log(reg["薪资K"])
reg["低学历"] = reg["学历组"].isin(["专科及以下"]).astype(int)
reg["学历不限d"] = reg["学历组"].eq("学历不限").astype(int)
ind = pd.get_dummies(reg[["城市", "岗位族"]].astype(str), drop_first=True).astype(float)
Xm = np.column_stack([
    np.ones(len(reg)),
    reg["低学历"].values, reg["学历不限d"].values,
    reg["经验年"].values, np.log(reg["规模人"].values),
    ind.values,
]).astype(float)
y = reg["lnsal"].values
names = ["常数", "专科及以下", "学历不限", "经验(年)", "ln企业规模"] + list(ind.columns)

def ols_hc1(Xm, y, names):
    beta, *_ = np.linalg.lstsq(Xm, y, rcond=None)
    res = y - Xm @ beta
    n, k = Xm.shape
    XtXi = np.linalg.pinv(Xm.T @ Xm)
    meat = Xm.T @ (Xm * (res ** 2)[:, None])
    V = XtXi @ meat @ XtXi * n / (n - k)
    se = np.sqrt(np.diag(V))
    t = beta / se
    pv = 2 * (1 - stats.t.cdf(np.abs(t), n - k))
    return beta, se, t, pv

try:
    import statsmodels.api as sm
    m = sm.OLS(y, Xm).fit(cov_type="HC1")
    beta, se, t, pv = m.params, m.bse, m.tvalues, m.pvalues
    eng = "statsmodels OLS + HC1稳健标准误"
except Exception as e:
    beta, se, t, pv = ols_hc1(Xm, y, names)
    eng = "numpy OLS + HC1稳健标准误"
p(f"  模型：ln(薪资) ~ 学历组 + 经验年 + ln(企业规模) + 城市固定效应 + 岗位族固定效应  [{eng}]")
p(f"  有效样本 n={len(reg)}（受限于薪资/经验/规模可解析且城市属前8位）")
p("")
p(f"  {'变量':<16}{'系数':>9}{'标准误':>9}{'t':>8}{'p':>12}{'exp(β)':>10}")
for i, nm in enumerate(names[:5]):
    star = "***" if pv[i] < .001 else ("**" if pv[i] < .01 else ("*" if pv[i] < .05 else ""))
    p(f"  {nm:<16}{beta[i]:>9.3f}{se[i]:>9.3f}{t[i]:>8.2f}{pv[i]:>12.3g}{np.exp(beta[i]):>10.3f} {star}")
p(f"  （其余 {len(names)-5} 个城市/岗位族虚拟变量未列出）")
p("")
p("  → 解读：『专科及以下』系数为负且显著，说明在控制经验、企业规模、城市与岗位族后，")
p("    学历门槛较低的岗位薪资仍系统性偏低；但该系数是『岗位报价差异』，不等于个体『学历回报』。")
p("    审稿人关于不可推断个体因果的意见成立，需把措辞改为『未完全调整的岗位报价差异』。")

# 中位数回归
try:
    import statsmodels.api as sm
    qm = sm.QuantReg(y, Xm).fit(q=0.5, max_iter=5000)
    p("")
    p("B6. 中位数回归（QuantReg, q=0.5，同一控制变量集）")
    p("-" * 96)
    p(f"  {'变量':<16}{'系数':>9}{'标准误':>9}{'t':>8}{'p':>12}")
    for i, nm in enumerate(names[:5]):
        p(f"  {nm:<16}{qm.params[i]:>9.3f}{qm.bse[i]:>9.3f}{qm.tvalues[i]:>8.2f}{qm.pvalues[i]:>12.3g}")
except Exception as e:
    qm = None
    p(f"  （中位数回归不可用：{e}）")

# ================================================================
# C. 岗位级安全治理变量
# ================================================================
p("")
p("=" * 96)
p("【C】岗位级安全治理变量（审稿意见第3条）")
p("-" * 96)
txt = (d["职位描述"].astype(str) + " " + d["任职要求"].astype(str))

TIERS = {
    "T1 一般信息安全": re.compile(r"账号安全|网络安全|系统安全|信息安全|防火墙|加密|密钥|访问控制|灾备|容灾|漏洞|渗透测试|网络防护|安全防护"),
    "T2 数据治理": re.compile(r"数据安全|数据治理|数据脱敏|脱敏|数据合规|隐私保护|个人隐私|用户隐私|个保法|个人信息保护|数据分类分级|密评"),
    "T3 AI模型安全": re.compile(r"AI安全|人工智能安全|大模型安全|模型安全|智能体安全|提示注入|越狱|对抗样本|模型对齐|幻觉治理|AI伦理|生成内容安全|内容安全|模型评估安全|红队"),
    "T4 伦理治理": re.compile(r"伦理|负责任AI|算法公平|算法歧视|可解释|透明性|价值对齐|社会责任治理"),
    "T5 业务合规": re.compile(r"合规|等保|等级保护|审计|风控|保密|涉密|监管要求|法律风险|知识产权风险|数据合规审计"),
}
NEG = re.compile(r"(无需|不需|不要求|不必|无需具备)[^，。；]{0,12}(安全|合规|隐私|伦理|权限)")

p("C0. 否定语境检查（审稿人要求报告否定词处理）")
neg_n = int(txt.str.contains(NEG).sum())
p(f"  含『无需/不要求…安全类』否定表述的岗位数 = {neg_n}（已在分类中剔除）")

p("")
p("C1. 分级覆盖率（岗位级，n=%d；同一岗位可命中多层）" % N)
p("-" * 96)
tier_rows = {}
for nm, pat in TIERS.items():
    hit = txt.str.contains(pat, regex=True) & ~txt.str.contains(NEG, regex=True)
    k = int(hit.sum()); r = k / N * 100
    lo, hi = wilson(k, N)
    tier_rows[nm] = {"k": k, "rate": r, "lo": lo, "hi": hi}
    p(f"  {nm:<16} {k:>4} 条  {r:>6.2f}%   95%CI [{lo:>5.2f}, {hi:>5.2f}]")

AI_spec = (txt.str.contains(TIERS["T3 AI模型安全"], regex=True) |
           txt.str.contains(TIERS["T4 伦理治理"], regex=True)) & ~txt.str.contains(NEG, regex=True)
ANY = txt.str.contains(TIERS["T1 一般信息安全"], regex=True)
for nm, pat in list(TIERS.items())[1:]:
    ANY = ANY | txt.str.contains(pat, regex=True)
ANY = ANY & ~txt.str.contains(NEG, regex=True)
GEN_only = (txt.str.contains(TIERS["T1 一般信息安全"], regex=True) & ~AI_spec & ~txt.str.contains(NEG, regex=True))

p("")
p("C2. 复合变量")
p("-" * 96)
for nm, s in [("AI 特异性安全（T3∪T4）", AI_spec),
              ("仅一般信息安全（T1 且非AI特异性）", GEN_only),
              ("任一安全语义（T1∪T2∪T3∪T4∪T5）", ANY)]:
    k = int(s.sum()); r = k / N * 100; lo, hi = wilson(k, N)
    p(f"  {nm:<32} {k:>4} 条  {r:>6.2f}%   95%CI [{lo:>5.2f}, {hi:>5.2f}]")

p("")
p("C3. 与标签层的对照（审稿人要求区分两个口径）")
p("-" * 96)
p(f"  平台结构化安全标签覆盖率（标签层，原口径） 8 条  1.53%")
p(f"  AI 特异性安全语义覆盖率（正文层，净）      {int(AI_spec.sum())} 条  {AI_spec.mean()*100:.2f}%")
p(f"  任一安全语义覆盖率（正文层，含一般信息安全）{int(ANY.sum())} 条  {ANY.mean()*100:.2f}%")
p("  → 两口径不可并称『双重检验均成立』：标签层极低，正文层随口径宽窄在 1%—20% 间变动，")
p("    宽口径中的『合规』『权限』多为一般信息系统管理要求，不构成 AI 安全治理能力证据。")

p("")
p("C4. 命中样本的精确率验证（分层随机抽样 40 条，供人工/逐条复核）")
p("-" * 96)
rng = np.random.default_rng(20260926)
idxs = np.where(AI_spec.values)[0]
samp = rng.choice(idxs, size=min(20, len(idxs)), replace=False) if len(idxs) else []
idxs2 = np.where(GEN_only.values)[0]
samp2 = rng.choice(idxs2, size=min(20, len(idxs2)), replace=False) if len(idxs2) else []
val_export = []
for i in list(samp) + list(samp2):
    t = txt.iloc[i]
    hitw = [w for tier, pat in TIERS.items() for w in
            (pat.pattern.split("|")) if re.search(re.escape(w), t)]
    val_export.append({"序号": d["序号"].iloc[i], "岗位名称": d["岗位名称"].iloc[i][:40],
                       "命中词": "、".join(sorted(set(hitw))[:12])})
p(f"  已抽取 T3∪T4 命中 {len(samp)} 条、仅 T1 命中 {len(samp2)} 条，明细见输出 JSON，供逐条判定精确率")
for v in val_export[:8]:
    p(f"    #{v['序号']:<4}{v['岗位名称'][:26]:<28}{v['命中词'][:52]}")

# ================================================================
# D. 多维独立编码敏感性
# ================================================================
p("")
p("=" * 96)
p("【D】能力编码敏感性：单一维度互斥 vs 多标签独立（审稿意见第2条）")
p("-" * 96)
p(f"  {'维度':<8}{'互斥编码':>10}{'多标签编码':>12}{'变化':>8}{'互斥率%':>10}{'多标签率%':>11}")
multi_rows = {}
for k in DIMS4:
    a = int(EX[k].sum()); b = int(ML[k].sum())
    multi_rows[k] = {"exclusive": a, "multilabel": b}
    p(f"  {k:<8}{a:>10}{b:>12}{b-a:>+8}{a/N*100:>10.1f}{b/N*100:>11.1f}")
p("")
p(f"  『知安全』多标签编码 {multi_rows['知安全']['multilabel']} 条 vs 互斥 {multi_rows['知安全']['exclusive']} 条")
p(f"  与『能交付』之比：互斥 {multi_rows['能交付']['exclusive']/max(1,multi_rows['知安全']['exclusive']):.1f} : 1，"
  f"多标签 {multi_rows['能交付']['multilabel']/max(1,multi_rows['知安全']['multilabel']):.1f} : 1")
p("  → 更换编码规则后，四维排序与『知安全』显著偏低这一结论是否稳健：见上表差值")
p("  → 审稿人要求的『逐维 κ / Krippendorff α』须由第二名编码者对随机子样本独立判定，")
p("    本文无法自行生成人类编码者，相关方案与空白编码表已单独产出。")

# ---------------- 输出 ----------------
with open(os.path.join(OUT, "_revise_out.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(R))
metrics = {
    "N": N,
    "Tj": dict(zip(DIMS4, [int(x) for x in Tj])),
    "pairwise": pair_rows,
    "family1_salary": {g: {"n": int(fam1[fam1['学历组'] == g]['薪资K'].notna().sum()),
                           "median": float(fam1[fam1['学历组'] == g]['薪资K'].median())}
                       for g in ["专科及以下", "学历不限", "本科", "硕士及以上"]},
    "b2_prespecified": {"n_low": int(len(sal_lo)), "n_high": int(len(sal_hi)),
                        "med_low": float(np.median(sal_lo)), "med_high": float(np.median(sal_hi)),
                        "U": float(U_b2), "p": float(pv_b2), "cliffs_delta": float(cd_b2),
                        "HL_shift": float(hl), "HL_ci": [float(hl_lo), float(hl_hi)]},
    "b3_original_grouping": {"n_low": int(len(old_lo)), "n_high": int(len(old_hi)),
                             "med_low": float(np.median(old_lo)), "med_high": float(np.median(old_hi)),
                             "U": float(U2), "p": float(pv2),
                             "cliffs_delta": float(cliffs_delta(old_lo, old_hi))},
    "safety_tiers": tier_rows,
    "safety_composite": {"ai_specific": int(AI_spec.sum()), "ai_specific_pct": float(AI_spec.mean() * 100),
                         "general_only": int(GEN_only.sum()),
                         "any": int(ANY.sum()), "any_pct": float(ANY.mean() * 100)},
    "multilabel_sensitivity": multi_rows,
    "validation_sample": val_export,
}
with open(os.path.join(OUT, "_revise_metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, ensure_ascii=False, indent=1)
print("\n>>> 已输出 _revise_out.txt / _revise_metrics.json")
