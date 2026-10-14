# -*- coding: utf-8 -*-
"""第4步：岗位家族分层 + 能力共现 + 课程比对预备。"""
import os
import re
import json
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
keep = pd.read_csv(os.path.join(OUT, "_清洗后样本.csv"), encoding="utf-8-sig",
                   dtype=str, keep_default_na=False)
N = len(keep)
R = []
def p(s=""):
    R.append(str(s)); print(s)

name = keep["岗位名称"].astype(str)
desc = keep["职位描述"].astype(str)
full = name + " " + desc

FAM = [
    ("① 交付实施族（FDE型）", r"FDE|前沿部署|前线部署|交付工程师|交付专家|实施交付|技术交付|"
                        r"应用交付|部署工程师|实施顾问|实施工程师|解决方案交付"),
    ("② 解决方案/售前族", r"解决方案|售前|技术顾问|咨询顾问|业务顾问|方案专家"),
    ("③ 研发算法族", r"算法|模型研发|研发工程师|训练|微调|Infra|推理加速|架构师|开发工程师|"
                  r"软件开发|后端|全栈|前端"),
    ("④ 产品运营族", r"产品经理|产品专家|运营|项目管理|项目经理"),
    ("⑤ AI应用/工具族", r"AI应用|人工智能|大模型|智能体|AIGC|Prompt|提示词|知识库|数据标注|训练师"),
]


def fam(n, d):
    for label, pat in FAM:
        if re.search(pat, n, re.I):
            return label
    for label, pat in FAM:
        if re.search(pat, d[:300], re.I):
            return label
    return "⑥ 其他"


keep["岗位族"] = [fam(n, d) for n, d in zip(name, desc)]
p("=" * 78)
p("【表8】岗位家族分层（以岗位名称为主判定，n=%d）" % N)
vc = keep["岗位族"].value_counts()
for k, v in vc.items():
    p(f"  {k:<22}{v:>4}  {v/N*100:5.1f}%")

p("\n【表8-附】岗位族 × 学历要求")
order = ["初中及以下", "高中", "中专/中技", "大专", "学历不限", "本科", "硕士", "博士"]
ct = pd.crosstab(keep["岗位族"], keep["学历要求"].astype(str).str.strip())
ct = ct.reindex(columns=[c for c in order if c in ct.columns], fill_value=0)
p(ct.to_string())

p("\n【表8-附2】岗位族 × 薪资中位数（K）")
keep["薪资K"] = pd.to_numeric(keep.get("薪资K"), errors="coerce")
g = keep.groupby("岗位族")["薪资K"].agg(["count", "median", "mean"]).round(1)
p(g.to_string())

# ---- 能力共现 ----
DIM_KEYS = {
    "懂业务": ["客户沟通", "制造业", "电商", "零售", "需求分析", "售前支持", "教育", "金融", "项目管理",
             "能源", "电力", "医疗", "物流", "政务", "商务谈判", "客户关系维护", "B端产品", "销售经验",
             "面销", "客户开发", "渠道", "企业服务", "汽车", "工业", "咨询", "CRM", "ERP", "OA", "BI", "报表",
             "数据分析", "软件", "互联网", "科技", "企业"],
    "通模型": ["AI", "人工智能", "大模型", "LLM", "Agent", "智能体", "推理", "Prompt工程", "RAG",
             "检索增强", "模型微调", "Function Calling", "多模态", "LangChain", "MCP", "向量数据库",
             "模型加速", "强化学习", "深度学习", "大模型算法", "生成式AI", "AIGC", "知识图谱", "GPT",
             "ChatGPT", "通义千问", "Qwen", "豆包", "DeepSeek", "Coze", "扣子", "Dify", "NLP", "机器学习",
             "计算机视觉", "Coze"],
    "知安全": ["数据安全", "安全合规", "合规", "隐私", "伦理", "等保", "权限管理", "脱敏", "审计",
             "网络安全", "数据治理"],
    "能交付": ["实施交付", "部署", "上线", "培训赋能", "解决方案", "文档撰写", "运维", "监控",
             "模型部署", "Docker", "容器", "Kubernetes", "接口", "现场驻场", "部署经验", "FDE",
             "智能体交付", "运维开发", "CI", "CD", "架构设计经验", "团队管理经验", "PMP", "微服务",
             "性能优化", "前沿部署", "云平台"],
    "技术工具": ["Python", "JavaScript", "Java", "C++", "SQL", "MySQL", "Linux", "数据库", "API",
              "TypeScript", "C", "Redis", "PostgreSQL", "Git", "Go", "Hadoop", "Vue", "React", "CSS",
              "HTML", "Spring", "Django", "Flask", "Node.js", "MongoDB", "Oracle", "Kafka", "ETL",
              "PyTorch", "SaaS", "小程序", "低代码"],
}

rows = []
for _, r in keep.iterrows():
    ts = [t.strip() for t in re.split(r"[,，;；/、]", str(r["技能标签"])) if t.strip()]
    rows.append({d: int(any(t in ks for t in ts)) for d, ks in DIM_KEYS.items()})
M = pd.DataFrame(rows)
p("\n【表9】单条岗位中五大能力维度同时出现的比例（n=%d）" % N)
for d in DIM_KEYS:
    p(f"  {d:<6} 出现于 {M[d].sum():>4} 条 = {M[d].mean()*100:5.1f}%")
p("\n【表9-附】维度共现组合 Top10")
combo = M.apply(lambda r: " + ".join([d for d in DIM_KEYS if r[d]]), axis=1)
for k, v in combo.value_counts().head(10).items():
    p(f"  {k or '(无标签)':<40} {v:>4}  {v/N*100:5.1f}%")

p("\n【表10】三条以上能力维度同时出现的岗位：%d 条 = %.1f%%"
  % ((M.sum(axis=1) >= 3).sum(), (M.sum(axis=1) >= 3).mean() * 100))

with open(os.path.join(OUT, "_s4_岗位族.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(R))
keep.to_csv(os.path.join(OUT, "_清洗后样本_带岗位族.csv"), index=False, encoding="utf-8-sig")
print("\n>>> 已写出 _s4_岗位族.txt / _清洗后样本_带岗位族.csv")
