# Supplementary S1 — Coding Manual

**Manuscript:** *Skill Requirements in AI Application Service Providers and Their Curriculum
Implications for Higher Vocational Education in Guangdong, China: A Sustainable Talent Supply
Perspective* (submitted to MDPI *Sustainability*)

**Scope of this file.** This is the full coding manual used in the study: the four-dimension
capability dictionary, the complete regular expressions, the priority rules, the
production-safety exclusion list, negation handling, boundary cases, the job-family decision
rules, and the low-prevalence reporting rule fixed in advance. Sections 1–5 are the version
that was issued to the second coder; Sections 6–8 are the methodological appendix that was
retained by the researchers and withheld from the second coder (it contains marginal totals
and the expected number of security hits, which would anchor the coder's judgements).

**Language note.** The unit of analysis is Chinese-language job postings, so all search terms,
skill tags and regular expressions are given in the original Chinese. English glosses are
provided in parentheses. The regular expressions are reproduced exactly as they were executed.

---

## 1. Coding task

Each coder independently completed two types of decision for the same 130 randomly drawn
posting records (24.8% of the analytic sample, sampled proportionally within job-family strata):

1. **Job-family assignment** (single choice, 1–6)
2. **Four capability dimensions** (four independent binary 0/1 variables)

Coders could use only three fields: job title, skill tags, and an excerpt of the job
description. **Coders were not to access, request or view any completed coding results, and
were not to discuss individual records with anyone else.** (If such a file was offered, the
instruction was to ignore it and inform the researcher.)

---

## 2. Job-family rules (single choice; first match in the listed order wins)

| Code | Job family | Decision basis (job title first; otherwise the first 300 characters of the description) |
|---|---|---|
| 1 | Delivery and implementation (FDE type) | FDE, 前沿部署 (frontier deployment), 前线部署 (frontline deployment), 交付工程师 (delivery engineer), 交付专家 (delivery specialist), 实施交付 (implementation delivery), 技术交付 (technical delivery), 应用交付 (application delivery), 部署工程师 (deployment engineer), 实施顾问 (implementation consultant), 实施工程师 (implementation engineer), 解决方案交付 (solution delivery) |
| 2 | Solutions and pre-sales | 解决方案 (solutions), 售前 (pre-sales), 技术顾问 (technical consultant), 咨询顾问 (consulting adviser), 业务顾问 (business consultant), 方案专家 (solution specialist) |
| 3 | Research, development and algorithms | 算法 (algorithm), 模型研发 (model R&D), 研发工程师 (R&D engineer), 训练 (training), 微调 (fine-tuning), Infra, 推理加速 (inference acceleration), 架构师 (architect), 开发工程师 (development engineer), 软件开发 (software development), 后端 (back end), 全栈 (full stack), 前端 (front end) |
| 4 | Product and operations | 产品经理 (product manager), 产品专家 (product specialist), 运营 (operations), 项目管理 (project management), 项目经理 (project manager) |
| 5 | AI applications and tools | AI应用 (AI application), 人工智能 (artificial intelligence), 大模型 (large model), 智能体 (agent), AIGC, Prompt, 提示词 (prompt), 知识库 (knowledge base), 数据标注 (data annotation), 训练师 (trainer) |
| 6 | Other | none of the above |

**Boundary cases and their treatment**

- A title containing both "交付" (delivery) and "算法" (algorithm), e.g. "AI交付算法工程师" →
  **code 1 (delivery and implementation)**, because the study's search terms are
  delivery-oriented.
- "AI应用工程师（FDE方向）" → **code 1**, because the title contains FDE.
- "资深架构师" with a description containing "全项目交付" → **code 1**.
- "ai agent 测试" → the title contains "测试", which appears in no list 1–5, but the
  description points to agents → **code 5**; if the description carries no AI-application
  signal → **code 6**.
- "27届校招 前沿安全算法研究方向" → contains "算法" → **code 3 (research, development and
  algorithms)**; it is **not** reassigned because of the word "安全" (security).

---

## 3. Four-dimension capability rules (**each dimension is decided independently**; a single
skill tag may hit more than one dimension)

The object of measurement is the **skill-tags field**. A dimension is coded 1 if and only if
the posting has at least one skill tag that hits that dimension's term list.

### 3.1 Production-safety exclusion (prerequisite rule)

Tags matching any of the following are **excluded from every capability dimension**, so that
industrial production safety cannot contaminate the AI/data-security dimension:

`房建` (building construction), `市政` (municipal engineering), `机电安全` (electromechanical
safety), `土建` (civil engineering), `注册安全工程师` (registered safety engineer),
`工程安全` (engineering safety), `生产安全` (production safety), `施工` (construction)

### 3.2 Dimension dictionaries (evaluated in priority order; used for the mutually exclusive
primary specification)

| Priority | Dimension | Regular expression (reproduced in full) |
|---|---|---|
| 1 | Knows security | `安全\|合规\|隐私\|伦理\|审计\|等保\|脱敏\|权限\|风控\|保密\|治理\|防泄漏\|水印` |
| 2 | Masters models | `\bAI\b\|人工智能\|大模型\|LLM\|GPT\|Agent\|智能体\|模型\|算法\|推理\|多模态\|提示词\|Prompt\|RAG\|检索增强\|向量\|机器学习\|深度学习\|NLP\|视觉\|语音\|知识图谱\|微调\|Function\|LangChain\|MCP\|AIGC\|生成式\|Qwen\|通义\|豆包\|DeepSeek\|Coze\|扣子\|Dify\|vLLM\|Copilot\|强化学习` (case-insensitive) |
| 3 | Can deliver | `交付\|部署\|实施\|上线\|运维\|监控\|解决方案\|培训\|文档\|驻场\|现场\|服务经验\|售前\|咨询\|接口\|集成\|Docker\|Kubernetes\|容器\|CI\|CD\|DevOps\|PMP\|项目管理\|架构设计\|性能优化\|微服务\|分布式\|全栈\|云平台\|SaaS\|低代码` |
| 4 | Understands business | `客户\|业务\|行业\|制造\|电商\|零售\|教育\|金融\|医疗\|健康\|交通\|物流\|政务\|能源\|电力\|汽车\|工业\|广告\|渠道\|销售\|面销\|陌拜\|需求分析\|商务\|CRM\|ERP\|OA\|报表\|BI\|数据分析\|市场营销\|管理相关专业\|企业服务\|B端\|C端\|咨询\|甲方` |

**Primary specification (mutually exclusive).** Each tag is assigned to the **first dimension
it hits** in the order above. Used for reporting tag shares (which sum to 100%).

**Sensitivity specification (multilabel).** A tag is counted in every dimension it hits. Used
for the robustness check reported in the manuscript.

### 3.3 Negation handling

Where a tag or description combines `无需 / 不需 / 不要求 / 不必` ("no need / not required")
with a security term, e.g. "无需安全经验", that security hit is **not counted**. Across the
whole sample the count of such negated expressions was **0** (verified and reported in the
analysis).

### 3.4 Expressions that are explicitly "using AI for security business" rather than "AI
governance of its own safety"

E.g. "AI 在防诈骗、防骚扰、智能风控等安全场景的应用" — **not counted** as *knows security*,
because this is implementation of a security-related business scenario, not AI governance
capability.

---

## 4. About the *knows security* column (read first to avoid misjudgement)

Earlier pilot coding showed that explicit requirements for AI/data security governance are
**very rare** among these postings; the *knows security* column will most likely contain only
a single-digit number of hits. Therefore:

- Coding almost everything as 0 is **expected**, not an omission. **Do not relax the criterion
  in order to make the column look better populated** — the low hit rate is itself one of the
  findings the study reports.
- When deciding *knows security*, hold strictly to the boundaries in Section 3: count only
  governance relating to the **AI model or the data itself**. Plant production safety, fire
  safety, civil engineering, electromechanical safety, information-security operations and
  data-permission administration as such are **not counted**; "using AI to do security
  business" (AI anti-fraud, intelligent risk control) is **not counted**.
- When in doubt, decide as you see fit and write one line of reasoning in the `coder_note`
  column. **These notes are valuable.**

---

## 5. What you are not asked to do

- You do not need to read the paper, to have a statistics background, or to consult the
  original job-posting pages.
- You do not need to compute any agreement statistic — that is done by the researcher after
  you return the form.
- You do not need to discuss with anyone whether a given record should be 0 or 1.
  **Disagreement is itself the object the study measures.**

---

---

*End of the version issued to the second coder. Sections 6–8 of the manual (required agreement metrics, the low-prevalence reporting rule, and the file list) were retained by the researchers and are reproduced in `S5_Sealed_Coder1_Record/S5_method_appendix.md`.*
