# -*- coding: utf-8 -*-
"""第2步：招聘数据清洗与诊断（v2，含近重复去重）。

v2 变更（依据《专家意见》与《论文重构大纲与写作方案》第十四节）：
  1) 在相关性筛选之前，新增"详情链接去重"与"近重复复核"两个步骤，
     并把去重规则与剔除记录如实输出，供论文3.2节照实书写；
  2) 统一去重技能标签口径说明（长度>20字符的异常项过滤）。

发现的问题：
  A. 665条由9个关键词拼合而成，其中"AI Infra""推理部署"等词捞入大量传统制造业岗位
  B. "行业"列有579条为"公司基本信息"，"融资阶段"列混入公司名 —— 爬取时字段错位
"""
import os
import re
import json
import difflib
from collections import Counter

import pandas as pd

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
df = pd.read_csv(os.path.join(BASE, "BOSS招聘数据-广东.csv"), encoding="utf-8-sig", dtype=str,
                 keep_default_na=False)

log = []


def p(s=""):
    log.append(str(s))
    print(s)


# ============ 一、字段错位问题的确认 ============
p("=" * 80)
p("一、字段错位问题的确认")
p("=" * 80)
for col in ["行业", "融资阶段"]:
    s = df[col].astype(str).str.strip()
    bad = s.isin(["公司基本信息", ""]) | s.str.contains("公司$|上市公司|知名", regex=True)
    p(f"{col}: 疑似错位/无效 {bad.sum()} / {len(df)}")
p("\n行业列 原始值样例（含错位）:")
for v in df["行业"].astype(str).str.strip().value_counts().head(8).items():
    p(f"   {v[0][:46]:<48} {v[1]}")

# ============ 二、去重（链接去重 + 近重复复核） ============
p("\n" + "=" * 80)
p("二、重复记录处理（论文3.2节第1—2步）")
p("=" * 80)
n_raw = len(df)
df = df.drop_duplicates(subset=["详情链接"], keep="first").reset_index(drop=True)
n_link_dup = n_raw - len(df)
p(f"步骤1 详情链接去重：原始 {n_raw} 条，链接完全重复 {n_link_dup} 条，剩余 {len(df)} 条")

# 近重复规则（v3，经三组校验后修订）：
#   以「公司核心名」分组（跨公司雷同对数=0，无需跨公司合并；岗位名不设硬条件，
#   因为"数采支持部署专员-双休"这类仅差后缀、或标题被平台截断的重复会被漏去）；
#   组内职位正文相似度 = max(整体difflib比, 最长公共块/较短文本) ≥ 0.95 判为重复发布。
#   阈值取 0.95 而非 0.90：腾讯"企微/微信搜索"等不同团队的同模板JD相似度为0.85—0.91，
#   属不同岗位，不应合并（敏感性检验见论文3.2节）。
def comp_core(s):
    return re.sub(r"(有限公司|股份有限公司|科技|网络|信息|技术|集团|股份)", "", str(s)).strip()


def jd_sim(a, b):
    if not a or not b or min(len(a), len(b)) < 200:
        return 0.0
    r = difflib.SequenceMatcher(None, a, b).ratio()
    m = difflib.SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b))
    return max(r, m.size / min(len(a), len(b)))


_cc = df["公司"].apply(comp_core)
_title = df["岗位名称"].astype(str).str.strip()
_jd = df["职位描述"].astype(str).str.replace(r"\s+", "", regex=True)

drop_idx = set()
DROP_LOG = []
for _c, g in df.groupby(_cc):
    idx = list(g.index)
    if len(idx) < 2:
        continue
    for i in range(len(idx)):
        if idx[i] in drop_idx:
            continue
        for j in range(i + 1, len(idx)):
            if idx[j] in drop_idx:
                continue
            s = jd_sim(_jd[idx[i]], _jd[idx[j]])
            if s >= 0.95:
                drop_idx.add(idx[j])
                DROP_LOG.append({"公司核心": _c, "保留岗位": _title[idx[i]], "剔除岗位": _title[idx[j]],
                                 "相似度": round(s, 3), "保留城市": df.at[idx[i], "来源城市"],
                                 "剔除城市": df.at[idx[j], "来源城市"],
                                 "保留薪资": df.at[idx[i], "薪资"], "剔除薪资": df.at[idx[j], "薪资"]})
p(f"步骤2 近重复复核：以「公司核心名」分组，职位正文相似度≥0.95（整体相似度与包含度取大）"
  f"判定为重复发布，仅保留首条，剔除 {len(drop_idx)} 条，剩余 {len(df) - len(drop_idx)} 条")
p("  剔除明细：")
for r in sorted(DROP_LOG, key=lambda x: -x["相似度"]):
    p(f"    {r['公司核心'][:16]:<18}「{r['保留岗位'][:22]}」↔「{r['剔除岗位'][:22]}」 "
      f"sim={r['相似度']:.3f}  {r['保留城市']}→{r['剔除城市']}")
df = df.drop(index=list(drop_idx)).reset_index(drop=True)
n_after_dedup = len(df)

# ============ 三、相关性分级规则 ============
p("\n" + "=" * 80)
p("三、相关性分级规则（论文3.2节第3步）")
p("=" * 80)

CORE_PAT = re.compile(
    r"FDE|前沿部署|前线部署|AI交付|AI应用交付|AI部署|应用部署|交付工程师|交付专家|"
    r"解决方案工程师|实施交付|技术交付|大模型部署|模型部署|推理部署|AI全栈交付",
    re.I)
NEAR_PAT = re.compile(
    r"AI解决方案|人工智能解决方案|AI实施|实施顾问|大模型|智能体|Agent|AI应用|"
    r"AI Infra|AI平台|AI产品|AI项目经理|提示词|Prompt|知识库|RAG|数字化顾问|售前",
    re.I)
IRRELEVANT_PAT = re.compile(
    r"SQE|供应商质量|电镀|焊接|模具|非标自动化|机械设计|结构工程师|电气工程师|硬件工程师|"
    r"嵌入式(?!AI)|厂房|物业|质量工程师|工艺(开发|工程)|设备工程师|数据标注|"
    r"短视频|直播|出题|训练师|美工|客服|销售代表|sqe|安卓|iOS|前端|测试工程师|"
    r"数控|装配|注塑|冲压|暖通|给排水|土建|监理|预算",
    re.I)

df["_judge"] = (df["岗位名称"].astype(str) + " || " + df["职位描述"].astype(str).str[:600])


def grade(row):
    t = row["_judge"]
    name = str(row["岗位名称"])
    if IRRELEVANT_PAT.search(name):
        return "D-无关"
    if CORE_PAT.search(name):
        return "A-核心FDE族"
    if CORE_PAT.search(t):
        return "B-交付邻域"
    if NEAR_PAT.search(name) or NEAR_PAT.search(t):
        return "C-泛AI相关"
    if IRRELEVANT_PAT.search(t):
        return "D-无关"
    return "C-泛AI相关"


df["相关性"] = df.apply(grade, axis=1)
p(df["相关性"].value_counts().sort_index().to_string())

p("\n-- 各级 × 来源关键词 交叉 --")
p(pd.crosstab(df["来源关键词"], df["相关性"]).to_string())

p("\n-- D-无关 的岗位名称 Top25 --")
p(df.loc[df["相关性"] == "D-无关", "岗位名称"].value_counts().head(25).to_string())

# ============ 四、清洗后（A+B+C）核心样本的分布 ============
p("\n" + "=" * 80)
p("四、清洗后（A+B+C）核心样本的分布")
p("=" * 80)
keep = df[df["相关性"] != "D-无关"].copy().reset_index(drop=True)
p(f"保留 {len(keep)} / {len(df)} 条（去重后），剔除 {len(df) - len(keep)} 条")
p(f"样本流程：原始 {n_raw} → 链接去重 {n_link_dup} → 近重复剔除 {len(drop_idx)} "
  f"→ 去重后 {n_after_dedup} → 相关性筛选剔除 {len(df) - len(keep)} → 有效样本 {len(keep)}")
p(f"以原始 {n_raw} 条为基数的有效样本率 = {len(keep) / n_raw * 100:.1f}%")

for col in ["学历要求", "经验要求", "来源城市", "公司规模"]:
    p(f"\n-- {col} --")
    p(keep[col].astype(str).str.strip().replace("", "(空)").value_counts().to_string())

p("\n-- 学历要求（去重后全部条数，对照）--")
p(df["学历要求"].astype(str).str.strip().value_counts().to_string())

# ============ 五、技能标签词表盘点 ============
p("\n" + "=" * 80)
p("五、技能标签词表盘点")
p("=" * 80)
tags_all, tags_valid = [], []
for v in keep["技能标签"].astype(str):
    for t in re.split(r"[,，;；/、]", v):
        t = t.strip()
        if t and t != "nan":
            tags_all.append(t)
            if len(t) <= 20:
                tags_valid.append(t)
cnt_all, cnt_valid = Counter(tags_all), Counter(tags_valid)
p(f"标签总出现次数 {len(tags_valid)}（已过滤长度>20字符的异常项 {len(tags_all) - len(tags_valid)} 次）")
p(f"去重标签数：未过滤口径 {len(cnt_all)} 个；论文采用口径（长度≤20字符）{len(cnt_valid)} 个")
p("\n-- 全部标签词频（降序，前80）--")
for t, c in cnt_valid.most_common(80):
    p(f"   {t:<26} {c}")

with open(os.path.join(OUT, "_s2_诊断.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log))
keep.to_csv(os.path.join(OUT, "_清洗后样本.csv"), index=False, encoding="utf-8-sig")
with open(os.path.join(OUT, "_标签词频.json"), "w", encoding="utf-8") as f:
    json.dump(cnt_valid.most_common(), f, ensure_ascii=False, indent=1)
json.dump({"n_raw": n_raw, "n_link_dup": n_link_dup,
           "n_near_dup": len(drop_idx), "n_after_dedup": n_after_dedup,
           "n_valid": len(keep), "drop_log": DROP_LOG,
           "tag_total": len(tags_valid), "tag_unique_valid": len(cnt_valid),
           "tag_unique_all": len(cnt_all)},
          open(os.path.join(OUT, "_去重口径.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n>>> 已写出 _s2_诊断.txt / _清洗后样本.csv / _标签词频.json / _去重口径.json")
